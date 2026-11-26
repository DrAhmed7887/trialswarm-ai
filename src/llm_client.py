"""Shared Gemini 4 client supporting AI Studio API keys and Vertex AI."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Optional

DEFAULT_EXTRACTOR_MODEL = os.environ.get("TRIALSWARM_EXTRACTOR_MODEL", "gemini-4-hydrogen")
DEFAULT_PHENOTYPER_MODEL = os.environ.get("TRIALSWARM_PHENOTYPER_MODEL", "gemini-4-argon")


def get_vertex_project() -> Optional[str]:
    """Return configured GCP project ID for Vertex AI, or None if unset."""
    proj = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT") or ""
    proj = proj.strip()
    return proj or None


def is_gemini_configured() -> bool:
    """Return True if either an AI Studio key or a Vertex AI GCP project is configured."""
    has_key = bool((os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip())
    return has_key or bool(get_vertex_project())


def _build_vertex_credentials() -> Any:
    """Resolve ADC or gcloud CLI credentials for Vertex AI without embedding secrets."""
    try:
        import google.auth  # type: ignore

        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if creds is not None:
            return creds
    except Exception:
        pass

    env = dict(os.environ)
    for py_override in (None, "python3.12", "python3.11"):
        if py_override:
            env["CLOUDSDK_PYTHON"] = py_override
        try:
            token = subprocess.check_output(
                ["gcloud", "auth", "print-access-token"],
                env=env,
                stderr=subprocess.DEVNULL,
                timeout=8,
            ).decode("utf-8").strip()
            if token:
                import google.oauth2.credentials  # type: ignore

                return google.oauth2.credentials.Credentials(token=token)
        except Exception:
            continue
    return None


def _build_clients() -> list[tuple[str, Any]]:
    """Build ordered list of (backend_label, genai.Client) candidates."""
    from google import genai  # type: ignore

    api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    vertex_project = get_vertex_project()
    prefer_vertex = os.environ.get("TRIALSWARM_USE_VERTEX", "").strip().lower() in ("1", "true", "yes")

    clients: list[tuple[str, Any]] = []

    def _add_vertex() -> None:
        if not vertex_project:
            return
        creds = _build_vertex_credentials()
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global").strip() or "global"
        kwargs: dict[str, Any] = {"vertexai": True, "project": vertex_project, "location": location}
        if creds is not None:
            kwargs["credentials"] = creds
        try:
            clients.append(("vertex", genai.Client(**kwargs)))
        except Exception:
            pass

    def _add_api_key() -> None:
        if not api_key:
            return
        try:
            clients.append(("ai_studio", genai.Client(api_key=api_key)))
        except Exception:
            pass

    if prefer_vertex or (vertex_project and not api_key):
        _add_vertex()
        _add_api_key()
    else:
        _add_api_key()
        _add_vertex()

    return clients


def generate_gemini_json(
    prompt: str,
    primary_model: str,
    fallback_models: tuple[str, ...] = (),
    timeout_ms: int = 25000,
) -> tuple[Any, str, dict[str, int]]:
    """Call Gemini 4 and parse JSON response with model/backend failover.

    Returns (parsed_json, model_id, token_usage).
    Raises RuntimeError if no configured client/model succeeds.
    """
    from google.genai import types  # type: ignore

    clients = _build_clients()
    if not clients:
        raise RuntimeError("No Gemini API key or Vertex AI project configured.")

    models_to_try: list[str] = []
    for candidate in (primary_model, *fallback_models):
        if candidate and candidate not in models_to_try:
            models_to_try.append(candidate)

    last_exc: Optional[Exception] = None
    for _, client in clients:
        for model_id in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json",
                        http_options=types.HttpOptions(timeout=timeout_ms),
                    ),
                )
                usage_meta = getattr(response, "usage_metadata", None)
                usage: dict[str, int] = {}
                if usage_meta is not None:
                    usage = {
                        "input_tokens": int(getattr(usage_meta, "prompt_token_count", 0) or 0),
                        "output_tokens": int(getattr(usage_meta, "candidates_token_count", 0) or 0),
                        "thought_tokens": int(getattr(usage_meta, "thoughts_token_count", 0) or 0),
                    }
                raw_text = (getattr(response, "text", None) or "").strip()
                if not raw_text:
                    raise ValueError(f"Empty JSON response from {model_id}")
                parsed = json.loads(raw_text)
                return parsed, model_id, usage
            except Exception as exc:
                last_exc = exc
                continue

    raise RuntimeError(f"All Gemini 4 calls failed: {last_exc}")

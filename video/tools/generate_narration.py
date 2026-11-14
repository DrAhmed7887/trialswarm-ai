#!/usr/bin/env python3
"""TrialSwarm AI — ElevenLabs Narration Pipeline via macOS Keychain.

Zero plain-text secrets in files. Retrieves ELEVENLABS_API_KEY from Keychain,
calls /v1/text-to-speech/{voice_id}/with-timestamps, and saves scene MP3s
and alignment durations.
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

API_BASE = "https://api.elevenlabs.io"


def get_keychain_secret(service_name: str = "ELEVENLABS_API_KEY") -> str:
    """Retrieve secret securely from macOS Keychain."""
    res = subprocess.run(
        ["security", "find-generic-password", "-s", service_name, "-w"],
        capture_output=True,
        text=True,
        check=True,
    )
    secret = res.stdout.strip()
    if not secret:
        raise ValueError(f"Secret {service_name} was empty in Keychain.")
    return secret


def speak_line(
    text: str,
    voice_id: str,
    model_id: str,
    voice_settings: dict,
    api_key: str,
) -> tuple[bytes, float, list[dict]]:
    """Generate audio and character timestamps from ElevenLabs with-timestamps API."""
    url = f"{API_BASE}/v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128"
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": voice_settings,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.load(resp)

    audio_bytes = base64.b64decode(data["audio_base64"])
    alignment = data.get("alignment", {})
    end_times = alignment.get("character_end_times_seconds", [])
    duration_s = float(end_times[-1]) if end_times else 0.0

    return audio_bytes, duration_s, alignment


def run_pipeline(narration_path: Path, output_dir: Path, force: bool = False) -> int:
    if not narration_path.is_file():
        print(f"Error: {narration_path} not found.", file=sys.stderr)
        return 1

    cfg = json.loads(narration_path.read_text(encoding="utf-8"))
    voice_id = cfg.get("voice_id", "onwK4e9ZLuTAKqWW03F9")
    model_id = cfg.get("model_id", "eleven_multilingual_v2")
    voice_settings = cfg.get(
        "voice_settings",
        {"stability": 0.6, "similarity_boost": 0.75, "style": 0.0, "speed": 1.05},
    )
    lines = cfg.get("lines", {})

    output_dir.mkdir(parents=True, exist_ok=True)
    durations_file = output_dir / "durations.json"
    durations: dict[str, dict] = {}
    if durations_file.exists() and not force:
        try:
            durations = json.loads(durations_file.read_text(encoding="utf-8"))
        except Exception:
            durations = {}

    api_key = get_keychain_secret("ELEVENLABS_API_KEY")
    print(f"Loaded authenticated ElevenLabs key from Keychain. Voice: {voice_id} | Model: {model_id}")

    total_seconds = 0.0
    for scene_id, text in lines.items():
        mp3_path = output_dir / f"{scene_id}.mp3"
        cached = durations.get(scene_id)
        if not force and mp3_path.exists() and cached and cached.get("text") == text:
            dur = cached.get("seconds", 0.0)
            print(f"  [CACHED] {scene_id} ({dur:.2f}s): {text[:60]}...")
            total_seconds += dur
            continue

        print(f"  [GENERATING] {scene_id} ({len(text)} chars)...")
        audio, dur, alignment = speak_line(text, voice_id, model_id, voice_settings, api_key)
        mp3_path.write_bytes(audio)
        durations[scene_id] = {
            "text": text,
            "seconds": round(dur, 2),
            "character_count": len(text),
        }
        total_seconds += dur
        print(f"    -> Saved {mp3_path.name} ({dur:.2f}s)")

    durations_file.write_text(json.dumps(durations, indent=2), encoding="utf-8")
    print(f"\nDone! Total narration time: {total_seconds:.2f}s ({total_seconds / 60.0:.2f} min).")
    print(f"Output files in: {output_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ElevenLabs VO from narration.json")
    parser.add_argument("--config", type=Path, required=True, help="Path to narration.json")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for MP3s")
    parser.add_argument("--force", action="store_true", help="Force regenerate all audio")
    args = parser.parse_args()

    return run_pipeline(args.config, args.out, force=args.force)


if __name__ == "__main__":
    sys.exit(main())

"""FastAPI TestClient suite for TrialSwarm AI web endpoints (paired with @web-ui)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

try:
    from src.web.app import app
except ImportError:
    app = None  # type: ignore[assignment]

pytestmark = pytest.mark.skipif(
    app is None,
    reason="src.web.app not yet available (built in parallel by @web-ui)",
)


def _client() -> TestClient:
    assert app is not None
    return TestClient(app)


def test_get_root_html() -> None:
    """GET / returns 200 HTML containing TrialSwarm."""
    client = _client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "TrialSwarm" in resp.text


def test_get_judge_html() -> None:
    """GET /judge returns 200 HTML containing Judge."""
    client = _client()
    resp = client.get("/judge")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "Judge" in resp.text


def test_get_api_health() -> None:
    """GET /api/health returns 200 JSON with status == 'ok'."""
    client = _client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"


def test_get_api_cases() -> None:
    """GET /api/cases returns 200 JSON with protocols, patients, and benchmark."""
    client = _client()
    resp = client.get("/api/cases")
    assert resp.status_code == 200
    data = resp.json()
    assert "protocols" in data
    assert "patients" in data
    assert "benchmark_summary" in data or "benchmark" in data
    bench = data.get("benchmark_summary") or data.get("benchmark")
    assert isinstance(bench, dict)
    assert bench.get("total_cases") == 120


def test_post_api_screen_pt102() -> None:
    """POST /api/screen flags PT-102 on NCT04613596 as CONTRAINDICATED and catches hidden trap."""
    client = _client()
    resp = client.post(
        "/api/screen",
        json={"nct_id": "NCT04613596", "patient_id": "PT-102"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("overall_verdict") == "CONTRAINDICATED"
    assert data.get("caught_hidden_trap") is True
    assert "run_id" in data
    assert "signoff_packet" in data
    assert "packet_id" in data["signoff_packet"]


def test_post_api_verify_trap() -> None:
    """POST /api/verify-trap returns 200 JSON blocking fabricated quotes and catching steroid trap."""
    client = _client()
    resp = client.post(
        "/api/verify-trap",
        json={"nct_id": "NCT04613596", "patient_id": "PT-102"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("unverified_claims_blocked", 0) >= 1
    assert data.get("verifier_status") == "UNVERIFIED_CITATION_BLOCKED"
    assert data.get("trialswarm_steroid_verdict") == "CONTRAINDICATED"


def test_post_api_signoff_receipt() -> None:
    """POST /api/signoff produces a cryptographic SHA-256 receipt using run_id and packet_id."""
    client = _client()
    screen_resp = client.post(
        "/api/screen",
        json={"nct_id": "NCT04613596", "patient_id": "PT-102"},
    )
    assert screen_resp.status_code == 200
    screen_data = screen_resp.json()

    run_id = screen_data["run_id"]
    packet_id = screen_data["signoff_packet"]["packet_id"]

    signoff_resp = client.post(
        "/api/signoff",
        json={
            "run_id": run_id,
            "packet_id": packet_id,
            "decision": "APPROVE",
            "reviewer_name": "Dr. Ahmed Zayed",
            "reviewer_role": "Principal Investigator",
            "clinical_note": "Confirmed steroid equivalence hold on PT-102.",
        },
    )
    assert signoff_resp.status_code == 200
    receipt = signoff_resp.json()
    assert receipt.get("run_id") == run_id
    assert receipt.get("packet_id") == packet_id
    sha = receipt.get("sha256_hash", "")
    assert isinstance(sha, str) and len(sha) == 64

"""FastAPI server for TrialSwarm AI clinical trial screening & verification console."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.agents.verifier import run_adversarial_verification_probe
from src.schemas import (
    AdversarialTrapResult,
    AuditReport,
    SignOffAction,
    SignOffReceipt,
)
from src.swarm import (
    EVIDENCE_PMIDS,
    SwarmCoordinator,
    fetch_live_nct_protocol,
    load_patient_record,
    sign_packet,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(__file__).resolve().parent / "static"
DOCS_DIR = REPO_ROOT / "docs"
PROTOCOLS_DIR = REPO_ROOT / "data" / "protocols"
FEATURED_PATIENTS_PATH = REPO_ROOT / "data" / "patients" / "featured_patients.json"
BENCHMARK_RESULTS_PATH = REPO_ROOT / "eval" / "results" / "benchmark_120.json"

FEATURED_NCT_IDS = ["NCT04613596", "NCT04787042", "NCT06890598"]
MAX_CACHED_RUNS = 200

app = FastAPI(
    title="TrialSwarm AI",
    description="Multi-Agent Clinical Trial Eligibility & Safety Verification Engine",
    version="1.0.0",
)

coordinator = SwarmCoordinator()
RUNS_CACHE: OrderedDict[str, AuditReport] = OrderedDict()

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ScreenRequest(BaseModel):
    """Payload for POST /api/screen."""

    nct_id: str = Field(..., min_length=4, description="ClinicalTrials.gov NCT identifier")
    patient_id: Optional[str] = None
    custom_ehr_text: Optional[str] = None
    use_live_nct: bool = False
    use_llm: bool = False


class TrapVerifyRequest(BaseModel):
    """Optional payload for POST /api/verify-trap."""

    nct_id: str = "NCT04613596"
    patient_id: str = "PT-102"


def _store_run(report: AuditReport) -> None:
    """Store an audit report in the bounded in-memory LRU cache (max 200)."""
    if report.run_id in RUNS_CACHE:
        RUNS_CACHE.move_to_end(report.run_id)
    RUNS_CACHE[report.run_id] = report
    while len(RUNS_CACHE) > MAX_CACHED_RUNS:
        RUNS_CACHE.popitem(last=False)


def _load_protocol_summary(nct_id: str) -> dict[str, Any]:
    """Load summary metadata for a cached protocol JSON."""
    path = PROTOCOLS_DIR / f"{nct_id}.json"
    if not path.exists():
        return {"nct_id": nct_id, "brief_title": nct_id}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "nct_id": data.get("nct_id", nct_id),
        "brief_title": data.get("brief_title", nct_id),
        "official_title": data.get("official_title", data.get("brief_title", nct_id)),
        "sponsor": data.get("sponsor", "Unknown Sponsor"),
        "phases": data.get("phases", []),
        "overall_status": data.get("overall_status", "RECRUITING"),
        "conditions": data.get("conditions", []),
        "interventions": data.get("interventions", []),
        "line_count": len(data.get("protocol_lines", [])),
    }


def _load_featured_patients_summary() -> list[dict[str, Any]]:
    """Load featured patient summaries from data/patients/featured_patients.json."""
    if not FEATURED_PATIENTS_PATH.exists():
        return []
    with FEATURED_PATIENTS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    summaries: list[dict[str, Any]] = []
    for p in data.get("patients", []):
        summaries.append(
            {
                "patient_id": p.get("patient_id"),
                "name": p.get("name"),
                "age": p.get("age"),
                "sex": p.get("sex"),
                "diagnosis": p.get("diagnosis"),
                "stage": p.get("stage"),
                "target_nct": p.get("target_nct"),
                "target_phase": p.get("target_phase"),
                "expected_verdict": p.get("expected_verdict"),
                "clinical_trap_summary": p.get("clinical_trap_summary"),
                "ehr_text": p.get("ehr_text"),
            }
        )
    return summaries


@app.get("/")
async def serve_index() -> FileResponse:
    """Serve the primary TrialSwarm Clinical Screening Workstation."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_path)


@app.get("/judge")
async def serve_judge() -> FileResponse:
    """Serve the Judge & VC Verification Console."""
    judge_path = STATIC_DIR / "judge.html"
    if not judge_path.exists():
        raise HTTPException(status_code=404, detail="judge.html not found")
    return FileResponse(judge_path)


@app.get("/docs/workflow.svg")
async def serve_workflow_svg() -> Response:
    """Serve docs/workflow.svg if present."""
    svg_path = DOCS_DIR / "workflow.svg"
    if svg_path.exists() and svg_path.is_file():
        return FileResponse(svg_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="workflow.svg not present")


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Return service health and Gemini API configuration status."""
    gemini_configured = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    return {
        "status": "ok",
        "service": "TrialSwarm AI",
        "gemini_configured": gemini_configured,
    }


@app.get("/api/cases")
async def get_cases() -> dict[str, Any]:
    """Return featured protocols, featured patients, and benchmark_120 summary if available."""
    protocols = [_load_protocol_summary(nct) for nct in FEATURED_NCT_IDS]
    patients = _load_featured_patients_summary()

    benchmark_summary: dict[str, Any] = {}
    if BENCHMARK_RESULTS_PATH.exists():
        try:
            with BENCHMARK_RESULTS_PATH.open("r", encoding="utf-8") as f:
                benchmark_summary = json.load(f)
        except Exception:
            benchmark_summary = {}

    return {
        "protocols": protocols,
        "patients": patients,
        "benchmark_summary": benchmark_summary,
        "pmids": EVIDENCE_PMIDS,
    }


@app.post("/api/screen", response_model=AuditReport)
async def screen_patient(req: ScreenRequest) -> AuditReport:
    """Run the multi-agent /swarm audit for a protocol and patient record."""
    clean_nct = req.nct_id.strip().upper()
    if not clean_nct.startswith("NCT"):
        raise HTTPException(status_code=400, detail="Protocol ID must start with NCT (e.g., NCT04613596)")

    # Validate live fetch if explicitly requested or non-cached
    if req.use_live_nct:
        try:
            url = f"https://clinicaltrials.gov/api/v2/studies/{clean_nct}"
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
        except httpx.HTTPError:
            # Fall back to cached protocol if available
            if not (PROTOCOLS_DIR / f"{clean_nct}.json").exists():
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch live protocol {clean_nct} from ClinicalTrials.gov APIv2.",
                )

    if req.custom_ehr_text and req.custom_ehr_text.strip():
        patient_ref: Any = {
            "patient_id": req.patient_id or "CUSTOM-EHR",
            "name": "Custom EHR Submission",
            "ehr_text": req.custom_ehr_text.strip(),
        }
    elif req.patient_id and req.patient_id.strip():
        patient_ref = req.patient_id.strip()
    else:
        patient_ref = "PT-102"

    try:
        report = await coordinator.run_swarm_async(
            nct_id=clean_nct,
            patient_ref=patient_ref,
            use_llm=req.use_llm,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=404 if exc.response.status_code == 404 else 502,
            detail=f"ClinicalTrials.gov lookup failed for {clean_nct}: HTTP {exc.response.status_code}",
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Network error contacting ClinicalTrials.gov for {clean_nct}: {exc}",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Swarm audit execution error: {exc}")

    _store_run(report)
    return report


@app.post("/api/verify-trap", response_model=AdversarialTrapResult)
async def verify_trap(req: Optional[TrapVerifyRequest] = None) -> AdversarialTrapResult:
    """Run adversarial hallucinated citation rejection + steroid equivalence override probe."""
    payload = req or TrapVerifyRequest()
    try:
        protocol = fetch_live_nct_protocol(payload.nct_id)
        patient = load_patient_record(payload.patient_id)
        return run_adversarial_verification_probe(protocol=protocol, patient=patient)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Verification probe error: {exc}")


@app.post("/api/signoff", response_model=SignOffReceipt)
async def submit_signoff(action: SignOffAction) -> SignOffReceipt:
    """Sign off a staged clinical eCRF or washout hold packet with SHA-256 tamper-evident receipt."""
    if not action.reviewer_name.strip():
        raise HTTPException(status_code=400, detail="Reviewer name is required for 21 CFR Part 11 sign-off.")
    if not action.run_id.strip():
        raise HTTPException(status_code=400, detail="run_id is required.")

    receipt = sign_packet(action)

    cached_report = RUNS_CACHE.get(action.run_id)
    if cached_report is not None and cached_report.signoff_packet.packet_id == action.packet_id:
        cached_report.signoff_packet.status = (
            "SIGNED_APPROVED" if action.decision == "APPROVE" else "SIGNED_OVERRIDE"
        )

    return receipt

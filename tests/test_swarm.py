"""Pytest verification suite for TrialSwarm AI clinical safety and swarm grounding."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from src.agents.safety_auditor import compute_prednisone_equivalent_mg
from src.agents.verifier import (
    run_adversarial_verification_probe,
    verify_citations_and_verdicts,
)
from src.schemas import CriterionVerdict, LineCitation, PatientPhenotype
from src.swarm.coordinator import (
    SwarmCoordinator,
    fetch_live_nct_protocol,
    load_patient_record,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
COHORT_120_PATH = REPO_ROOT / "data" / "cohort_120.json"


def test_pt101_eligible_nct04613596() -> None:
    """PT-101 (Elena Rostova) is a clean ELIGIBLE pass on NCT04613596."""
    coord = SwarmCoordinator()
    report = coord.run_swarm("NCT04613596", "PT-101", use_llm=False)

    assert report.overall_verdict == "ELIGIBLE"
    assert report.citation_verification_rate == 100.0
    assert report.unverified_claims_blocked == 0
    assert report.signoff_packet.action_type == "STAGE_ECRF_PRE_SCREEN"
    assert report.signoff_packet.status == "PENDING_HUMAN_SIGNOFF"


def test_pt102_contraindicated_both_trials() -> None:
    """PT-102 (Marcus Vance) triggers R1 steroid trap and R2 washout on NCT04613596 & NCT04787042."""
    coord = SwarmCoordinator()

    # 1) NCT04613596 (KRYSTAL-7)
    rep_461 = coord.run_swarm("NCT04613596", "PT-102", use_llm=False)
    assert rep_461.overall_verdict == "CONTRAINDICATED"
    assert rep_461.caught_hidden_trap is True

    r1_461 = next(f for f in rep_461.safety_findings if f.rule_code == "R1")
    assert r1_461.severity == "BLOCKER"
    assert r1_461.prednisone_eq_mg == pytest.approx(26.67, abs=0.2)

    r2_461 = next(f for f in rep_461.safety_findings if f.rule_code == "R2")
    assert r2_461.severity == "BLOCKER"
    assert r2_461.washout_days_elapsed == 19

    # 2) NCT04787042 (ST-067)
    rep_478 = coord.run_swarm("NCT04787042", "PT-102", use_llm=False)
    assert rep_478.overall_verdict == "CONTRAINDICATED"
    assert rep_478.caught_hidden_trap is True

    r1_478 = next(f for f in rep_478.safety_findings if f.rule_code == "R1")
    assert r1_478.severity == "BLOCKER"
    assert r1_478.prednisone_eq_mg == pytest.approx(26.67, abs=0.2)

    r2_478 = next(f for f in rep_478.safety_findings if f.rule_code == "R2")
    assert r2_478.severity == "BLOCKER"
    assert r2_478.washout_days_elapsed == 19
    assert r2_478.earliest_rescreen_date == "2026-11-23"
    assert rep_478.signoff_packet.earliest_rescreen_date == "2026-11-23"


def test_pt103_contraindicated_nct04787042() -> None:
    """PT-103 (Sofia Morales) triggers both R3 (45 Gy RT at 110d) and R4 (AST 142 / ALT 156)."""
    coord = SwarmCoordinator()
    report = coord.run_swarm("NCT04787042", "PT-103", use_llm=False)

    assert report.overall_verdict == "CONTRAINDICATED"
    assert report.caught_hidden_trap is True

    r3 = next(f for f in report.safety_findings if f.rule_code == "R3")
    assert r3.severity == "BLOCKER"
    assert "45" in r3.calculation_detail
    assert "110" in r3.calculation_detail

    r4 = next(f for f in report.safety_findings if f.rule_code == "R4")
    assert r4.severity == "BLOCKER"
    assert "142" in r4.calculation_detail
    assert "156" in r4.calculation_detail


def test_pt104_needs_human_review_nct06890598() -> None:
    """PT-104 (David Chen) triggers R5 NEEDS_HUMAN_REVIEW due to pending reflex EGFR/ALK and PD-L1."""
    coord = SwarmCoordinator()
    report = coord.run_swarm("NCT06890598", "PT-104", use_llm=False)

    assert report.overall_verdict == "NEEDS_HUMAN_REVIEW"
    assert report.caught_hidden_trap is True

    r5 = next(f for f in report.safety_findings if f.rule_code == "R5")
    assert r5.severity == "NEEDS_REVIEW"
    assert "PENDING_LAB_RESULT" in r5.calculation_detail
    assert report.signoff_packet.action_type == "REQUEST_REFLEX_BIOMARKERS"


def test_glucocorticoid_equivalence_conversions() -> None:
    """Verify Rule R1 glucocorticoid conversion factors against Prednisone equivalents."""
    # Dexamethasone: 5.0 / 0.75 = 6.6667x -> 4 mg = 26.67 mg
    assert compute_prednisone_equivalent_mg("Dexamethasone", 4.0) == pytest.approx(26.67, abs=0.05)
    # Methylprednisolone: 5.0 / 4.0 = 1.25x -> 16 mg = 20.0 mg
    assert compute_prednisone_equivalent_mg("Methylprednisolone", 16.0) == pytest.approx(20.0, abs=0.01)
    # Hydrocortisone: 5.0 / 20.0 = 0.25x -> 40 mg = 10.0 mg
    assert compute_prednisone_equivalent_mg("Hydrocortisone", 40.0) == pytest.approx(10.0, abs=0.01)
    # Prednisone: 1.0x -> 10 mg = 10.0 mg
    assert compute_prednisone_equivalent_mg("Prednisone", 10.0) == pytest.approx(10.0, abs=0.01)
    assert compute_prednisone_equivalent_mg("Prednisolone", 10.0) == pytest.approx(10.0, abs=0.01)
    assert compute_prednisone_equivalent_mg("Dexamethasone", 0.0) == 0.0
    assert compute_prednisone_equivalent_mg("Dexamethasone", None) == 0.0


def test_deterministic_citation_verifier_blocks_fabricated_quotes() -> None:
    """Rule R6 verifier rejects fabricated quotes with UNVERIFIED_CITATION_BLOCKED."""
    protocol_lines = [{"line": 1, "text": "Inclusion Criteria: Age >= 18 years with NSCLC."}]
    ehr_lines = [{"line": 1, "text": "PATIENT IDENTIFIER: PT-102 | Ongoing Dexamethasone 2 mg BID."}]

    fake_quote = "Patient has zero steroid intake and normal AST/ALT."
    verdict = CriterionVerdict(
        rule_id="FAKE-RULE-1",
        criterion="Systemic corticosteroid check",
        category="EXCLUSION",
        status="MET",
        reasoning="Claimed no steroids.",
        citations=[
            LineCitation(
                doc_type="EHR",
                doc_id="PT-102",
                line_start=1,
                line_end=1,
                verbatim_quote=fake_quote,
                verified=False,
            )
        ],
        verified_by_rule_engine=True,
    )

    rate, blocked = verify_citations_and_verdicts(
        protocol_lines=protocol_lines,
        ehr_lines=ehr_lines,
        rules=[],
        phenotype=PatientPhenotype(),
        safety_findings=[],
        criterion_verdicts=[verdict],
    )

    assert verdict.status == "UNVERIFIED_CITATION_BLOCKED"
    assert verdict.verified_by_rule_engine is False
    assert blocked == 1
    assert rate == 0.0


def test_adversarial_verification_probe() -> None:
    """Adversarial probe catches injected hallucination and confirms naive baseline failure."""
    protocol = fetch_live_nct_protocol("NCT04613596")
    patient = load_patient_record("PT-102")

    res = run_adversarial_verification_probe(protocol, patient)
    assert res.case_id == "PT-102"
    assert res.nct_id == "NCT04613596"
    assert res.verifier_status == "UNVERIFIED_CITATION_BLOCKED"
    assert res.unverified_claims_blocked >= 1
    assert res.prednisone_eq_mg == pytest.approx(26.67, abs=0.2)
    assert res.trialswarm_steroid_verdict == "CONTRAINDICATED"
    assert "MET" in res.naive_steroid_verdict


def test_cohort_120_loads_with_120_cases() -> None:
    """Verify data/cohort_120.json contains exactly 120 cases balanced across 3 trials."""
    assert COHORT_120_PATH.exists()
    with COHORT_120_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    patients = data.get("patients", [])
    assert data.get("total_count") == 120
    assert len(patients) == 120

    trial_counts = Counter(p["target_nct"] for p in patients)
    assert trial_counts["NCT04613596"] == 40
    assert trial_counts["NCT04787042"] == 40
    assert trial_counts["NCT06890598"] == 40


def test_r5_unrecorded_pdl1_returns_needs_human_review() -> None:
    """R5 must route unrecorded (None) PD-L1 TPS to NEEDS_HUMAN_REVIEW, never ELIGIBLE."""
    from src.agents.safety_auditor import audit_patient_safety

    phenotype = PatientPhenotype(
        patient_id="PT-TEST-R5",
        age=62,
        ecog=0,
        histology_group="NSCLC",
        biomarkers={"kras_g12c": "POSITIVE", "pd_l1_tps": None, "egfr_mut": "NEGATIVE", "alk_fusion": "NEGATIVE"},
        labs={"egfr": 75.0, "ast": 24.0, "alt": 22.0, "total_bilirubin": 0.7, "anc": 3200.0, "platelets": 210000.0},
    )
    findings, _, overall_verdict, _, _, _, _ = audit_patient_safety(
        nct_id="NCT06890598",
        rules=[],
        phenotype=phenotype,
        reference_date="2026-11-14",
    )
    assert overall_verdict == "NEEDS_HUMAN_REVIEW"
    r5 = [f for f in findings if f.rule_code == "R5"]
    assert r5 and r5[0].severity == "NEEDS_REVIEW"

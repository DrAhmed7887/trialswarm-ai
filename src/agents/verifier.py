"""@verifier agent: deterministic Rule R6 verbatim citation verification & adversarial trap probe."""

from __future__ import annotations

import re
from typing import Any, Optional, Union

from src.agents.extractor import extract_protocol_rules
from src.agents.phenotyper import extract_patient_phenotype
from src.agents.safety_auditor import DEFAULT_REFERENCE_DATE, audit_patient_safety
from src.schemas import (
    AdversarialTrapResult,
    CriterionRule,
    CriterionVerdict,
    LineCitation,
    PatientPhenotype,
    SafetyFinding,
)


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def verify_single_citation(
    citation: LineCitation,
    protocol_map: dict[int, str],
    ehr_map: dict[int, str],
) -> bool:
    """Verify a LineCitation against line-indexed protocol or EHR text using normalized whitespace."""
    source_map = protocol_map if citation.doc_type == "PROTOCOL" else ehr_map
    if citation.line_start < 1 or citation.line_end < citation.line_start:
        citation.verified = False
        return False

    span_parts: list[str] = []
    for lnum in range(citation.line_start, citation.line_end + 1):
        if lnum not in source_map:
            citation.verified = False
            return False
        span_parts.append(source_map[lnum])

    norm_span = _normalize_ws(" ".join(span_parts))
    norm_quote = _normalize_ws(citation.verbatim_quote)
    is_valid = bool(norm_quote and norm_quote in norm_span)
    citation.verified = is_valid
    return is_valid


def verify_citations_and_verdicts(
    protocol_lines: list[dict[str, Any]],
    ehr_lines: list[dict[str, Any]],
    rules: list[CriterionRule],
    phenotype: PatientPhenotype,
    safety_findings: list[SafetyFinding],
    criterion_verdicts: list[CriterionVerdict],
) -> tuple[float, int]:
    """Enforce Rule R6: verify every citation and block any ungrounded verdict claims.

    Returns (citation_verification_rate_pct, unverified_claims_blocked).
    """
    protocol_map = {int(item["line"]): str(item["text"]) for item in protocol_lines}
    ehr_map = {int(item["line"]): str(item["text"]) for item in ehr_lines}

    total_checked = 0
    total_verified = 0
    blocked_count = 0

    def check_cit(cit: LineCitation) -> bool:
        nonlocal total_checked, total_verified
        ok = verify_single_citation(cit, protocol_map, ehr_map)
        total_checked += 1
        if ok:
            total_verified += 1
        return ok

    for r in rules:
        check_cit(r.citation)

    for c in phenotype.extraction_citations:
        check_cit(c)

    for m in phenotype.medications:
        if m.citation:
            check_cit(m.citation)

    for rt in phenotype.radiation_history:
        if rt.citation:
            check_cit(rt.citation)

    for sf in safety_findings:
        for c in sf.citations:
            check_cit(c)

    for cv in criterion_verdicts:
        if not cv.citations:
            cv.status = "UNVERIFIED_CITATION_BLOCKED"
            cv.verified_by_rule_engine = False
            cv.reasoning = f"[BLOCKED BY RULE R6: Missing citation] {cv.reasoning}"
            blocked_count += 1
            continue

        all_ok = True
        for c in cv.citations:
            if not check_cit(c):
                all_ok = False
        if not all_ok:
            cv.status = "UNVERIFIED_CITATION_BLOCKED"
            cv.verified_by_rule_engine = False
            cv.reasoning = f"[BLOCKED BY RULE R6: Unverified line citation] {cv.reasoning}"
            blocked_count += 1

    rate = round((total_verified / total_checked) * 100.0, 2) if total_checked > 0 else 100.0
    return rate, blocked_count


def run_adversarial_verification_probe(
    protocol: dict[str, Any],
    patient: Union[dict[str, Any], str],
    reference_date: str = DEFAULT_REFERENCE_DATE,
) -> AdversarialTrapResult:
    """Execute real swarm audit PLUS adversarial hallucinated-citation probe (Rule R6 + Rule R1)."""
    nct_id = str(protocol.get("nct_id") or "NCT04613596")
    target_phase = patient.get("target_phase") if isinstance(patient, dict) else "PHASE3"

    rules, protocol_lines, _ = extract_protocol_rules(protocol, target_phase=target_phase)
    phenotype, ehr_lines, _ = extract_patient_phenotype(patient)
    pid = str(patient.get("patient_id") if isinstance(patient, dict) else "CUSTOM-EHR")

    (
        safety_findings,
        criterion_verdicts,
        overall_verdict,
        _naive_overall,
        _caught_trap,
        _trap_exp,
        earliest_rescreen,
    ) = audit_patient_safety(nct_id, rules, phenotype, reference_date=reference_date)

    # Extract real steroid finding and naive steroid status
    pred_eq = 0.0
    for sf in safety_findings:
        if sf.rule_code == "R1" and sf.prednisone_eq_mg is not None:
            pred_eq = sf.prednisone_eq_mg

    naive_steroid_verdict = "MET (raw dose <= 10.0 mg/day)"
    for cv in criterion_verdicts:
        if "steroid" in cv.criterion.lower() or "corticosteroid" in cv.criterion.lower():
            if cv.naive_baseline_status:
                naive_steroid_verdict = f"{cv.naive_baseline_status} (raw daily dose compared against <=10 mg ceiling)"
            break

    # Inject adversarial hallucination into a synthetic verdict claim attributed to EHR line 1
    injected_quote = "Patient is taking 0 mg corticosteroids"
    adversarial_verdict = CriterionVerdict(
        rule_id=f"{nct_id}-ADV-PROBE",
        criterion="Adversarial Hallucinated Steroid Claim Probe",
        category="EXCLUSION",
        status="MET",
        reasoning="Injected adversarial LLM claim asserting 0 mg corticosteroids.",
        citations=[
            LineCitation(
                doc_type="EHR",
                doc_id=pid,
                line_start=1,
                line_end=1,
                verbatim_quote=injected_quote,
                verified=False,
            )
        ],
        verified_by_rule_engine=False,
    )
    probe_verdicts = list(criterion_verdicts) + [adversarial_verdict]

    _, blocked_count = verify_citations_and_verdicts(
        protocol_lines=protocol_lines,
        ehr_lines=ehr_lines,
        rules=rules,
        phenotype=phenotype,
        safety_findings=safety_findings,
        criterion_verdicts=probe_verdicts,
    )

    return AdversarialTrapResult(
        case_id=pid,
        nct_id=nct_id,
        injected_hallucination_quote=injected_quote,
        verifier_status=adversarial_verdict.status,
        unverified_claims_blocked=blocked_count,
        naive_steroid_verdict=naive_steroid_verdict,
        trialswarm_steroid_verdict=overall_verdict,
        prednisone_eq_mg=pred_eq,
        earliest_rescreen_date=earliest_rescreen,
        details=(
            f"Rule R6 rejected adversarial quote '{injected_quote}' attributed to EHR Line 1 "
            f"(status={adversarial_verdict.status}, blocked={blocked_count}). "
            f"Rule R1 computed Prednisone equivalent = {pred_eq:.2f} mg/day -> {overall_verdict}, "
            f"whereas naive numeric baseline yielded {naive_steroid_verdict}."
        ),
    )

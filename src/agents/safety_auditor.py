"""@safety-auditor agent: deterministic clinical rules R1-R5 and naive single-prompt baseline."""

from __future__ import annotations

from datetime import date, timedelta
import re
from typing import Any, Optional

from src.schemas import (
    CriterionRule,
    CriterionVerdict,
    LineCitation,
    MedicationEntry,
    PatientPhenotype,
    SafetyFinding,
)

STEROID_CONVERSION_FACTORS: dict[str, float] = {
    "Dexamethasone": 5.0 / 0.75,      # ~6.6667x
    "Methylprednisolone": 5.0 / 4.0,  # 1.25x
    "Hydrocortisone": 5.0 / 20.0,     # 0.25x
    "Prednisone": 1.0,
    "Prednisolone": 1.0,
}

DEFAULT_REFERENCE_DATE = "2026-11-14"


def _parse_date_safe(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str.strip())
    except ValueError:
        return None


def compute_prednisone_equivalent_mg(drug_name: str, daily_dose_mg: Optional[float]) -> float:
    """Convert daily corticosteroid dose to Prednisone-equivalent mg/day (Rule R1)."""
    if daily_dose_mg is None or daily_dose_mg <= 0:
        return 0.0
    for key, factor in STEROID_CONVERSION_FACTORS.items():
        if key.lower() == drug_name.strip().lower():
            return round(daily_dose_mg * factor, 2)
    return round(daily_dose_mg, 2)


_CASE_SENSITIVE_KWS = {"eGFR", "EGFR", "AST", "ALT", "ANC", "RT", "ER:", "PR:"}


def _find_citations_for_biomarker(phenotype: PatientPhenotype, *keywords: str) -> list[LineCitation]:
    matched: list[LineCitation] = []
    for cit in phenotype.extraction_citations:
        quote = cit.verbatim_quote
        for kw in keywords:
            flags = 0 if kw in _CASE_SENSITIVE_KWS else re.IGNORECASE
            pattern = re.escape(kw)
            if kw.rstrip(":").isalnum():
                pattern = rf"\b{pattern}"
                if kw[-1].isalnum():
                    pattern = rf"{pattern}\b"
            if re.search(pattern, quote, flags):
                matched.append(cit)
                break
    return matched


def evaluate_naive_single_prompt_baseline(
    nct_id: str,
    rules: list[CriterionRule],
    phenotype: PatientPhenotype,
    reference_date: str = DEFAULT_REFERENCE_DATE,
) -> tuple[str, dict[str, str], str]:
    """Simulate a literal single-prompt LLM without pharmacology/date/CTCAE deterministic tools.

    Failure modes simulated:
    1. Raw corticosteroid mg comparison (daily_dose_mg <= 10.0) without Prednisone equivalence.
    2. Calendar-month heuristic instead of exact 14d/28d/30d/180d day arithmetic.
    3. Misses CTCAE v5.0 Grade >= 2 ULN numeric thresholds unless extreme.
    4. Assumes pending biomarkers will pass or checks only primary driver.
    """
    per_rule: dict[str, str] = {}
    naive_failures: list[str] = []

    for rule in rules:
        rt = rule.rule_type
        status = "MET"

        if rt == "steroid_ceiling_mg":
            ceiling = float(rule.threshold_value or 10.0)
            max_raw = 0.0
            for m in phenotype.medications:
                if m.drug_class == "systemic_corticosteroid" and m.ongoing and m.daily_dose_mg:
                    max_raw = max(max_raw, m.daily_dose_mg)
            if max_raw > ceiling:
                status = "EXCLUDED"
                naive_failures.append(f"Raw steroid dose {max_raw} mg > {ceiling} mg")
            else:
                # Trap: Dexamethasone 4.0 mg/day <= 10.0 mg raw ceiling -> falsely MET!
                status = "MET"

        elif rt in ("systemic_washout_days", "live_vaccine_washout_days", "major_surgery_washout_days", "thoracic_rt_window", "any_rt_washout_days", "cns_steroid_washout_days"):
            # Naive LLM fails relative day arithmetic across months -> falsely assumes cleared
            status = "MET"

        elif rt == "prior_metastatic_lines":
            # Naive LLM misses investigational modulator or counts only standard chemotherapy
            has_standard_chemo = any(
                "chemo" in str(p.get("regimen", "")).lower() or "pemetrexed" in str(p.get("regimen", "")).lower()
                for p in phenotype.prior_lines_detail
            )
            if has_standard_chemo:
                status = "EXCLUDED"
                naive_failures.append("Prior standard metastatic chemotherapy")
            else:
                status = "MET"

        elif rt == "ctcae_grade2_labs":
            # Naive LLM lacks CTCAE ULN multipliers (checks only ECOG >= 2 or severe cytopenia)
            if phenotype.ecog is not None and phenotype.ecog > 1:
                status = "EXCLUDED"
                naive_failures.append(f"ECOG {phenotype.ecog} > 1")
            else:
                status = "MET"

        elif rt == "kras_g12c":
            if phenotype.biomarkers.get("kras_g12c") == "NEGATIVE":
                status = "NOT_MET"
                naive_failures.append("KRAS G12C negative")
            else:
                status = "MET"

        elif rt == "pd_l1_tps":
            tps = phenotype.biomarkers.get("pd_l1_tps")
            if isinstance(tps, (int, float)) and tps < float(rule.threshold_value or 50):
                status = "NOT_MET"
                naive_failures.append(f"PD-L1 TPS {tps}% < {rule.threshold_value}%")
            else:
                status = "MET"

        elif rt == "driver_exclusion":
            if phenotype.histology_group == "NSCLC" and (
                phenotype.biomarkers.get("egfr_mut") == "POSITIVE"
                or phenotype.biomarkers.get("alk_fusion") == "POSITIVE"
            ):
                status = "EXCLUDED"
                naive_failures.append("Actionable EGFR/ALK mutation")
            else:
                status = "MET"

        elif rt == "ecog":
            if phenotype.ecog is not None and phenotype.ecog > 1:
                status = "NOT_MET"
                naive_failures.append(f"ECOG {phenotype.ecog} > 1")

        elif rt == "autoimmune_active" and phenotype.autoimmune_active:
            status = "EXCLUDED"
            naive_failures.append("Active autoimmune disease")

        elif rt == "prior_grade3_irae" and phenotype.prior_grade3_irae:
            status = "EXCLUDED"
            naive_failures.append("Prior Grade >= 3 irAE")

        per_rule[rule.rule_id] = status

    if naive_failures:
        naive_verdict = "CONTRAINDICATED"
        explanation = "Naive single-prompt baseline flagged: " + "; ".join(naive_failures)
    else:
        naive_verdict = "ELIGIBLE"
        explanation = (
            "Naive single-prompt baseline returned ELIGIBLE (lacks glucocorticoid Prednisone-equivalence "
            "conversion, relative calendar-day washout arithmetic, CTCAE v5.0 ULN thresholds, and pending-assay gating)."
        )
    return naive_verdict, per_rule, explanation


def audit_patient_safety(
    nct_id: str,
    rules: list[CriterionRule],
    phenotype: PatientPhenotype,
    reference_date: str = DEFAULT_REFERENCE_DATE,
) -> tuple[
    list[SafetyFinding],
    list[CriterionVerdict],
    str,
    str,
    bool,
    Optional[str],
    Optional[str],
]:
    """Run Rules R1-R5 against extracted protocol rules and EHR phenotype.

    Returns:
        (safety_findings, criterion_verdicts, overall_verdict, naive_verdict,
         caught_hidden_trap, trap_explanation, earliest_rescreen_date)
    """
    ref_dt = _parse_date_safe(reference_date) or date(2026, 11, 14)
    findings: list[SafetyFinding] = []
    verdicts: list[CriterionVerdict] = []
    rescreen_dates: list[date] = []
    blockers: list[str] = []
    pending_reviews: list[str] = []

    naive_verdict, naive_per_rule, _ = evaluate_naive_single_prompt_baseline(
        nct_id, rules, phenotype, reference_date
    )

    # =========================================================================
    # RULE R1: Glucocorticoid Potency Equivalence
    # =========================================================================
    max_ongoing_pred_eq = 0.0
    r1_blockers: list[str] = []
    r1_citations: list[LineCitation] = []
    r1_rescreen: Optional[str] = None

    steroid_meds = [m for m in phenotype.medications if m.drug_class == "systemic_corticosteroid"]
    for med in steroid_meds:
        if med.citation:
            r1_citations.append(med.citation)
        if med.ongoing:
            pred_eq = compute_prednisone_equivalent_mg(med.name, med.daily_dose_mg)
            max_ongoing_pred_eq = max(max_ongoing_pred_eq, pred_eq)
            if pred_eq > 10.0:
                factor = STEROID_CONVERSION_FACTORS.get(med.name, 1.0)
                r1_blockers.append(
                    f"Ongoing {med.name} {med.daily_dose_mg:g} mg/day x {factor:.4g} = "
                    f"{pred_eq:.2f} mg/day Prednisone eq (> 10.0 mg/day ceiling)"
                )
        elif nct_id == "NCT04787042" and med.last_dose_date and phenotype.cns_status.get("has_lesions"):
            last_dt = _parse_date_safe(med.last_dose_date)
            if last_dt is not None:
                days_off = (ref_dt - last_dt).days
                if days_off < 14:
                    rs_dt = last_dt + timedelta(days=14)
                    rescreen_dates.append(rs_dt)
                    r1_rescreen = rs_dt.isoformat()
                    r1_blockers.append(
                        f"Treated brain met steroid ({med.name}) stopped {days_off}d ago (< 14d required; clearance {r1_rescreen})"
                    )

    if r1_blockers:
        blockers.extend(r1_blockers)
        findings.append(
            SafetyFinding(
                rule_code="R1",
                severity="BLOCKER",
                title="R1 Glucocorticoid Potency Equivalence Ceiling Exceeded",
                calculation_detail="; ".join(r1_blockers),
                prednisone_eq_mg=max_ongoing_pred_eq if max_ongoing_pred_eq > 0 else None,
                earliest_rescreen_date=r1_rescreen,
                citations=r1_citations,
            )
        )
    else:
        detail = (
            "No ongoing systemic corticosteroids > 10.0 mg/day Prednisone equivalent "
            f"(active Prednisone eq = {max_ongoing_pred_eq:.1f} mg/day)."
        )
        findings.append(
            SafetyFinding(
                rule_code="R1",
                severity="PASS",
                title="R1 Glucocorticoid Potency Equivalence Cleared",
                calculation_detail=detail,
                prednisone_eq_mg=max_ongoing_pred_eq,
                citations=r1_citations,
            )
        )

    # =========================================================================
    # RULE R2: Systemic Anticancer, Investigational, Vaccine & Surgical Washout
    # =========================================================================
    r2_blockers: list[str] = []
    r2_citations: list[LineCitation] = []
    r2_elapsed: Optional[int] = None
    r2_required: Optional[int] = None
    r2_rescreen: Optional[str] = None

    for m in phenotype.medications:
        if m.drug_class in ("systemic_anticancer", "investigational_anticancer") and m.citation:
            r2_citations.append(m.citation)

    if nct_id == "NCT04613596" or any(r.rule_type == "prior_metastatic_lines" for r in rules):
        if phenotype.prior_metastatic_lines > 0 or any(
            p.get("setting") == "metastatic" for p in phenotype.prior_lines_detail
        ):
            regimens = ", ".join(p.get("regimen", "systemic therapy") for p in phenotype.prior_lines_detail) or "prior metastatic line"
            r2_blockers.append(
                f"Prior metastatic systemic therapy ({regimens}) violates 0 prior metastatic lines gate"
            )
            # Also compute 28d washout date for multi-trial referral context if last_dose_date exists
            for p in phenotype.prior_lines_detail:
                ldt = _parse_date_safe(p.get("last_dose_date"))
                if ldt:
                    days_since = (ref_dt - ldt).days
                    r2_elapsed = days_since
                    r2_required = 28

    if nct_id == "NCT04787042" or any(r.rule_type == "systemic_washout_days" for r in rules):
        for p in phenotype.prior_lines_detail:
            ldt = _parse_date_safe(p.get("last_dose_date"))
            if ldt:
                days_since = (ref_dt - ldt).days
                if days_since < 28:
                    rs_dt = ldt + timedelta(days=28)
                    rescreen_dates.append(rs_dt)
                    r2_elapsed = days_since
                    r2_required = 28
                    r2_rescreen = rs_dt.isoformat()
                    r2_blockers.append(
                        f"Systemic/investigational therapy ({p.get('regimen')}) ended {days_since}d ago "
                        f"(< 28d washout; earliest clearance {r2_rescreen})"
                    )

    if (nct_id == "NCT04787042" or any(r.rule_type == "live_vaccine_washout_days" for r in rules)) and phenotype.live_vaccine_date:
        vdt = _parse_date_safe(phenotype.live_vaccine_date)
        if vdt:
            v_days = (ref_dt - vdt).days
            if v_days < 30:
                rs_dt = vdt + timedelta(days=30)
                rescreen_dates.append(rs_dt)
                r2_elapsed = v_days
                r2_required = 30
                r2_rescreen = rs_dt.isoformat()
                r2_blockers.append(f"Live vaccine administered {v_days}d ago (< 30d washout; clearance {r2_rescreen})")
                r2_citations.extend(_find_citations_for_biomarker(phenotype, "vaccine"))

    if (nct_id == "NCT04787042" or any(r.rule_type == "major_surgery_washout_days" for r in rules)) and phenotype.major_surgery_date:
        sdt = _parse_date_safe(phenotype.major_surgery_date)
        if sdt:
            s_days = (ref_dt - sdt).days
            if s_days < 28:
                rs_dt = sdt + timedelta(days=28)
                rescreen_dates.append(rs_dt)
                r2_elapsed = s_days
                r2_required = 28
                r2_rescreen = rs_dt.isoformat()
                r2_blockers.append(f"Major surgery performed {s_days}d ago (< 28d washout; clearance {r2_rescreen})")
                r2_citations.extend(_find_citations_for_biomarker(phenotype, "surgery"))

    if nct_id == "NCT06890598" or any(r.rule_type in ("prior_grade3_irae", "autoimmune_active", "prior_malignancy_2yr") for r in rules):
        if phenotype.prior_grade3_irae:
            r2_blockers.append("Prior Grade >= 3 immune-related adverse event (irAE) on immunotherapy")
            r2_citations.extend(_find_citations_for_biomarker(phenotype, "Grade 3", "irAE"))
        if phenotype.autoimmune_active:
            r2_blockers.append("Active autoimmune disease requiring systemic treatment within 2 years")
            r2_citations.extend(_find_citations_for_biomarker(phenotype, "Autoimmune"))
        if phenotype.prior_malignancy_2yr:
            r2_blockers.append("Other active malignancy progressing/requiring treatment within 2 years")
            r2_citations.extend(_find_citations_for_biomarker(phenotype, "malignancy"))

    if r2_blockers:
        blockers.extend(r2_blockers)
        findings.append(
            SafetyFinding(
                rule_code="R2",
                severity="BLOCKER",
                title="R2 Systemic Therapy / Washout / Immunotherapy Exclusion Triggered",
                calculation_detail="; ".join(r2_blockers),
                washout_days_elapsed=r2_elapsed,
                washout_days_required=r2_required,
                earliest_rescreen_date=r2_rescreen,
                citations=r2_citations,
            )
        )
    else:
        findings.append(
            SafetyFinding(
                rule_code="R2",
                severity="PASS",
                title="R2 Systemic Washout, Vaccine & Surgical Windows Cleared",
                calculation_detail="All systemic therapy lines, washout intervals (>=28d/30d), and immunotherapy history gates cleared.",
                citations=r2_citations,
            )
        )

    # =========================================================================
    # RULE R3: Thoracic / Lung Radiation & Recent Radiotherapy Gate
    # =========================================================================
    r3_blockers: list[str] = []
    r3_citations: list[LineCitation] = []
    r3_elapsed: Optional[int] = None
    r3_required: Optional[int] = None
    r3_rescreen: Optional[str] = None

    for rt in phenotype.radiation_history:
        if rt.citation:
            r3_citations.append(rt.citation)
        edt = _parse_date_safe(rt.end_date)
        if edt is None:
            continue
        days_ago = (ref_dt - edt).days
        if rt.is_thoracic_lung and rt.dose_gy > 30.0 and days_ago < 180:
            rs_dt = edt + timedelta(days=180)
            rescreen_dates.append(rs_dt)
            r3_elapsed = days_ago
            r3_required = 180
            r3_rescreen = rs_dt.isoformat()
            r3_blockers.append(
                f"Thoracic/lung RT {rt.dose_gy:g} Gy (> 30 Gy) ended {rt.end_date} ({days_ago}d ago < 180d limit; clearance {r3_rescreen})"
            )
        elif (nct_id == "NCT04787042" or any(r.rule_type == "any_rt_washout_days" for r in rules)) and days_ago < 14:
            rs_dt = edt + timedelta(days=14)
            rescreen_dates.append(rs_dt)
            r3_elapsed = days_ago
            r3_required = 14
            r3_rescreen = rs_dt.isoformat()
            r3_blockers.append(
                f"Recent radiotherapy ({rt.site}) ended {days_ago}d ago (< 14d washout; clearance {r3_rescreen})"
            )

    if phenotype.radiation_complication:
        r3_blockers.append("Radiation-induced pneumonitis or severe esophageal dysphagia documented")
    if (nct_id == "NCT06890598" or any(r.rule_type == "oral_swallow" for r in rules)) and not phenotype.able_to_swallow_oral:
        r3_blockers.append("Unable to swallow intact oral medication (post-RT esophageal stricture/dysphagia)")
        r3_citations.extend(_find_citations_for_biomarker(phenotype, "swallow"))

    if r3_blockers:
        blockers.extend(r3_blockers)
        findings.append(
            SafetyFinding(
                rule_code="R3",
                severity="BLOCKER",
                title="R3 Radiotherapy Dose / Washout Window Violation",
                calculation_detail="; ".join(r3_blockers),
                washout_days_elapsed=r3_elapsed,
                washout_days_required=r3_required,
                earliest_rescreen_date=r3_rescreen,
                citations=r3_citations,
            )
        )
    else:
        findings.append(
            SafetyFinding(
                rule_code="R3",
                severity="PASS",
                title="R3 Thoracic / Palliative Radiotherapy Windows Cleared",
                calculation_detail="No thoracic/lung RT > 30 Gy within 180 days and no recent RT within 14 days.",
                citations=r3_citations,
            )
        )

    # =========================================================================
    # RULE R4: CTCAE v5.0 Grade >= 2 Organ Reserve Safety Floor
    # =========================================================================
    r4_blockers: list[str] = []
    r4_citations = _find_citations_for_biomarker(phenotype, "eGFR", "AST", "ALT", "Bilirubin", "ANC", "Platelets", "ECOG")
    labs = phenotype.labs

    egfr_val = labs.get("egfr_ml_min")
    if egfr_val is not None and egfr_val < 50:
        r4_blockers.append(f"eGFR {egfr_val:g} mL/min/1.73m2 (< 50 floor, CTCAE Grade >= 2)")
    ast_val = labs.get("ast_u_l")
    if ast_val is not None and ast_val > 100:
        r4_blockers.append(f"AST {ast_val:g} U/L ({ast_val / 40.0:.2f}x ULN 40 > 100 U/L [2.5x ULN], CTCAE Grade >= 2)")
    alt_val = labs.get("alt_u_l")
    if alt_val is not None and alt_val > 100:
        r4_blockers.append(f"ALT {alt_val:g} U/L ({alt_val / 40.0:.2f}x ULN 40 > 100 U/L [2.5x ULN], CTCAE Grade >= 2)")
    bili_val = labs.get("bilirubin_mg_dl")
    if bili_val is not None and bili_val > 1.8:
        r4_blockers.append(f"Total Bilirubin {bili_val:g} mg/dL ({bili_val / 1.2:.2f}x ULN 1.2 > 1.8 mg/dL [1.5x ULN], CTCAE Grade >= 2)")
    anc_val = labs.get("anc_u_l")
    if anc_val is not None and anc_val < 1500:
        r4_blockers.append(f"ANC {anc_val:,} /uL (< 1,500 /uL floor, CTCAE Grade >= 2)")
    plt_val = labs.get("platelets_u_l")
    if plt_val is not None and plt_val < 100000:
        r4_blockers.append(f"Platelets {plt_val:,} /uL (< 100,000 /uL floor, CTCAE Grade >= 2)")
    if phenotype.ecog is not None and phenotype.ecog > 1:
        r4_blockers.append(f"ECOG Performance Status {phenotype.ecog} (> 1 ceiling)")

    if r4_blockers:
        blockers.extend(r4_blockers)
        findings.append(
            SafetyFinding(
                rule_code="R4",
                severity="BLOCKER",
                title="R4 CTCAE v5.0 Grade >= 2 Organ Reserve Violation",
                calculation_detail="; ".join(r4_blockers),
                citations=r4_citations,
            )
        )
    else:
        findings.append(
            SafetyFinding(
                rule_code="R4",
                severity="PASS",
                title="R4 CTCAE v5.0 Grade 0/1 Organ Reserve Cleared",
                calculation_detail=(
                    f"eGFR={egfr_val}, AST={ast_val} U/L, ALT={alt_val} U/L, "
                    f"Bili={bili_val} mg/dL, ANC={anc_val}/uL, Platelets={plt_val}/uL, ECOG={phenotype.ecog}."
                ),
                citations=r4_citations,
            )
        )

    # =========================================================================
    # RULE R5: Oncogenic Driver & Biomarker Gate (+ Pending Assay Handling)
    # =========================================================================
    r5_blockers: list[str] = []
    r5_pending: list[str] = []
    bm = phenotype.biomarkers
    r5_citations = _find_citations_for_biomarker(
        phenotype, "KRAS", "PD-L1", "PD_L1", "EGFR", "ALK", "TRK", "Estrogen", "Progesterone", "HER2", "ER:", "PR:", "Biopsy"
    )

    if nct_id == "NCT04613596":
        kras = bm.get("kras_g12c")
        pdl1 = bm.get("pd_l1_tps")
        egfr_m = bm.get("egfr_mut")
        alk_m = bm.get("alk_fusion")
        if kras is not None and kras not in ("POSITIVE", "PENDING_LAB_RESULT"):
            r5_blockers.append(f"KRAS G12C status is {kras} (POSITIVE required)")
        if isinstance(pdl1, (int, float)) and pdl1 < 50:
            r5_blockers.append(f"PD-L1 TPS {pdl1}% (< 50% required for Phase 3)")
        if egfr_m == "POSITIVE" or alk_m == "POSITIVE":
            r5_blockers.append("Actionable EGFR or ALK alteration detected (excluded)")
        if not r5_blockers and ("PENDING_LAB_RESULT" in (kras, pdl1, egfr_m, alk_m) or pdl1 is None or kras is None):
            r5_pending.append("Required KRAS G12C / PD-L1 / EGFR / ALK panel is PENDING_LAB_RESULT (or unrecorded)")
        # CNS untreated lesion > 2.0 cm or brainstem
        cns = phenotype.cns_status
        if cns.get("has_lesions") and not cns.get("treated"):
            if cns.get("max_size_cm") and cns["max_size_cm"] > 2.0:
                r5_blockers.append(f"Untreated brain lesion {cns['max_size_cm']} cm (> 2.0 cm limit)")
            if cns.get("brainstem"):
                r5_blockers.append("Brainstem lesion detected (excluded)")

    elif nct_id == "NCT04787042":
        dx = phenotype.histology_group or ""
        pending_vals = [
            k for k, v in bm.items()
            if k != "pending_panels" and v == "PENDING_LAB_RESULT"
        ]
        if pending_vals or bm.get("pending_panels"):
            r5_pending.append(f"Required tumor biomarker/eval pending: {', '.join(bm.get('pending_panels') or pending_vals)}")
        elif phenotype.accessible_biopsy_lesion == "PENDING_CLINICAL_EVAL":
            r5_pending.append("Accessible biopsy lesion feasibility is PENDING_CLINICAL_EVAL")
        else:
            if dx == "NSCLC" and (
                bm.get("egfr_mut") == "POSITIVE"
                or bm.get("alk_fusion") == "POSITIVE"
                or bm.get("trk_fusion") == "POSITIVE"
            ):
                r5_blockers.append("NSCLC with actionable EGFR/ALK/TRK alteration (excluded)")
            if dx == "TNBC" and bm.get("tnbc_confirmed") is False:
                r5_blockers.append("Non-TNBC receptor profile (ER+/PR+/HER2+ excluded)")

    elif nct_id == "NCT06890598":
        kras = bm.get("kras_g12c")
        pdl1 = bm.get("pd_l1_tps")
        egfr_m = bm.get("egfr_mut")
        alk_m = bm.get("alk_fusion")
        if kras is not None and kras not in ("POSITIVE", "PENDING_LAB_RESULT"):
            r5_blockers.append(f"KRAS G12C status is {kras} (POSITIVE required)")
        if egfr_m == "POSITIVE" or alk_m == "POSITIVE":
            r5_blockers.append("Actionable EGFR or ALK alteration detected (excluded)")
        if not r5_blockers and ("PENDING_LAB_RESULT" in (kras, pdl1, egfr_m, alk_m) or pdl1 is None or kras is None):
            r5_pending.append("Required KRAS G12C / PD-L1 / EGFR / ALK surgical reflex panel is PENDING_LAB_RESULT (or unrecorded)")

    else:
        # Generic NCT trial evaluation based on extracted rules
        if bm.get("pending_panels"):
            r5_pending.append(f"Biomarker panel pending: {', '.join(bm['pending_panels'])}")
        for rule in rules:
            if rule.rule_type == "kras_g12c" and bm.get("kras_g12c") != "POSITIVE":
                r5_blockers.append(f"KRAS G12C status is {bm.get('kras_g12c') or 'MISSING'} (POSITIVE required)")
            if rule.rule_type == "pd_l1_tps":
                tps = bm.get("pd_l1_tps")
                if isinstance(tps, (int, float)) and tps < float(rule.threshold_value or 50):
                    r5_blockers.append(f"PD-L1 TPS {tps}% (< {rule.threshold_value}% required)")
            if rule.rule_type == "driver_exclusion" and (
                bm.get("egfr_mut") == "POSITIVE" or bm.get("alk_fusion") == "POSITIVE"
            ):
                r5_blockers.append("Actionable EGFR/ALK driver detected (excluded)")

    if r5_blockers:
        blockers.extend(r5_blockers)
        findings.append(
            SafetyFinding(
                rule_code="R5",
                severity="BLOCKER",
                title="R5 Oncogenic Driver / Biomarker Gate Failed",
                calculation_detail="; ".join(r5_blockers),
                citations=r5_citations,
            )
        )
    elif r5_pending:
        pending_reviews.extend(r5_pending)
        findings.append(
            SafetyFinding(
                rule_code="R5",
                severity="NEEDS_REVIEW",
                title="R5 Pending Biomarker / Reflex Assay Gate",
                calculation_detail="; ".join(r5_pending),
                citations=r5_citations,
            )
        )
    else:
        findings.append(
            SafetyFinding(
                rule_code="R5",
                severity="PASS",
                title="R5 Oncogenic Driver & Biomarker Profile Verified",
                calculation_detail="All protocol-required molecular inclusions met and actionable driver exclusions negative.",
                citations=r5_citations,
            )
        )

    # =========================================================================
    # Per-Criterion Verdicts Mapping
    # =========================================================================
    for rule in rules:
        rt = rule.rule_type
        cits: list[LineCitation] = [rule.citation]
        status: str = "MET"
        reasoning: str = "Verified against EHR evidence."

        if rt == "age":
            req_age = int(rule.threshold_value or 18)
            if phenotype.age is None:
                status = "NEEDS_REVIEW"
                reasoning = "Age not documented in EHR."
            elif phenotype.age >= req_age:
                status = "MET"
                reasoning = f"Patient age {phenotype.age} >= {req_age} years."
                cits.extend(_find_citations_for_biomarker(phenotype, "yo", "year-old"))
            else:
                status = "NOT_MET"
                reasoning = f"Patient age {phenotype.age} < {req_age} years."

        elif rt == "ecog":
            if phenotype.ecog is None:
                status = "NEEDS_REVIEW"
                reasoning = "ECOG Performance Status missing."
            elif phenotype.ecog <= 1:
                status = "MET"
                reasoning = f"ECOG Performance Status {phenotype.ecog} <= 1."
                cits.extend(_find_citations_for_biomarker(phenotype, "ECOG"))
            else:
                status = "NOT_MET"
                reasoning = f"ECOG Performance Status {phenotype.ecog} > 1."
                cits.extend(_find_citations_for_biomarker(phenotype, "ECOG"))

        elif rt in ("histology_nsclc", "histology_solid_tumor"):
            if phenotype.diagnosis:
                if rt == "histology_nsclc" and phenotype.histology_group not in ("NSCLC", None):
                    status = "NOT_MET"
                    reasoning = f"Diagnosis '{phenotype.diagnosis}' is not NSCLC."
                else:
                    status = "MET"
                    reasoning = f"Histologically confirmed {phenotype.diagnosis}."
                cits.extend(_find_citations_for_biomarker(phenotype, "Diagnosis"))
            else:
                status = "NEEDS_REVIEW"
                reasoning = "Histologic diagnosis missing."

        elif rt == "tnbc_receptors":
            if phenotype.histology_group == "TNBC":
                cits.extend(_find_citations_for_biomarker(phenotype, "ER", "PR", "HER2", "Estrogen", "Progesterone"))
                if phenotype.biomarkers.get("tnbc_confirmed") == "PENDING_LAB_RESULT":
                    status = "NEEDS_REVIEW"
                    reasoning = "TNBC receptor assay PENDING_LAB_RESULT."
                elif phenotype.biomarkers.get("tnbc_confirmed") is False:
                    status = "NOT_MET"
                    reasoning = "Non-TNBC receptor profile (ER+/PR+/HER2+)."
                else:
                    status = "MET"
                    reasoning = "Confirmed triple-negative receptor profile (ER-, PR-, HER2-)."
            else:
                status = "MET"
                reasoning = f"Not applicable to non-TNBC histology ({phenotype.histology_group or 'solid tumor'})."

        elif rt == "kras_g12c":
            kras_val = phenotype.biomarkers.get("kras_g12c")
            cits.extend(_find_citations_for_biomarker(phenotype, "KRAS"))
            if kras_val == "PENDING_LAB_RESULT":
                status = "NEEDS_REVIEW"
                reasoning = "KRAS G12C testing is PENDING_LAB_RESULT."
            elif kras_val == "POSITIVE":
                status = "MET"
                reasoning = "KRAS p.G12C mutation POSITIVE."
            else:
                status = "NOT_MET"
                reasoning = f"KRAS G12C status is {kras_val or 'NOT DETECTED'} (POSITIVE required)."

        elif rt == "pd_l1_tps":
            pdl1 = phenotype.biomarkers.get("pd_l1_tps")
            req_tps = int(rule.threshold_value or 50)
            cits.extend(_find_citations_for_biomarker(phenotype, "PD-L1", "PD_L1"))
            if pdl1 == "PENDING_LAB_RESULT" or pdl1 is None:
                status = "NEEDS_REVIEW"
                reasoning = "PD-L1 TPS IHC is PENDING_LAB_RESULT."
            elif isinstance(pdl1, (int, float)) and pdl1 >= req_tps:
                status = "MET"
                reasoning = f"PD-L1 TPS = {pdl1}% (>= {req_tps}% required)."
            else:
                status = "NOT_MET"
                reasoning = f"PD-L1 TPS = {pdl1}% (< {req_tps}% required)."

        elif rt == "pd_l1_known":
            pdl1 = phenotype.biomarkers.get("pd_l1_tps")
            cits.extend(_find_citations_for_biomarker(phenotype, "PD-L1", "PD_L1"))
            if pdl1 == "PENDING_LAB_RESULT" or pdl1 is None:
                status = "NEEDS_REVIEW"
                reasoning = "PD-L1 IHC expression is PENDING_LAB_RESULT (must be known)."
            else:
                status = "MET"
                reasoning = f"Known PD-L1 expression documented (TPS = {pdl1}%)."

        elif rt == "driver_exclusion":
            cits.extend(_find_citations_for_biomarker(phenotype, "EGFR", "ALK", "TRK"))
            egfr_m = phenotype.biomarkers.get("egfr_mut")
            alk_m = phenotype.biomarkers.get("alk_fusion")
            trk_m = phenotype.biomarkers.get("trk_fusion")
            if "PENDING_LAB_RESULT" in (egfr_m, alk_m, trk_m):
                status = "NEEDS_REVIEW"
                reasoning = "Reflex EGFR/ALK panel is PENDING_LAB_RESULT."
            elif egfr_m == "POSITIVE" or alk_m == "POSITIVE" or trk_m == "POSITIVE":
                status = "EXCLUDED"
                reasoning = "Actionable driver alteration detected (EGFR/ALK/TRK positive)."
            else:
                status = "MET"
                reasoning = "Cleared: EGFR/ALK/TRK driver alterations negative."

        elif rt == "measurable_recist":
            cits.extend(_find_citations_for_biomarker(phenotype, "RECIST"))
            if phenotype.measurable_recist is True:
                status = "MET"
                reasoning = "Measurable disease per RECIST 1.1 documented."
            elif phenotype.measurable_recist is False:
                status = "NOT_MET"
                reasoning = "No measurable RECIST 1.1 lesion."
            else:
                status = "NEEDS_REVIEW"
                reasoning = "RECIST 1.1 measurability not specified."

        elif rt == "accessible_biopsy":
            cits.extend(_find_citations_for_biomarker(phenotype, "Biopsy"))
            if phenotype.accessible_biopsy_lesion == "PENDING_CLINICAL_EVAL":
                status = "NEEDS_REVIEW"
                reasoning = "Accessible biopsy lesion feasibility is PENDING_CLINICAL_EVAL."
            elif phenotype.accessible_biopsy_lesion:
                status = "MET"
                reasoning = "Accessible tumor lesion confirmed for biopsy."
            else:
                status = "NOT_MET"
                reasoning = "No accessible tumor lesion for mandatory biopsy."

        elif rt == "oral_swallow":
            cits.extend(_find_citations_for_biomarker(phenotype, "swallow"))
            if phenotype.able_to_swallow_oral:
                status = "MET"
                reasoning = "Able to swallow intact oral tablets."
            else:
                status = "NOT_MET"
                reasoning = "Unable to swallow oral medication."

        elif rt == "cns_inclusion":
            cits.extend(_find_citations_for_biomarker(phenotype, "Brain MRI"))
            cns = phenotype.cns_status
            if not cns.get("has_lesions"):
                status = "MET"
                reasoning = "No evidence of brain metastases."
            elif cns.get("treated") and not cns.get("needs_immediate_local_therapy"):
                status = "MET"
                reasoning = "Previously treated brain metastasis clinically/radiologically stable without need for immediate local therapy."
            elif cns.get("needs_immediate_local_therapy"):
                status = "NOT_MET"
                reasoning = "Symptomatic untreated brain lesion with peritumoral edema needing local CNS management."
            else:
                status = "MET"
                reasoning = "Brain lesion stable without immediate local therapy requirement."

        elif rt == "cns_untreated_max_cm":
            cits.extend(_find_citations_for_biomarker(phenotype, "Brain MRI"))
            cns = phenotype.cns_status
            if cns.get("has_lesions") and not cns.get("treated") and cns.get("max_size_cm") and cns["max_size_cm"] > float(rule.threshold_value or 2.0):
                status = "EXCLUDED"
                reasoning = f"Untreated brain lesion {cns['max_size_cm']} cm > {rule.threshold_value} cm ceiling."
            else:
                status = "MET"
                reasoning = "Cleared: no untreated brain lesions > 2.0 cm."

        elif rt == "cns_brainstem_excl":
            cits.extend(_find_citations_for_biomarker(phenotype, "Brain MRI"))
            if phenotype.cns_status.get("brainstem"):
                status = "EXCLUDED"
                reasoning = "Brainstem lesion present."
            else:
                status = "MET"
                reasoning = "Cleared: no brainstem lesions."

        elif rt == "cns_active_excl":
            cits.extend(_find_citations_for_biomarker(phenotype, "Brain MRI"))
            cns = phenotype.cns_status
            if cns.get("has_lesions") and not cns.get("treated"):
                status = "EXCLUDED"
                reasoning = "Active untreated CNS metastasis present."
            else:
                status = "MET"
                reasoning = "Cleared: no active untreated CNS metastases."

        elif rt == "steroid_ceiling_mg":
            cits.extend(r1_citations)
            if max_ongoing_pred_eq > float(rule.threshold_value or 10.0):
                status = "EXCLUDED"
                reasoning = (
                    f"Ongoing systemic steroid equals {max_ongoing_pred_eq:.2f} mg/day Prednisone eq "
                    f"(> {rule.threshold_value:g} mg/day ceiling)."
                )
            else:
                status = "MET"
                reasoning = f"Cleared: active systemic steroid Prednisone eq = {max_ongoing_pred_eq:.1f} mg/day <= {rule.threshold_value:g} mg/day."

        elif rt == "cns_steroid_washout_days":
            cits.extend(r1_citations)
            if r1_rescreen:
                status = "EXCLUDED"
                reasoning = f"Treated brain met steroid washout < 14d (clearance {r1_rescreen})."
            else:
                status = "MET"
                reasoning = "Cleared: no CNS steroid treatment within past 14 days."

        elif rt == "prior_metastatic_lines":
            cits.extend(r2_citations or _find_citations_for_biomarker(phenotype, "Prior Systemic"))
            if phenotype.prior_metastatic_lines > 0 or any(p.get("setting") == "metastatic" for p in phenotype.prior_lines_detail):
                status = "EXCLUDED"
                reasoning = f"Received {max(1, phenotype.prior_metastatic_lines)} prior metastatic systemic line(s); 0 allowed."
            else:
                status = "MET"
                reasoning = "Cleared: 0 prior systemic lines for metastatic disease."

        elif rt == "systemic_washout_days":
            cits.extend(r2_citations or _find_citations_for_biomarker(phenotype, "Prior Systemic"))
            req_d = int(rule.threshold_value or 28)
            viol = [
                p for p in phenotype.prior_lines_detail
                if _parse_date_safe(p.get("last_dose_date")) and (ref_dt - _parse_date_safe(p.get("last_dose_date"))).days < req_d  # type: ignore[operator]
            ]
            if viol:
                ldt = _parse_date_safe(viol[0]["last_dose_date"])
                days_s = (ref_dt - ldt).days  # type: ignore[operator]
                status = "EXCLUDED"
                reasoning = f"Systemic therapy ended {days_s}d ago (< {req_d}d washout)."
            else:
                status = "MET"
                reasoning = f"Cleared: >= {req_d} days since prior systemic therapy."

        elif rt == "live_vaccine_washout_days":
            cits.extend(_find_citations_for_biomarker(phenotype, "vaccine"))
            req_d = int(rule.threshold_value or 30)
            vdt = _parse_date_safe(phenotype.live_vaccine_date)
            if vdt and (ref_dt - vdt).days < req_d:
                status = "EXCLUDED"
                reasoning = f"Live vaccine {(ref_dt - vdt).days}d ago (< {req_d}d washout)."
            else:
                status = "MET"
                reasoning = f"Cleared: no live vaccine within {req_d} days."

        elif rt == "major_surgery_washout_days":
            cits.extend(_find_citations_for_biomarker(phenotype, "surgery", "lobectomy"))
            req_d = int(rule.threshold_value or 28)
            sdt = _parse_date_safe(phenotype.major_surgery_date)
            if sdt and (ref_dt - sdt).days < req_d:
                status = "EXCLUDED"
                reasoning = f"Major surgery {(ref_dt - sdt).days}d ago (< {req_d}d washout)."
            else:
                status = "MET"
                reasoning = f"Cleared: no major surgery within {req_d} days."

        elif rt == "thoracic_rt_window":
            cits.extend(r3_citations or _find_citations_for_biomarker(phenotype, "Radiotherapy", "RT"))
            viol_rt = [
                rt_e for rt_e in phenotype.radiation_history
                if rt_e.is_thoracic_lung and rt_e.dose_gy > 30.0
                and _parse_date_safe(rt_e.end_date)
                and (ref_dt - _parse_date_safe(rt_e.end_date)).days < 180  # type: ignore[operator]
            ]
            if viol_rt:
                edt = _parse_date_safe(viol_rt[0].end_date)
                days_s = (ref_dt - edt).days  # type: ignore[operator]
                status = "EXCLUDED"
                reasoning = f"Thoracic RT {viol_rt[0].dose_gy:g} Gy ended {days_s}d ago (< 180d limit)."
            else:
                status = "MET"
                reasoning = "Cleared: no thoracic/lung RT > 30 Gy within 180 days."

        elif rt == "any_rt_washout_days":
            cits.extend(r3_citations or _find_citations_for_biomarker(phenotype, "Radiotherapy", "RT"))
            req_d = int(rule.threshold_value or 14)
            viol_rt = [
                rt_e for rt_e in phenotype.radiation_history
                if _parse_date_safe(rt_e.end_date)
                and (ref_dt - _parse_date_safe(rt_e.end_date)).days < req_d  # type: ignore[operator]
            ]
            if viol_rt:
                edt = _parse_date_safe(viol_rt[0].end_date)
                days_s = (ref_dt - edt).days  # type: ignore[operator]
                status = "EXCLUDED"
                reasoning = f"Prior RT ended {days_s}d ago (< {req_d}d washout)."
            else:
                status = "MET"
                reasoning = f"Cleared: no RT within {req_d} days."

        elif rt == "ctcae_grade2_labs":
            cits.extend(r4_citations)
            if r4_blockers:
                status = "EXCLUDED" if rule.category == "EXCLUSION" else "NOT_MET"
                reasoning = "; ".join(r4_blockers)
            else:
                status = "MET"
                reasoning = "Cleared: all chemistry & hematology labs within CTCAE v5.0 Grade 0/1 limits."

        elif rt == "autoimmune_active":
            if phenotype.autoimmune_active:
                status = "EXCLUDED"
                reasoning = "Active autoimmune disease requiring systemic treatment within 2 years."
                cits.extend(_find_citations_for_biomarker(phenotype, "Autoimmune"))
            else:
                status = "MET"
                reasoning = "Cleared: no active autoimmune disease."

        elif rt == "prior_grade3_irae":
            if phenotype.prior_grade3_irae:
                status = "EXCLUDED"
                reasoning = "Prior Grade >= 3 immune-related adverse event (irAE)."
                cits.extend(_find_citations_for_biomarker(phenotype, "Grade 3", "irAE"))
            else:
                status = "MET"
                reasoning = "Cleared: no prior Grade >= 3 irAE."

        elif rt == "prior_malignancy_2yr":
            if phenotype.prior_malignancy_2yr:
                status = "EXCLUDED"
                reasoning = "Other active malignancy within 2 years."
                cits.extend(_find_citations_for_biomarker(phenotype, "malignancy"))
            else:
                status = "MET"
                reasoning = "Cleared: no other active malignancy within 2 years."

        # Deduplicate citations in verdict
        uniq_cits: list[LineCitation] = []
        seen_k: set[tuple[str, int, str]] = set()
        for c in cits:
            k = (c.doc_type, c.line_start, c.verbatim_quote)
            if k not in seen_k:
                seen_k.add(k)
                uniq_cits.append(c.model_copy())

        verdicts.append(
            CriterionVerdict(
                rule_id=rule.rule_id,
                criterion=rule.title,
                category=rule.category,
                status=status,  # type: ignore[arg-type]
                naive_baseline_status=naive_per_rule.get(rule.rule_id),
                reasoning=reasoning,
                citations=uniq_cits,
                verified_by_rule_engine=True,
            )
        )

    # =========================================================================
    # Overall Verdict & Trap Detection
    # =========================================================================
    earliest_rescreen = max(rescreen_dates).isoformat() if rescreen_dates else None

    if blockers:
        overall_verdict = "CONTRAINDICATED"
    elif pending_reviews:
        overall_verdict = "NEEDS_HUMAN_REVIEW"
    else:
        overall_verdict = "ELIGIBLE"

    caught_trap = overall_verdict != naive_verdict
    trap_explanation: Optional[str] = None
    if caught_trap:
        reasons = blockers or pending_reviews
        trap_explanation = (
            f"Naive baseline predicted {naive_verdict}, whereas TrialSwarm Rules R1-R5 determined "
            f"{overall_verdict}: {' | '.join(reasons)}"
        )

    return (
        findings,
        verdicts,
        overall_verdict,
        naive_verdict,
        caught_trap,
        trap_explanation,
        earliest_rescreen,
    )

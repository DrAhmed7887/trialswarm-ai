"""Deterministic synthetic oncology cohort generator (seed=20261114).

Generates 120 synthetic patient-protocol screening pairs (40 per trial across
NCT04613596, NCT04787042, and NCT06890598) with ground-truth verdicts and
trap labels computed directly from Clinical Rules R1-R5.
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

SEED = 20261114
REFERENCE_DATE_STR = "2026-11-14"
REFERENCE_DATE = date(2026, 11, 14)

TRIALS = [
    ("NCT04613596", "PHASE3"),
    ("NCT04787042", "PHASE1_PHASE2"),
    ("NCT06890598", "PHASE3"),
]

ARCHETYPE_COUNTS_PER_TRIAL = [
    ("ELIGIBLE", 10),
    ("STEROID_EQUIVALENCE_TRAP", 5),
    ("WASHOUT_WINDOW_TRAP", 5),
    ("RADIATION_TRAP", 5),
    ("ORGAN_LAB_CTCAE_TRAP", 5),
    ("DRIVER_EXCLUSION_TRAP", 5),
    ("MISSING_BIOMARKER_REVIEW", 5),
]

STEROID_FACTORS = {
    "Dexamethasone": 5.0 / 0.75,
    "Methylprednisolone": 5.0 / 4.0,
    "Hydrocortisone": 5.0 / 20.0,
    "Prednisone": 1.0,
    "Prednisolone": 1.0,
}

FIRST_NAMES_F = [
    "Clara", "Nadia", "Hannah", "Beatriz", "Amina", "Priya", "Lydia", "Carmen",
    "Mei", "Ingrid", "Sonia", "Fatima", "Rachel", "Tessa", "Kira", "Maya",
    "Helena", "Yuki", "Miriam", "Nora", "Zainab", "Paula", "Valeria", "Grace",
    "Leila", "Simone", "Ananya", "Rosa", "Freya", "Diana",
]
FIRST_NAMES_M = [
    "Arthur", "Tariq", "Samuel", "Mateo", "Kenji", "Victor", "Omar", "Lucas",
    "Hector", "Daniel", "Rohan", "Jonas", "Idris", "Felix", "Gabriel", "Tomas",
    "Sanjay", "Julian", "Malik", "Henrik", "Rafael", "Caleb", "Ibrahim", "Noah",
    "Leo", "Andres", "Elias", "Nikhil", "Owen", "Darius",
]
LAST_NAMES = [
    "Alvarez", "Mercer", "Kowalski", "Tanaka", "Okafor", "Lindqvist", "Bhattacharya",
    "Moreau", "Haddad", "Novak", "Castellanos", "Petrov", "Kulkarni", "Delgado",
    "Bergstrom", "Sato", "Mansour", "Keller", "Silva", "Cho", "Ndiaye", "Rossi",
    "Weber", "Farouk", "Park", "Solis", "Richter", "Nair", "Gomez", "Bauer",
]


def prednisone_equivalent_mg(drug_name: str, daily_dose_mg: float) -> float:
    """Convert systemic glucocorticoid daily dose to Prednisone equivalent (R1)."""
    factor = STEROID_FACTORS[drug_name]
    return round(daily_dose_mg * factor, 2)


def _format_date(d: date) -> str:
    return d.isoformat()


def _parse_date(date_str: str) -> date:
    return date.fromisoformat(date_str)


def evaluate_patient_eligibility(
    structured_truth: dict[str, Any],
    target_nct: str,
    ref_date: date = REFERENCE_DATE,
) -> tuple[str, str, list[str], str | None]:
    """Compute ground-truth verdict and trap type strictly from R1-R5.

    Returns:
        (verdict, primary_trap_type, violation_reasons, earliest_rescreen_date)
    """
    violations: list[str] = []
    trap_tags: list[str] = []
    rescreen_dates: list[date] = []
    pending_reasons: list[str] = []

    # --- R1: Glucocorticoid Potency Equivalence (> 10.0 mg/day Prednisone eq) ---
    for med in structured_truth.get("medications", []):
        if med.get("type") == "systemic_corticosteroid" and med.get("ongoing"):
            pred_eq = prednisone_equivalent_mg(med["name"], med["daily_dose_mg"])
            if pred_eq > 10.0:
                violations.append(
                    f"R1: Ongoing {med['name']} {med['daily_dose_mg']} mg/day "
                    f"({pred_eq} mg/day Prednisone eq > 10.0 mg/day ceiling)"
                )
                trap_tags.append("STEROID_EQUIVALENCE_TRAP")
        elif (
            target_nct == "NCT04787042"
            and med.get("type") == "systemic_corticosteroid"
            and med.get("last_dose_date")
            and structured_truth.get("cns_lesions", {}).get("has_lesions")
        ):
            days_off = (ref_date - _parse_date(med["last_dose_date"])).days
            if days_off < 14:
                violations.append(
                    f"R1/Excl#16: Treated brain met steroid stopped {days_off}d ago (< 14d required)"
                )
                trap_tags.append("STEROID_EQUIVALENCE_TRAP")
                rescreen_dates.append(_parse_date(med["last_dose_date"]) + timedelta(days=14))

    # --- R2: Systemic Anticancer, Investigational, Vaccine & Surgical Washout ---
    prior_lines = structured_truth.get("prior_lines", [])
    if target_nct == "NCT04613596":
        for line in prior_lines:
            if line.get("setting") == "metastatic":
                violations.append(
                    f"R2: Prior metastatic systemic therapy ({line.get('regimen')}) violates 0 prior lines"
                )
                trap_tags.append("WASHOUT_WINDOW_TRAP")
    elif target_nct == "NCT04787042":
        for line in prior_lines:
            last_dt_str = line.get("last_dose_date")
            if last_dt_str:
                last_dt = _parse_date(last_dt_str)
                days_ago = (ref_date - last_dt).days
                if days_ago < 28:
                    violations.append(
                        f"R2: Systemic/investigational therapy {line.get('regimen')} ended {days_ago}d ago (< 28d washout)"
                    )
                    trap_tags.append("WASHOUT_WINDOW_TRAP")
                    rescreen_dates.append(last_dt + timedelta(days=28))
        vaccine_dt_str = structured_truth.get("live_vaccine_date")
        if vaccine_dt_str:
            v_dt = _parse_date(vaccine_dt_str)
            v_days = (ref_date - v_dt).days
            if v_days < 30:
                violations.append(f"R2: Live vaccine {v_days}d ago (< 30d washout)")
                trap_tags.append("WASHOUT_WINDOW_TRAP")
                rescreen_dates.append(v_dt + timedelta(days=30))
        surg_dt_str = structured_truth.get("major_surgery_date")
        if surg_dt_str:
            s_dt = _parse_date(surg_dt_str)
            s_days = (ref_date - s_dt).days
            if s_days < 28:
                violations.append(f"R2: Major surgery {s_days}d ago (< 28d washout)")
                trap_tags.append("WASHOUT_WINDOW_TRAP")
                rescreen_dates.append(s_dt + timedelta(days=28))
    elif target_nct == "NCT06890598":
        if structured_truth.get("prior_irae_grade_gte3"):
            violations.append("R2/Immunotherapy: Prior Grade >= 3 immune-related adverse event")
            trap_tags.append("WASHOUT_WINDOW_TRAP")
        if structured_truth.get("active_autoimmune_2yr"):
            violations.append("R2/Autoimmune: Active autoimmune disease requiring systemic treatment within 2 years")
            trap_tags.append("WASHOUT_WINDOW_TRAP")
        if structured_truth.get("prior_malignancy_2yr"):
            violations.append("R2/Malignancy: Other active malignancy within past 2 years")
            trap_tags.append("WASHOUT_WINDOW_TRAP")

    # --- R3: Thoracic / Lung Radiation (>30 Gy within 180d, or any RT within 14d) ---
    for rt in structured_truth.get("radiation_history", []):
        end_dt = _parse_date(rt["end_date"])
        days_ago = (ref_date - end_dt).days
        if rt.get("is_thoracic_lung") and rt["total_dose_gy"] > 30.0 and days_ago < 180:
            violations.append(
                f"R3: Thoracic/lung RT {rt['total_dose_gy']} Gy ended {days_ago}d ago (< 180d limit)"
            )
            trap_tags.append("RADIATION_TRAP")
            rescreen_dates.append(end_dt + timedelta(days=180))
        elif target_nct == "NCT04787042" and days_ago < 14:
            violations.append(
                f"R3: Prior RT ({rt['site']}) ended {days_ago}d ago (< 14d washout)"
            )
            trap_tags.append("RADIATION_TRAP")
            rescreen_dates.append(end_dt + timedelta(days=14))
        if rt.get("radiation_pneumonitis") or rt.get("radiation_esophagitis_dysphagia"):
            violations.append(
                "R3: Radiation-induced pneumonitis or severe esophageal dysphagia"
            )
            trap_tags.append("RADIATION_TRAP")

    if target_nct == "NCT06890598" and not structured_truth.get("able_to_swallow_oral", True):
        if "RADIATION_TRAP" not in trap_tags:
            trap_tags.append("RADIATION_TRAP")
        violations.append("R3/Oral: Unable to swallow oral medication (radiation esophagitis/stricture)")

    # --- R4: CTCAE v5.0 Grade >= 2 Organ Reserve Safety Floor ---
    labs = structured_truth.get("labs", {})
    ecog = structured_truth.get("ecog", 0)
    if labs.get("egfr_ml_min", 90) < 50:
        violations.append(f"R4: eGFR {labs['egfr_ml_min']} mL/min/1.73m2 (< 50 floor)")
        trap_tags.append("ORGAN_LAB_CTCAE_TRAP")
    if labs.get("ast_u_l", 20) > 100:
        violations.append(f"R4: AST {labs['ast_u_l']} U/L (> 100 U/L [2.5x ULN 40])")
        trap_tags.append("ORGAN_LAB_CTCAE_TRAP")
    if labs.get("alt_u_l", 20) > 100:
        violations.append(f"R4: ALT {labs['alt_u_l']} U/L (> 100 U/L [2.5x ULN 40])")
        trap_tags.append("ORGAN_LAB_CTCAE_TRAP")
    if labs.get("total_bilirubin_mg_dl", 0.6) > 1.8:
        violations.append(f"R4: Total Bilirubin {labs['total_bilirubin_mg_dl']} mg/dL (> 1.8 mg/dL [1.5x ULN 1.2])")
        trap_tags.append("ORGAN_LAB_CTCAE_TRAP")
    if labs.get("anc_per_ul", 3500) < 1500:
        violations.append(f"R4: ANC {labs['anc_per_ul']} /uL (< 1500 /uL floor)")
        trap_tags.append("ORGAN_LAB_CTCAE_TRAP")
    if labs.get("platelets_per_ul", 200000) < 100000:
        violations.append(f"R4: Platelets {labs['platelets_per_ul']} /uL (< 100,000 /uL floor)")
        trap_tags.append("ORGAN_LAB_CTCAE_TRAP")
    if ecog > 1:
        violations.append(f"R4: ECOG Performance Status {ecog} (> 1 ceiling)")
        trap_tags.append("ORGAN_LAB_CTCAE_TRAP")

    # --- R5: Oncogenic Driver & Biomarker Gate ---
    bm = structured_truth.get("biomarkers", {})
    if target_nct == "NCT04613596":
        kras = bm.get("kras_g12c")
        pdl1 = bm.get("pd_l1_tps_pct")
        if kras == "PENDING_LAB_RESULT" or pdl1 == "PENDING_LAB_RESULT" or bm.get("egfr") == "PENDING_LAB_RESULT" or bm.get("alk") == "PENDING_LAB_RESULT":
            pending_reasons.append("R5: Required KRAS G12C / PD-L1 / EGFR / ALK biomarker is PENDING_LAB_RESULT")
        else:
            if kras != "POSITIVE":
                violations.append(f"R5: KRAS G12C status is {kras} (POSITIVE required)")
                trap_tags.append("DRIVER_EXCLUSION_TRAP")
            if isinstance(pdl1, (int, float)) and pdl1 < 50:
                violations.append(f"R5: PD-L1 TPS {pdl1}% (< 50% required for Phase 3)")
                trap_tags.append("DRIVER_EXCLUSION_TRAP")
            if bm.get("egfr") == "POSITIVE" or bm.get("alk") == "POSITIVE":
                violations.append("R5: Actionable EGFR/ALK driver detected (exclusion)")
                trap_tags.append("DRIVER_EXCLUSION_TRAP")
    elif target_nct == "NCT04787042":
        dx = structured_truth.get("histology_group", "")
        if any(v == "PENDING_LAB_RESULT" for v in bm.values()):
            pending_reasons.append("R5: Required tumor biomarker / receptor assay is PENDING_LAB_RESULT")
        elif structured_truth.get("accessible_biopsy_lesion") == "PENDING_CLINICAL_EVAL":
            pending_reasons.append("R5: Accessible biopsy lesion feasibility is PENDING_CLINICAL_EVAL")
        else:
            if dx == "NSCLC" and (bm.get("egfr") == "POSITIVE" or bm.get("alk") == "POSITIVE" or bm.get("trk") == "POSITIVE"):
                violations.append("R5: NSCLC with actionable EGFR/ALK/TRK alteration (excluded)")
                trap_tags.append("DRIVER_EXCLUSION_TRAP")
            if dx == "TNBC" and (bm.get("er") == "POSITIVE" or bm.get("pr") == "POSITIVE" or bm.get("her2") == "POSITIVE"):
                violations.append("R5: Non-TNBC receptor profile (ER+/PR+/HER2+ excluded)")
                trap_tags.append("DRIVER_EXCLUSION_TRAP")
    elif target_nct == "NCT06890598":
        kras = bm.get("kras_g12c")
        pdl1 = bm.get("pd_l1_tps_pct")
        egfr = bm.get("egfr")
        alk = bm.get("alk")
        if "PENDING_LAB_RESULT" in (kras, pdl1, egfr, alk):
            pending_reasons.append("R5: Required KRAS G12C / PD-L1 / EGFR / ALK panel is PENDING_LAB_RESULT")
        else:
            if kras != "POSITIVE":
                violations.append(f"R5: KRAS G12C status is {kras} (POSITIVE required)")
                trap_tags.append("DRIVER_EXCLUSION_TRAP")
            if egfr == "POSITIVE" or alk == "POSITIVE":
                violations.append("R5: Actionable EGFR or ALK alteration detected (excluded)")
                trap_tags.append("DRIVER_EXCLUSION_TRAP")

    earliest_rescreen = _format_date(max(rescreen_dates)) if rescreen_dates else None

    if violations:
        return "CONTRAINDICATED", trap_tags[0], violations, earliest_rescreen
    if pending_reasons:
        return "NEEDS_HUMAN_REVIEW", "MISSING_BIOMARKER_REVIEW", pending_reasons, None
    return "ELIGIBLE", "ELIGIBLE", [], None


def _render_ehr_text(record: dict[str, Any]) -> str:
    st = record["structured_truth"]
    labs = st["labs"]
    bm = st["biomarkers"]
    cns = st["cns_lesions"]
    meds = st["medications"]
    rts = st["radiation_history"]
    priors = st["prior_lines"]

    bm_lines = []
    for k, v in bm.items():
        bm_lines.append(f"- {k.upper()}: {v}")

    if meds:
        med_lines = []
        for m in meds:
            if m.get("type") == "systemic_corticosteroid":
                status = "ONGOING" if m.get("ongoing") else f"discontinued {m.get('last_dose_date')}"
                peq = prednisone_equivalent_mg(m["name"], m["daily_dose_mg"]) if m.get("ongoing") else 0.0
                med_lines.append(
                    f"- {m['name']} {m.get('dose_schedule', '')} (daily_dose_mg={m['daily_dose_mg']} mg/day, "
                    f"Prednisone_eq={peq} mg/day, started {m.get('start_date')}, status={status}; "
                    f"indication: {m.get('indication', 'clinical management')})"
                )
            else:
                med_lines.append(f"- {m['name']} ({m.get('dose_schedule', 'maintenance')})")
    else:
        med_lines = ["- Systemic Corticosteroids: None (0.0 mg/day Prednisone equivalent)."]

    if priors:
        for p in priors:
            med_lines.append(
                f"- Prior Systemic Therapy ({p.get('setting')}): {p['regimen']} — last dose {p['last_dose_date']} "
                f"({(REFERENCE_DATE - _parse_date(p['last_dose_date'])).days} days prior to {REFERENCE_DATE_STR})."
            )
    else:
        med_lines.append("- Prior Systemic Anticancer Therapy: None.")

    if st.get("live_vaccine_date"):
        vd = _parse_date(st["live_vaccine_date"])
        med_lines.append(
            f"- Recent Immunization: Live-attenuated vaccine administered {st['live_vaccine_date']} "
            f"({(REFERENCE_DATE - vd).days} days prior to {REFERENCE_DATE_STR})."
        )
    if st.get("major_surgery_date"):
        sd = _parse_date(st["major_surgery_date"])
        med_lines.append(
            f"- Recent Surgical Procedure: Major surgery performed {st['major_surgery_date']} "
            f"({(REFERENCE_DATE - sd).days} days prior to {REFERENCE_DATE_STR})."
        )
    if st.get("prior_irae_grade_gte3"):
        med_lines.append("- Immunotherapy Toxicity History: Prior Grade 3 immune-mediated pneumonitis/colitis on ICI.")
    if st.get("active_autoimmune_2yr"):
        med_lines.append("- Autoimmune History: Active rheumatoid arthritis requiring systemic DMARD therapy within past 2 years.")

    if rts:
        rt_lines = [
            f"- {r['end_date']}: {r['modality']} to {r['site']} — total dose {r['total_dose_gy']} Gy "
            f"(completed {(REFERENCE_DATE - _parse_date(r['end_date'])).days} days prior to {REFERENCE_DATE_STR})"
            + ("; complicated by radiation esophagitis/dysphagia" if r.get("radiation_esophagitis_dysphagia") else "")
            + ("; complicated by radiation pneumonitis" if r.get("radiation_pneumonitis") else "")
            for r in rts
        ]
    else:
        rt_lines = ["- Prior Thoracic or Systemic Radiotherapy: None."]

    if cns.get("has_lesions"):
        cns_str = (
            f"Brain MRI w/ contrast: {cns.get('count', 1)} parenchymal lesion(s), max size {cns.get('max_size_cm', 1.0)} cm "
            f"({cns.get('location', 'frontal')}), brainstem={'YES' if cns.get('brainstem') else 'NO'}, "
            f"treated={'YES (SRS ' + str(cns.get('srs_date')) + ')' if cns.get('treated') else 'NO'}, "
            f"peritumoral_edema={'YES' if cns.get('peritumoral_edema') else 'NO'}."
        )
    else:
        cns_str = "Brain MRI w/ contrast: No intracranial metastasis or leptomeningeal enhancement."

    swallow_str = "Able to swallow intact oral tablets." if st.get("able_to_swallow_oral", True) else "UNABLE to swallow oral medications due to post-RT esophageal stricture/dysphagia."
    biopsy_str = str(st.get("accessible_biopsy_lesion", False))

    sections = [
        f"PATIENT IDENTIFIER: {record['patient_id']} | NAME: {record['name']} | AGE/SEX: {record['age']}yo {record['sex']} | REF DATE: {REFERENCE_DATE_STR}",
        f"TARGET CLINICAL TRIAL: {record['target_nct']} ({record['target_phase']})",
        "",
        "=== DEMOGRAPHICS ===",
        f"{record['name']} is a {record['age']}-year-old {'female' if record['sex'] == 'F' else 'male'} presenting for clinical trial eligibility screening.",
        "",
        "=== DIAGNOSIS & STAGE ===",
        f"Diagnosis: {record['diagnosis']} | Stage: {record['stage']}",
        f"Measurable Disease (RECIST 1.1): {st.get('measurable_disease_recist11')} ({st.get('measurable_lesion_cm', 'N/A')} cm target lesion)",
        f"Accessible Biopsy Lesion: {biopsy_str} | Oral Swallowing: {swallow_str}",
        "",
        "=== PATHOLOGY & MOLECULAR NGS ===",
        *bm_lines,
        "",
        "=== BRAIN MRI / CNS IMAGING ===",
        cns_str,
        "",
        "=== RADIATION ONCOLOGY HISTORY ===",
        *rt_lines,
        "",
        "=== ACTIVE & PRIOR MEDICATIONS ===",
        *med_lines,
        "",
        f"=== LABORATORY PANEL (Collected {labs['test_date']}) ===",
        f"- eGFR: {labs['egfr_ml_min']} mL/min/1.73m2 | AST: {labs['ast_u_l']} U/L (ULN 40) | ALT: {labs['alt_u_l']} U/L (ULN 40)",
        f"- Total Bilirubin: {labs['total_bilirubin_mg_dl']} mg/dL (ULN 1.2) | ANC: {labs['anc_per_ul']} /uL | Platelets: {labs['platelets_per_ul']} /uL",
        "",
        "=== ECOG PERFORMANCE STATUS ===",
        f"ECOG Performance Status: {st['ecog']}",
    ]
    return "\n".join(sections)


def _build_base_truth(rng: random.Random, target_nct: str) -> tuple[str, str, dict[str, Any]]:
    """Build clean, baseline ELIGIBLE clinical profile tailored to target_nct."""
    test_date = "2026-11-12"
    labs = {
        "test_date": test_date,
        "egfr_ml_min": rng.randint(62, 95),
        "ast_u_l": rng.randint(18, 38),
        "alt_u_l": rng.randint(19, 39),
        "total_bilirubin_mg_dl": round(rng.uniform(0.4, 1.0), 1),
        "anc_per_ul": rng.randint(2400, 6200),
        "platelets_per_ul": rng.randint(155000, 340000),
    }

    if target_nct == "NCT04613596":
        dx = "Non-squamous Non-Small Cell Lung Cancer (NSCLC)"
        stage = rng.choice(["Stage IV (cT2aN2M1b)", "Stage IV (cT3N2M1c)", "Unresectable Stage IIIB"])
        truth = {
            "histology_group": "NSCLC",
            "ecog": rng.choice([0, 1]),
            "able_to_swallow_oral": True,
            "measurable_disease_recist11": True,
            "measurable_lesion_cm": round(rng.uniform(2.1, 4.8), 1),
            "accessible_biopsy_lesion": False,
            "biomarkers": {
                "kras_g12c": "POSITIVE",
                "pd_l1_tps_pct": rng.randint(52, 95),
                "egfr": "NEGATIVE",
                "alk": "NEGATIVE",
            },
            "labs": labs,
            "medications": [],
            "radiation_history": [],
            "cns_lesions": {"has_lesions": False, "count": 0},
            "prior_lines": [],
            "live_vaccine_date": None,
            "major_surgery_date": None,
        }
        return dx, stage, truth

    if target_nct == "NCT04787042":
        hist = rng.choice(["TNBC", "NSCLC", "Melanoma"])
        if hist == "TNBC":
            dx = "Metastatic Triple-Negative Breast Cancer (TNBC)"
            bm = {"er": "NEGATIVE", "pr": "NEGATIVE", "her2": "NEGATIVE (IHC 0)"}
        elif hist == "NSCLC":
            dx = "Metastatic Non-Small Cell Lung Cancer (NSCLC)"
            bm = {"egfr": "NEGATIVE", "alk": "NEGATIVE", "trk": "NEGATIVE"}
        else:
            dx = "Metastatic Cutaneous Melanoma"
            bm = {"braf": "WILD-TYPE"}
        stage = "Stage IV"
        last_chemo = _format_date(REFERENCE_DATE - timedelta(days=rng.randint(35, 90)))
        truth = {
            "histology_group": hist,
            "ecog": rng.choice([0, 1]),
            "able_to_swallow_oral": True,
            "measurable_disease_recist11": True,
            "measurable_lesion_cm": round(rng.uniform(1.8, 4.5), 1),
            "accessible_biopsy_lesion": True,
            "biomarkers": bm,
            "labs": labs,
            "medications": [],
            "radiation_history": [],
            "cns_lesions": {"has_lesions": False, "count": 0},
            "prior_lines": [
                {
                    "line_number": 1,
                    "setting": "metastatic",
                    "regimen": "Standard-of-care chemotherapy",
                    "last_dose_date": last_chemo,
                }
            ],
            "live_vaccine_date": None,
            "major_surgery_date": None,
        }
        return dx, stage, truth

    # NCT06890598
    dx = "Resected Stage II-IIIA Non-Small Cell Lung Cancer (NSCLC)"
    stage = rng.choice(["Stage IIB (pT2bN1M0)", "Stage IIIA (pT2bN2M0)", "Stage IIIB (pT3N2M0)"])
    truth = {
        "histology_group": "NSCLC",
        "ecog": rng.choice([0, 1]),
        "able_to_swallow_oral": True,
        "measurable_disease_recist11": False,
        "measurable_lesion_cm": 0.0,
        "accessible_biopsy_lesion": False,
        "biomarkers": {
            "kras_g12c": "POSITIVE",
            "pd_l1_tps_pct": rng.randint(1, 85),
            "egfr": "NEGATIVE",
            "alk": "NEGATIVE",
        },
        "labs": labs,
        "medications": [],
        "radiation_history": [],
        "cns_lesions": {"has_lesions": False, "count": 0},
        "prior_lines": [],
        "prior_irae_grade_gte3": False,
        "active_autoimmune_2yr": False,
        "prior_malignancy_2yr": False,
        "live_vaccine_date": None,
        "major_surgery_date": _format_date(REFERENCE_DATE - timedelta(days=rng.randint(35, 65))),
    }
    return dx, stage, truth


def _inject_archetype(
    rng: random.Random,
    archetype: str,
    target_nct: str,
    truth: dict[str, Any],
) -> None:
    """Mutate baseline truth deterministically to instantiate the target clinical archetype."""
    if archetype == "ELIGIBLE":
        if target_nct == "NCT04613596" and rng.random() < 0.4:
            srs_dt = _format_date(REFERENCE_DATE - timedelta(days=rng.randint(35, 80)))
            stop_dt = _format_date(REFERENCE_DATE - timedelta(days=rng.randint(20, 35)))
            truth["cns_lesions"] = {
                "has_lesions": True,
                "count": 1,
                "max_size_cm": 1.1,
                "location": "left parietal",
                "brainstem": False,
                "treated": True,
                "srs_date": srs_dt,
                "peritumoral_edema": False,
            }
            truth["medications"].append(
                {
                    "name": "Dexamethasone",
                    "type": "systemic_corticosteroid",
                    "daily_dose_mg": 0.0,
                    "dose_schedule": "Tapered off",
                    "start_date": srs_dt,
                    "last_dose_date": stop_dt,
                    "ongoing": False,
                    "indication": "Post-SRS prophylaxis",
                }
            )
        return

    if archetype == "STEROID_EQUIVALENCE_TRAP":
        variant = rng.choice(["Dexamethasone", "Methylprednisolone", "Hydrocortisone"])
        if variant == "Dexamethasone":
            dose = rng.choice([2.0, 3.0, 4.0, 6.0])  # 13.3 to 40.0 mg/day Pred eq
            sched = f"{dose/2:.1f} mg PO BID" if dose >= 4 else f"{dose:.1f} mg PO daily"
        elif variant == "Methylprednisolone":
            dose = rng.choice([12.0, 16.0, 24.0])  # 15.0 to 30.0 mg/day Pred eq
            sched = f"{dose:.0f} mg PO daily"
        else:
            dose = rng.choice([60.0, 80.0])  # 15.0 to 20.0 mg/day Pred eq
            sched = f"{dose/2:.0f} mg PO BID"
        truth["medications"].append(
            {
                "name": variant,
                "type": "systemic_corticosteroid",
                "daily_dose_mg": dose,
                "dose_schedule": sched,
                "start_date": _format_date(REFERENCE_DATE - timedelta(days=rng.randint(7, 25))),
                "last_dose_date": REFERENCE_DATE_STR,
                "ongoing": True,
                "indication": "Symptomatic peritumoral CNS edema / systemic inflammation",
            }
        )
        truth["cns_lesions"] = {
            "has_lesions": True,
            "count": 1,
            "max_size_cm": 1.6,
            "location": "right frontal",
            "brainstem": False,
            "treated": False,
            "peritumoral_edema": True,
        }
        return

    if archetype == "WASHOUT_WINDOW_TRAP":
        if target_nct == "NCT04613596":
            dt = _format_date(REFERENCE_DATE - timedelta(days=rng.randint(15, 75)))
            truth["prior_lines"].append(
                {
                    "line_number": 1,
                    "setting": "metastatic",
                    "regimen": rng.choice(["Carboplatin + Pemetrexed", "Pembrolizumab monotherapy", "Sotorasib (AMG 510)"]),
                    "last_dose_date": dt,
                }
            )
        elif target_nct == "NCT04787042":
            sub = rng.choice(["investigational", "vaccine", "surgery"])
            if sub == "investigational":
                dt = _format_date(REFERENCE_DATE - timedelta(days=rng.randint(8, 25)))
                truth["prior_lines"] = [
                    {
                        "line_number": 2,
                        "setting": "metastatic",
                        "regimen": "Investigational anti-LAG-3 antibody",
                        "last_dose_date": dt,
                    }
                ]
            elif sub == "vaccine":
                truth["live_vaccine_date"] = _format_date(REFERENCE_DATE - timedelta(days=rng.randint(10, 26)))
            else:
                truth["major_surgery_date"] = _format_date(REFERENCE_DATE - timedelta(days=rng.randint(7, 24)))
        else:  # NCT06890598
            sub = rng.choice(["irae", "autoimmune"])
            if sub == "irae":
                truth["prior_irae_grade_gte3"] = True
            else:
                truth["active_autoimmune_2yr"] = True
        return

    if archetype == "RADIATION_TRAP":
        days_ago = rng.randint(40, 155)
        dose_gy = rng.choice([36.0, 45.0, 50.0, 60.0])
        rt_entry = {
            "site": "Thoracic mediastinum / lung",
            "modality": "External Beam RT",
            "total_dose_gy": dose_gy,
            "end_date": _format_date(REFERENCE_DATE - timedelta(days=days_ago)),
            "is_thoracic_lung": True,
        }
        if target_nct == "NCT06890598":
            rt_entry["radiation_esophagitis_dysphagia"] = True
            truth["able_to_swallow_oral"] = False
        truth["radiation_history"].append(rt_entry)
        return

    if archetype == "ORGAN_LAB_CTCAE_TRAP":
        fail_mode = rng.choice(["transaminase", "renal", "bilirubin", "platelets", "anc", "ecog"])
        if fail_mode == "transaminase":
            truth["labs"]["ast_u_l"] = rng.randint(118, 175)
            truth["labs"]["alt_u_l"] = rng.randint(122, 190)
        elif fail_mode == "renal":
            truth["labs"]["egfr_ml_min"] = rng.randint(31, 46)
        elif fail_mode == "bilirubin":
            truth["labs"]["total_bilirubin_mg_dl"] = round(rng.uniform(2.0, 2.9), 1)
        elif fail_mode == "platelets":
            truth["labs"]["platelets_per_ul"] = rng.randint(58000, 89000)
        elif fail_mode == "anc":
            truth["labs"]["anc_per_ul"] = rng.randint(850, 1350)
        else:
            truth["ecog"] = 2
        return

    if archetype == "DRIVER_EXCLUSION_TRAP":
        if target_nct == "NCT04613596":
            trap_choice = rng.choice(["low_pdl1", "non_g12c", "egfr_pos"])
            if trap_choice == "low_pdl1":
                truth["biomarkers"]["pd_l1_tps_pct"] = rng.randint(5, 40)
            elif trap_choice == "non_g12c":
                truth["biomarkers"]["kras_g12c"] = "NEGATIVE (KRAS G12D detected)"
            else:
                truth["biomarkers"]["egfr"] = "POSITIVE"
        elif target_nct == "NCT04787042":
            if truth["histology_group"] == "NSCLC":
                truth["biomarkers"][rng.choice(["egfr", "alk"])] = "POSITIVE"
            elif truth["histology_group"] == "TNBC":
                truth["biomarkers"]["her2"] = "POSITIVE"
            else:
                # Force NSCLC with EGFR positive so exclusion applies unambiguously
                truth["histology_group"] = "NSCLC"
                truth["biomarkers"] = {"egfr": "POSITIVE", "alk": "NEGATIVE", "trk": "NEGATIVE"}
        else:  # NCT06890598
            truth["biomarkers"][rng.choice(["egfr", "alk"])] = "POSITIVE"
        return

    if archetype == "MISSING_BIOMARKER_REVIEW":
        if target_nct == "NCT04613596":
            truth["biomarkers"]["pd_l1_tps_pct"] = "PENDING_LAB_RESULT"
        elif target_nct == "NCT04787042":
            if rng.random() < 0.5:
                key = next(iter(truth["biomarkers"]))
                truth["biomarkers"][key] = "PENDING_LAB_RESULT"
            else:
                truth["accessible_biopsy_lesion"] = "PENDING_CLINICAL_EVAL"
        else:
            truth["biomarkers"]["egfr"] = "PENDING_LAB_RESULT"
            truth["biomarkers"]["alk"] = "PENDING_LAB_RESULT"
        return

    raise ValueError(f"Unknown archetype: {archetype}")


def generate_cohort(seed: int = SEED) -> dict[str, Any]:
    """Generate the deterministic 120-patient synthetic screening cohort."""
    rng = random.Random(seed)
    records: list[dict[str, Any]] = []
    idx = 1

    for target_nct, target_phase in TRIALS:
        for archetype, count in ARCHETYPE_COUNTS_PER_TRIAL:
            for _ in range(count):
                sex = rng.choice(["F", "M"])
                first = rng.choice(FIRST_NAMES_F if sex == "F" else FIRST_NAMES_M)
                last = rng.choice(LAST_NAMES)
                age = rng.randint(42, 78)

                dx, stage, truth = _build_base_truth(rng, target_nct)
                _inject_archetype(rng, archetype, target_nct, truth)
                if target_nct == "NCT04787042" and truth["histology_group"] == "NSCLC":
                    dx = "Metastatic Non-Small Cell Lung Cancer (NSCLC)"

                verdict, trap_type, reasons, rescreen_dt = evaluate_patient_eligibility(
                    truth, target_nct, REFERENCE_DATE
                )

                # Invariant check: deterministic evaluator must agree with intended archetype
                expected_verdict_for_arch = (
                    "ELIGIBLE"
                    if archetype == "ELIGIBLE"
                    else ("NEEDS_HUMAN_REVIEW" if archetype == "MISSING_BIOMARKER_REVIEW" else "CONTRAINDICATED")
                )
                if verdict != expected_verdict_for_arch or trap_type != archetype:
                    raise AssertionError(
                        f"Label mismatch for {target_nct}/{archetype}: "
                        f"got verdict={verdict}, trap={trap_type}, reasons={reasons}"
                    )

                patient_id = f"COHORT-{idx:03d}"
                record: dict[str, Any] = {
                    "patient_id": patient_id,
                    "name": f"{first} {last}",
                    "age": age,
                    "sex": sex,
                    "diagnosis": dx,
                    "stage": stage,
                    "target_nct": target_nct,
                    "target_phase": target_phase,
                    "reference_date": REFERENCE_DATE_STR,
                    "archetype": archetype,
                    "expected_verdict": verdict,
                    "expected_trap_type": trap_type,
                    "earliest_rescreen_date": rescreen_dt,
                    "clinical_summary": "; ".join(reasons) if reasons else "Meets all inclusion/exclusion and safety floor criteria.",
                    "structured_truth": truth,
                }
                ehr_text = _render_ehr_text(record)
                record["ehr_text"] = ehr_text
                record["ehr_lines"] = [
                    {"line": ln_idx, "text": ln_txt}
                    for ln_idx, ln_txt in enumerate(ehr_text.splitlines(), start=1)
                ]
                records.append(record)
                idx += 1

    by_trial: dict[str, int] = {}
    by_verdict: dict[str, int] = {}
    by_archetype: dict[str, int] = {}
    for r in records:
        by_trial[r["target_nct"]] = by_trial.get(r["target_nct"], 0) + 1
        by_verdict[r["expected_verdict"]] = by_verdict.get(r["expected_verdict"], 0) + 1
        by_archetype[r["archetype"]] = by_archetype.get(r["archetype"], 0) + 1

    return {
        "seed": seed,
        "reference_date": REFERENCE_DATE_STR,
        "total_count": len(records),
        "counts": {
            "by_trial": by_trial,
            "by_verdict": by_verdict,
            "by_archetype": by_archetype,
        },
        "patients": records,
    }


def main() -> None:
    payload = generate_cohort(SEED)
    out_path = Path("data/cohort_120.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Generated {payload['total_count']} synthetic screening pairs -> {out_path}")
    print(f"By trial: {payload['counts']['by_trial']}")
    print(f"By verdict: {payload['counts']['by_verdict']}")
    print(f"By archetype: {payload['counts']['by_archetype']}")


if __name__ == "__main__":
    main()

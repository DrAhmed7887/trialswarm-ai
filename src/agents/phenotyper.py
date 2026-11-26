"""@phenotyper agent: extracts grounded PatientPhenotype from structured or unstructured EHR lines."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional, Union

from src.schemas import (
    LineCitation,
    MedicationEntry,
    PatientPhenotype,
    RadiationEntry,
)

STEROID_NAMES = (
    "Dexamethasone",
    "Methylprednisolone",
    "Hydrocortisone",
    "Prednisone",
    "Prednisolone",
)


def ensure_ehr_lines(patient: Union[dict[str, Any], str]) -> tuple[str, list[dict[str, Any]]]:
    """Return (patient_id, 1-indexed ehr_lines) from patient dict or raw EHR text."""
    if isinstance(patient, str):
        lines = [{"line": idx, "text": txt} for idx, txt in enumerate(patient.splitlines(), start=1)]
        m_id = re.search(r"PATIENT\s+IDENTIFIER:\s*([A-Z0-9-]+)", patient, re.IGNORECASE)
        pid = m_id.group(1) if m_id else "CUSTOM-EHR"
        return pid, lines

    pid = str(patient.get("patient_id") or "UNKNOWN")
    if patient.get("ehr_lines"):
        lines = [{"line": int(item["line"]), "text": str(item["text"])} for item in patient["ehr_lines"]]
        return pid, lines

    raw = str(patient.get("ehr_text") or "")
    lines = [{"line": idx, "text": txt} for idx, txt in enumerate(raw.splitlines(), start=1)]
    return pid, lines


def _cite(doc_id: str, line_num: int, text: str) -> LineCitation:
    quote = text.strip() if text.strip() else text
    return LineCitation(
        doc_type="EHR",
        doc_id=doc_id,
        line_start=line_num,
        line_end=line_num,
        verbatim_quote=quote,
        verified=False,
    )


def _parse_number(s: str) -> float:
    return float(s.replace(",", "").strip())


def _parse_steroid_dose(line_text: str) -> Optional[float]:
    """Parse total daily mg dose of corticosteroid from EHR line text."""
    m_explicit = re.search(
        r"(?:daily_dose_mg\s*=|total\s+daily\s+dose\s*=)\s*(\d+(?:\.\d+)?)\s*(?:mg(?:/day)?)?",
        line_text,
        re.IGNORECASE,
    )
    if m_explicit:
        return float(m_explicit.group(1))

    m_sched = re.search(
        r"(\d+(?:\.\d+)?)\s*mg\s*(?:PO|IV|oral)?\s*(BID|TID|QID|daily|QD|/day)?",
        line_text,
        re.IGNORECASE,
    )
    if not m_sched:
        return None
    dose = float(m_sched.group(1))
    freq = (m_sched.group(2) or "daily").upper()
    if freq == "BID":
        return round(dose * 2.0, 4)
    if freq == "TID":
        return round(dose * 3.0, 4)
    if freq == "QID":
        return round(dose * 4.0, 4)
    return round(dose, 4)


def _extract_biomarker_status(val_str: str) -> Any:
    upper = val_str.upper()
    if "PENDING_LAB_RESULT" in upper:
        return "PENDING_LAB_RESULT"
    if "NEGATIVE" in upper or "WILD-TYPE" in upper or "NOT AMPLIFIED" in upper or "IHC 0" in upper:
        # Distinguish e.g. "NEGATIVE (KRAS G12D detected)"
        return "NEGATIVE"
    if "POSITIVE" in upper or "DETECTED" in upper:
        return "POSITIVE"
    return val_str.strip()


def _parse_ehr_deterministic(
    doc_id: str,
    ehr_lines: list[dict[str, Any]],
) -> PatientPhenotype:
    """Deterministically extract PatientPhenotype with exact LineCitations from ehr_lines."""
    age: Optional[int] = None
    sex: Optional[str] = None
    diagnosis: Optional[str] = None
    stage: Optional[str] = None
    ecog: Optional[int] = None
    measurable_recist: Optional[bool] = None
    prior_metastatic_lines: int = 0
    prior_lines_detail: list[dict[str, Any]] = []
    able_to_swallow_oral: bool = True
    accessible_biopsy_lesion: Optional[Any] = None
    autoimmune_active: bool = False
    prior_grade3_irae: bool = False
    prior_malignancy_2yr: bool = False
    radiation_complication: bool = False
    live_vaccine_date: Optional[str] = None
    major_surgery_date: Optional[str] = None
    histology_group: Optional[str] = None

    biomarkers: dict[str, Any] = {
        "kras_g12c": None,
        "pd_l1_tps": None,
        "egfr_mut": None,
        "alk_fusion": None,
        "trk_fusion": None,
        "msi_high": None,
        "tmb_mut_mb": None,
        "tnbc_confirmed": None,
        "er": None,
        "pr": None,
        "her2": None,
        "braf": None,
        "pending_panels": [],
    }
    labs: dict[str, Any] = {
        "egfr_ml_min": None,
        "ast_u_l": None,
        "alt_u_l": None,
        "bilirubin_mg_dl": None,
        "anc_u_l": None,
        "platelets_u_l": None,
    }
    medications: list[MedicationEntry] = []
    radiation_history: list[RadiationEntry] = []
    cns_status: dict[str, Any] = {
        "has_lesions": False,
        "count": 0,
        "max_size_cm": None,
        "brainstem": False,
        "treated": False,
        "peritumoral_edema": False,
        "symptomatic": False,
        "needs_immediate_local_therapy": False,
        "srs_date": None,
    }
    citations: list[LineCitation] = []

    current_section = ""

    def add_citation(line_num: int, text: str) -> LineCitation:
        c = _cite(doc_id, line_num, text)
        citations.append(c)
        return c

    for entry in ehr_lines:
        lnum = int(entry["line"])
        text = str(entry["text"])
        stripped = text.strip()
        if not stripped:
            continue

        # Never treat summary assessor notes or inline potency annotations as primary EHR facts
        if re.match(r"^(?:Assessor Note:|\[Potency Calculation:)", stripped, re.IGNORECASE):
            continue

        m_sec = re.match(r"^===\s*(.+?)\s*===$", stripped)
        if m_sec:
            current_section = m_sec.group(1).upper()
            continue

        # Demographics / Header
        m_age_sex = re.search(r"(?:DOB/AGE|AGE/SEX):\s*(\d+)yo\s*(Female|Male|F|M)", stripped, re.IGNORECASE)
        if m_age_sex:
            age = int(m_age_sex.group(1))
            s_raw = m_age_sex.group(2).upper()
            sex = "F" if s_raw.startswith("F") else "M"
            add_citation(lnum, stripped)
        elif age is None:
            m_yo = re.search(r"\b(\d{2})-year-old\s+(female|male)\b", stripped, re.IGNORECASE)
            if m_yo:
                age = int(m_yo.group(1))
                sex = "F" if m_yo.group(2).lower().startswith("f") else "M"
                add_citation(lnum, stripped)

        # Diagnosis & Stage
        m_dx_stage = re.match(r"^Diagnosis:\s*(.+?)\s*\|\s*Stage:\s*(.+)$", stripped, re.IGNORECASE)
        if m_dx_stage:
            diagnosis = m_dx_stage.group(1).strip()
            stage = m_dx_stage.group(2).strip()
            add_citation(lnum, stripped)
        elif re.match(r"^Primary Diagnosis:\s*(.+)", stripped, re.IGNORECASE):
            m_pdx = re.match(r"^Primary Diagnosis:\s*(.+)", stripped, re.IGNORECASE)
            if m_pdx:
                dx_full = m_pdx.group(1).strip()
                diagnosis = dx_full
                m_st = re.search(r"(Stage\s+[IV]+[ABC]?(?:\s*\([^)]+\))?)", dx_full, re.IGNORECASE)
                if m_st:
                    stage = m_st.group(1)
                add_citation(lnum, stripped)

        if diagnosis and not histology_group:
            if re.search(r"Triple-Negative Breast Cancer|TNBC", diagnosis, re.IGNORECASE):
                histology_group = "TNBC"
            elif re.search(r"NSCLC|Non-Small Cell Lung Cancer", diagnosis, re.IGNORECASE):
                histology_group = "NSCLC"
            elif re.search(r"Melanoma", diagnosis, re.IGNORECASE):
                histology_group = "Melanoma"

        # Post-op surgery in Diagnosis line (e.g., PT-104)
        if re.search(r"lobectomy|resection|surgery", stripped, re.IGNORECASE) and not re.search(r"No major surgery", stripped, re.IGNORECASE):
            m_op_dt = re.search(r"(?:on|performed)\s+(\d{4}-\d{2}-\d{2})", stripped, re.IGNORECASE)
            if m_op_dt and not major_surgery_date:
                major_surgery_date = m_op_dt.group(1)
                add_citation(lnum, stripped)

        # Prior lines mentioned in Diagnosis line (e.g., PT-103)
        m_dx_prior = re.search(
            r"progressive after (\d+) prior lines? of systemic.*?(?:completed|last dose)\s+(\d{4}-\d{2}-\d{2})",
            stripped,
            re.IGNORECASE,
        )
        if m_dx_prior:
            cnt = int(m_dx_prior.group(1))
            dt = m_dx_prior.group(2)
            if not any(p.get("last_dose_date") == dt for p in prior_lines_detail):
                prior_metastatic_lines = max(prior_metastatic_lines, cnt)
                prior_lines_detail.append({"setting": "metastatic", "regimen": "Prior chemotherapy", "last_dose_date": dt})
                add_citation(lnum, stripped)

        # Measurable RECIST 1.1
        m_recist_bool = re.search(r"Measurable Disease \(RECIST 1\.1\):\s*(True|False)", stripped, re.IGNORECASE)
        if m_recist_bool:
            measurable_recist = m_recist_bool.group(1).lower() == "true"
            add_citation(lnum, stripped)
        elif re.search(r"Target Disease Burden \(RECIST 1\.1\):\s*Measurable", stripped, re.IGNORECASE):
            measurable_recist = True
            add_citation(lnum, stripped)

        # Accessible biopsy & oral swallowing
        m_biopsy = re.search(r"Accessible Biopsy Lesion:\s*(True|False|PENDING_CLINICAL_EVAL)", stripped, re.IGNORECASE)
        if m_biopsy:
            bval = m_biopsy.group(1)
            if bval.upper() == "PENDING_CLINICAL_EVAL":
                accessible_biopsy_lesion = "PENDING_CLINICAL_EVAL"
                if "BIOPSY_ACCESS" not in biomarkers["pending_panels"]:
                    biomarkers["pending_panels"].append("BIOPSY_ACCESS")
            else:
                accessible_biopsy_lesion = bval.lower() == "true"
            add_citation(lnum, stripped)
        elif re.search(r"Biopsy Accessibility:\s*Accessible", stripped, re.IGNORECASE):
            accessible_biopsy_lesion = True
            add_citation(lnum, stripped)

        if re.search(r"UNABLE to swallow oral", stripped, re.IGNORECASE):
            able_to_swallow_oral = False
            add_citation(lnum, stripped)
        elif re.search(r"Able to swallow.*oral", stripped, re.IGNORECASE):
            able_to_swallow_oral = True
            add_citation(lnum, stripped)

        # Autoimmune / irAE / prior malignancy negatives vs positives
        if re.search(r"Prior Grade >=?\s*3|prior.*Grade 3.*(?:irAE|immune-mediated)", stripped, re.IGNORECASE):
            if not re.search(r"\bno\s+prior\b", stripped, re.IGNORECASE):
                prior_grade3_irae = True
                add_citation(lnum, stripped)
        if re.search(r"Autoimmune History:\s*Active|Active.*autoimmune", stripped, re.IGNORECASE):
            if not re.search(r"\bno\s+active\s+autoimmune\b", stripped, re.IGNORECASE):
                autoimmune_active = True
                add_citation(lnum, stripped)
        if re.search(r"other\s+(?:active\s+)?malignancy.*2\s*years", stripped, re.IGNORECASE):
            if not re.search(r"\bno\s+prior\s+history\b|\bno\s+other\b", stripped, re.IGNORECASE):
                prior_malignancy_2yr = True
                add_citation(lnum, stripped)

        # Pathology & Biomarkers
        if "PATHOLOGY" in current_section or (
            not re.search(r"mL/min|Renal\s+Function", stripped, re.IGNORECASE)
            and re.search(r"\b(KRAS|PD-L1|PD_L1|EGFR|ALK|TRK|NTRK|HER2|Estrogen Receptor|Progesterone Receptor)\b", stripped)
        ):
            if re.search(r"KRAS", stripped, re.IGNORECASE):
                if "PENDING_LAB_RESULT" in stripped.upper():
                    biomarkers["kras_g12c"] = "PENDING_LAB_RESULT"
                    if "KRAS_G12C" not in biomarkers["pending_panels"]:
                        biomarkers["pending_panels"].append("KRAS_G12C")
                elif re.search(r"NEGATIVE|G12D|G12V|G12A|WILD-TYPE", stripped, re.IGNORECASE):
                    biomarkers["kras_g12c"] = "NEGATIVE"
                elif re.search(r"G12C.*(?:DETECTED|POSITIVE)|KRAS_G12C:\s*POSITIVE", stripped, re.IGNORECASE):
                    biomarkers["kras_g12c"] = "POSITIVE"
                add_citation(lnum, stripped)

            if re.search(r"PD-L1|PD_L1", stripped, re.IGNORECASE):
                if "PENDING_LAB_RESULT" in stripped.upper():
                    biomarkers["pd_l1_tps"] = "PENDING_LAB_RESULT"
                    if "PD_L1" not in biomarkers["pending_panels"]:
                        biomarkers["pending_panels"].append("PD_L1")
                else:
                    m_tps = re.search(r"(?:PD_L1_TPS_PCT:|TPS\s*=)\s*(\d+(?:\.\d+)?)", stripped, re.IGNORECASE)
                    if m_tps:
                        val = float(m_tps.group(1))
                        biomarkers["pd_l1_tps"] = int(val) if val.is_integer() else val
                add_citation(lnum, stripped)

            if re.search(r"\bEGFR\b", stripped) and not re.search(r"mL/min|Renal", stripped, re.IGNORECASE):
                if "PENDING_LAB_RESULT" in stripped.upper():
                    biomarkers["egfr_mut"] = "PENDING_LAB_RESULT"
                    if "EGFR" not in biomarkers["pending_panels"]:
                        biomarkers["pending_panels"].append("EGFR")
                else:
                    biomarkers["egfr_mut"] = _extract_biomarker_status(stripped)
                add_citation(lnum, stripped)

            if re.search(r"\bALK\b", stripped, re.IGNORECASE):
                if "PENDING_LAB_RESULT" in stripped.upper():
                    biomarkers["alk_fusion"] = "PENDING_LAB_RESULT"
                    if "ALK" not in biomarkers["pending_panels"]:
                        biomarkers["pending_panels"].append("ALK")
                else:
                    biomarkers["alk_fusion"] = _extract_biomarker_status(stripped)
                add_citation(lnum, stripped)

            if re.search(r"\bTRK\b|\bNTRK\b", stripped, re.IGNORECASE):
                if "PENDING_LAB_RESULT" in stripped.upper():
                    biomarkers["trk_fusion"] = "PENDING_LAB_RESULT"
                    if "TRK" not in biomarkers["pending_panels"]:
                        biomarkers["pending_panels"].append("TRK")
                else:
                    biomarkers["trk_fusion"] = _extract_biomarker_status(stripped)
                add_citation(lnum, stripped)

            if re.search(r"^\-\s*ER:|Estrogen Receptor \(ER\):", stripped, re.IGNORECASE):
                biomarkers["er"] = _extract_biomarker_status(stripped)
                if biomarkers["er"] == "PENDING_LAB_RESULT" and "ER" not in biomarkers["pending_panels"]:
                    biomarkers["pending_panels"].append("ER")
                add_citation(lnum, stripped)

            if re.search(r"^\-\s*PR:|Progesterone Receptor \(PR\):", stripped, re.IGNORECASE):
                biomarkers["pr"] = _extract_biomarker_status(stripped)
                if biomarkers["pr"] == "PENDING_LAB_RESULT" and "PR" not in biomarkers["pending_panels"]:
                    biomarkers["pending_panels"].append("PR")
                add_citation(lnum, stripped)

            if re.search(r"^\-\s*HER2:", stripped, re.IGNORECASE):
                biomarkers["her2"] = _extract_biomarker_status(stripped)
                if biomarkers["her2"] == "PENDING_LAB_RESULT" and "HER2" not in biomarkers["pending_panels"]:
                    biomarkers["pending_panels"].append("HER2")
                add_citation(lnum, stripped)

            if re.search(r"^\-\s*BRAF:", stripped, re.IGNORECASE):
                biomarkers["braf"] = _extract_biomarker_status(stripped)
                if biomarkers["braf"] == "PENDING_LAB_RESULT" and "BRAF" not in biomarkers["pending_panels"]:
                    biomarkers["pending_panels"].append("BRAF")
                add_citation(lnum, stripped)

        # CNS / Brain MRI
        if "BRAIN MRI" in current_section or re.search(r"Brain MRI", stripped, re.IGNORECASE):
            if re.search(r"No intracranial metastasis|No evidence of brain metastases|Normal brain parenchyma", stripped, re.IGNORECASE):
                cns_status["has_lesions"] = False
                cns_status["count"] = 0
            elif re.search(r"parenchymal|metastasis|lesion", stripped, re.IGNORECASE):
                cns_status["has_lesions"] = True
                m_sz = re.search(r"(\d+(?:\.\d+)?)\s*cm", stripped, re.IGNORECASE)
                if m_sz:
                    cns_status["max_size_cm"] = float(m_sz.group(1))
                cns_status["brainstem"] = bool(
                    re.search(r"brainstem\s*=\s*YES|brainstem\s+lesion", stripped, re.IGNORECASE)
                    and not re.search(r"(?:zero|no)\s+brainstem", stripped, re.IGNORECASE)
                )
                if re.search(r"treated\s*=\s*YES|Stereotactic Radiosurgery|SRS|Post-SRS", stripped, re.IGNORECASE):
                    cns_status["treated"] = True
                    m_srs = re.search(r"SRS\s*(\d{4}-\d{2}-\d{2})|^(\d{4}-\d{2}-\d{2})\s+Stereotactic", stripped, re.IGNORECASE)
                    if m_srs:
                        cns_status["srs_date"] = m_srs.group(1) or m_srs.group(2)
                elif re.search(r"treated\s*=\s*NO", stripped, re.IGNORECASE):
                    cns_status["treated"] = False
                if re.search(r"peritumoral_edema\s*=\s*YES|peritumoral edema|vasogenic.*edema", stripped, re.IGNORECASE) and not re.search(r"resolution of perilesional edema|minimal vasogenic edema", stripped, re.IGNORECASE):
                    cns_status["peritumoral_edema"] = True
                if re.search(r"clumsiness|headache|symptomatic", stripped, re.IGNORECASE) and not re.search(r"asymptomatic", stripped, re.IGNORECASE):
                    cns_status["symptomatic"] = True
                    cns_status["needs_immediate_local_therapy"] = True
            add_citation(lnum, stripped)

        # Radiation History
        if "RADIATION" in current_section or re.search(r"\b\d+(?:\.\d+)?\s*Gy\b", stripped, re.IGNORECASE):
            if not re.search(r":\s*None\b", stripped, re.IGNORECASE):
                m_rt_gy = re.search(r"(\d+(?:\.\d+)?)\s*Gy", stripped, re.IGNORECASE)
                if m_rt_gy:
                    gy = float(m_rt_gy.group(1))
                    # Look for completion date (prefer 'completed YYYY-MM-DD' or leading date)
                    m_comp = re.search(r"completed\s+(\d{4}-\d{2}-\d{2})", stripped, re.IGNORECASE)
                    m_lead = re.search(r"(\d{4}-\d{2}-\d{2})", stripped)
                    end_dt = m_comp.group(1) if m_comp else (m_lead.group(1) if m_lead else "")
                    is_thoracic = bool(re.search(r"thoracic|lung|mediastin|chest wall", stripped, re.IGNORECASE))
                    if re.search(r"radiation\s+pneumonitis|radiation\s+esophagitis|dysphagia", stripped, re.IGNORECASE):
                        radiation_complication = True
                    # Avoid double counting same SRS event if mentioned in both Brain MRI & Radiation section
                    if end_dt and not any(r.end_date == end_dt and r.dose_gy == gy for r in radiation_history):
                        site_desc = stripped
                        m_site = re.search(r"(?:to|delivered to)\s+([^—(;]+)", stripped, re.IGNORECASE)
                        if m_site:
                            site_desc = m_site.group(1).strip()
                        elif is_thoracic:
                            site_desc = "Thoracic / Lung"
                        elif re.search(r"brain|cranial|parietal|frontal", stripped, re.IGNORECASE):
                            site_desc = "Brain (Cranial SRS)"
                        radiation_history.append(
                            RadiationEntry(
                                site=site_desc,
                                dose_gy=gy,
                                end_date=end_dt,
                                is_thoracic_lung=is_thoracic,
                                citation=add_citation(lnum, stripped),
                            )
                        )

        # Medications, Corticosteroids, Prior Systemic Lines, Vaccines, Surgeries
        matched_steroid = None
        for st_name in STEROID_NAMES:
            if re.search(rf"\b{st_name}\b(?!\s*(?:_|eq\b|equivalent\b))", stripped, re.IGNORECASE):
                matched_steroid = st_name
                break

        if matched_steroid and not re.search(r"Systemic Corticosteroids:\s*None", stripped, re.IGNORECASE):
            is_discontinued = bool(re.search(r"discontinued|taper completed|tapered off|status\s*=\s*discontinued|stopped", stripped, re.IGNORECASE))
            ongoing = not is_discontinued
            dose_mg = 0.0 if is_discontinued else _parse_steroid_dose(stripped)
            m_start = re.search(r"started\s+(?:[\d.]+\s*mg.*?on\s+)?(\d{4}-\d{2}-\d{2})", stripped, re.IGNORECASE)
            m_last = re.search(r"(?:discontinued(?:\s+permanently)?(?:\s+on)?|last_dose_date\s*=|as of)\s*(\d{4}-\d{2}-\d{2})", stripped, re.IGNORECASE)
            medications.append(
                MedicationEntry(
                    name=matched_steroid,
                    drug_class="systemic_corticosteroid",
                    daily_dose_mg=dose_mg,
                    raw_dose_text=stripped,
                    start_date=m_start.group(1) if m_start else None,
                    last_dose_date=m_last.group(1) if m_last else None,
                    ongoing=ongoing,
                    citation=add_citation(lnum, stripped),
                )
            )

        # Prior systemic anticancer / investigational therapies
        if re.search(r"Prior Systemic Therapy|Prior Systemic Anticancer Therapy", stripped, re.IGNORECASE):
            if not re.search(r":\s*None\b", stripped, re.IGNORECASE):
                m_dt = re.search(r"(?:last dose(?:\s+administered\s+on)?|completed)\s*(\d{4}-\d{2}-\d{2})", stripped, re.IGNORECASE)
                if m_dt:
                    dt = m_dt.group(1)
                    is_met = bool(re.search(r"\(metastatic\)|metastatic setting|for metastatic", stripped, re.IGNORECASE))
                    if not any(p.get("last_dose_date") == dt for p in prior_lines_detail):
                        prior_lines_detail.append(
                            {
                                "setting": "metastatic" if is_met else "systemic",
                                "regimen": stripped.lstrip("- ").split("—")[0].strip(),
                                "last_dose_date": dt,
                            }
                        )
                        if is_met:
                            prior_metastatic_lines += 1
                    medications.append(
                        MedicationEntry(
                            name=stripped.lstrip("- ").split("—")[0].strip()[:80],
                            drug_class="investigational_anticancer" if "investigational" in stripped.lower() else "systemic_anticancer",
                            daily_dose_mg=None,
                            raw_dose_text=stripped,
                            last_dose_date=dt,
                            ongoing=False,
                            citation=add_citation(lnum, stripped),
                        )
                    )

        # Live vaccine & Major surgery in Medication section
        m_vax = re.search(r"live[- ]attenuated vaccine administered\s+(\d{4}-\d{2}-\d{2})", stripped, re.IGNORECASE)
        if m_vax:
            live_vaccine_date = m_vax.group(1)
            add_citation(lnum, stripped)
        m_surg = re.search(r"Major surgery performed\s+(\d{4}-\d{2}-\d{2})", stripped, re.IGNORECASE)
        if m_surg:
            major_surgery_date = m_surg.group(1)
            add_citation(lnum, stripped)

        # Labs
        m_egfr = re.search(r"\beGFR(?:\s*\(CKD-EPI\))?:?\s*(\d+(?:\.\d+)?)\s*mL/min", stripped, re.IGNORECASE)
        if m_egfr:
            labs["egfr_ml_min"] = _parse_number(m_egfr.group(1))
            add_citation(lnum, stripped)
        m_ast = re.search(r"\bAST:?\s*(\d+(?:\.\d+)?)\s*U/L", stripped, re.IGNORECASE)
        if m_ast:
            labs["ast_u_l"] = _parse_number(m_ast.group(1))
            add_citation(lnum, stripped)
        m_alt = re.search(r"\bALT:?\s*(\d+(?:\.\d+)?)\s*U/L", stripped, re.IGNORECASE)
        if m_alt:
            labs["alt_u_l"] = _parse_number(m_alt.group(1))
            add_citation(lnum, stripped)
        m_bili = re.search(r"Total Bilirubin:?\s*(\d+(?:\.\d+)?)\s*mg/dL", stripped, re.IGNORECASE)
        if m_bili:
            labs["bilirubin_mg_dl"] = _parse_number(m_bili.group(1))
            add_citation(lnum, stripped)
        m_anc = re.search(r"(?:Absolute Neutrophil Count\s*\(ANC\)|ANC):?\s*([\d,]+)\s*/uL", stripped, re.IGNORECASE)
        if m_anc:
            labs["anc_u_l"] = int(_parse_number(m_anc.group(1)))
            add_citation(lnum, stripped)
        m_plt = re.search(r"Platelets:?\s*([\d,]+)\s*/uL", stripped, re.IGNORECASE)
        if m_plt:
            labs["platelets_u_l"] = int(_parse_number(m_plt.group(1)))
            add_citation(lnum, stripped)

        # ECOG
        m_ecog = re.search(r"ECOG\s+Performance\s+Status:\s*(\d)", stripped, re.IGNORECASE)
        if m_ecog:
            ecog = int(m_ecog.group(1))
            add_citation(lnum, stripped)

    # Derive TNBC confirmation when ER/PR/HER2 are populated
    if biomarkers["er"] or biomarkers["pr"] or biomarkers["her2"]:
        if "PENDING_LAB_RESULT" in (biomarkers["er"], biomarkers["pr"], biomarkers["her2"]):
            biomarkers["tnbc_confirmed"] = "PENDING_LAB_RESULT"
        elif biomarkers["er"] == "NEGATIVE" and biomarkers["pr"] == "NEGATIVE" and biomarkers["her2"] == "NEGATIVE":
            biomarkers["tnbc_confirmed"] = True
        elif any(v == "POSITIVE" for v in (biomarkers["er"], biomarkers["pr"], biomarkers["her2"])):
            biomarkers["tnbc_confirmed"] = False

    # Deduplicate extraction citations by (line_start, verbatim_quote)
    dedup_citations: list[LineCitation] = []
    seen_c: set[tuple[int, str]] = set()
    for c in citations:
        k = (c.line_start, c.verbatim_quote)
        if k not in seen_c:
            seen_c.add(k)
            dedup_citations.append(c)

    return PatientPhenotype(
        age=age,
        sex=sex,
        diagnosis=diagnosis,
        stage=stage,
        ecog=ecog,
        measurable_recist=measurable_recist,
        prior_metastatic_lines=prior_metastatic_lines,
        biomarkers=biomarkers,
        labs=labs,
        medications=medications,
        radiation_history=radiation_history,
        cns_status=cns_status,
        autoimmune_active=autoimmune_active,
        prior_grade3_irae=prior_grade3_irae,
        live_vaccine_date=live_vaccine_date,
        major_surgery_date=major_surgery_date,
        extraction_citations=dedup_citations,
        able_to_swallow_oral=able_to_swallow_oral,
        accessible_biopsy_lesion=accessible_biopsy_lesion,
        prior_malignancy_2yr=prior_malignancy_2yr,
        radiation_complication=radiation_complication,
        histology_group=histology_group,
        prior_lines_detail=prior_lines_detail,
    )


def _enrich_phenotype_with_gemini(
    doc_id: str,
    ehr_lines: list[dict[str, Any]],
    phenotype: PatientPhenotype,
) -> tuple[PatientPhenotype, bool, str, dict[str, int]]:
    """Optionally enrich extracted PatientPhenotype with Gemini 4 when API key or Vertex project is configured."""
    from src.llm_client import DEFAULT_PHENOTYPER_MODEL, generate_gemini_json, is_gemini_configured

    if not is_gemini_configured():
        return phenotype, False, "deterministic-ehr-parser", {}

    try:
        numbered = "\n".join(f"{item['line']}: {item['text']}" for item in ehr_lines if item["text"].strip())
        prompt = (
            "You are a clinical EHR phenotyping agent. Extract and verify key fields from this line-numbered EHR record "
            "as a JSON object with keys: ecog (int or null), age (int or null), sex (string or null), diagnosis (string or null), "
            "line_start (int), verbatim_quote (EXACT substring from that line in the EHR).\n\n"
            f"{numbered[:12000]}"
        )
        parsed, model_used, usage = generate_gemini_json(
            prompt=prompt,
            primary_model=DEFAULT_PHENOTYPER_MODEL,
            fallback_models=("gemini-4-neon", "gemini-4-hydrogen"),
            timeout_ms=25000,
        )
        if isinstance(parsed, dict):
            line_map = {int(item["line"]): str(item["text"]) for item in ehr_lines}
            lnum = parsed.get("line_start")
            quote = str(parsed.get("verbatim_quote", "")).strip()
            if isinstance(lnum, int) and lnum in line_map and quote and quote in line_map[lnum]:
                existing_quotes = {c.verbatim_quote for c in phenotype.extraction_citations}
                if quote not in existing_quotes:
                    phenotype.extraction_citations.append(_cite(doc_id, lnum, quote))
            if phenotype.ecog is None and isinstance(parsed.get("ecog"), int):
                phenotype.ecog = parsed["ecog"]
            if phenotype.age is None and isinstance(parsed.get("age"), int):
                phenotype.age = parsed["age"]
        return phenotype, True, model_used, usage
    except Exception:
        return phenotype, False, "deterministic-ehr-parser", {}


def extract_patient_phenotype(
    patient: Union[dict[str, Any], str],
    use_llm: bool = False,
) -> tuple[PatientPhenotype, list[dict[str, Any]], dict[str, Any]]:
    """Extract PatientPhenotype grounded in EHR line citations.

    Returns (phenotype, ehr_lines, metadata).
    """
    doc_id, ehr_lines = ensure_ehr_lines(patient)
    phenotype = _parse_ehr_deterministic(doc_id, ehr_lines)
    llm_used = False
    model_used = "deterministic-ehr-parser"
    usage: dict[str, int] = {}

    if use_llm:
        phenotype, llm_used, model_used, usage = _enrich_phenotype_with_gemini(doc_id, ehr_lines, phenotype)

    meta = {
        "agent": "@phenotyper",
        "model": model_used if llm_used else "deterministic-ehr-parser",
        "llm_used": llm_used,
        "token_usage": usage,
        "citation_count": len(phenotype.extraction_citations),
    }
    return phenotype, ehr_lines, meta

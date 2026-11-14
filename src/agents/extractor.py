"""@extractor agent: compiles structured CriterionRule items with verbatim protocol line citations."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from src.schemas import CriterionRule, LineCitation


def ensure_protocol_lines(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    """Return 1-indexed protocol lines from protocol dict, synthesizing from text if absent."""
    lines = protocol.get("protocol_lines")
    if lines:
        return [{"line": int(item["line"]), "text": str(item["text"])} for item in lines]

    raw_text = (
        protocol.get("eligibility_criteria_text")
        or protocol.get("eligibility_module", {}).get("eligibilityCriteria")
        or protocol.get("protocolSection", {}).get("eligibilityModule", {}).get("eligibilityCriteria")
        or ""
    )
    return [{"line": idx, "text": txt} for idx, txt in enumerate(raw_text.splitlines(), start=1)]


def _make_citation(
    nct_id: str,
    line_num: int,
    quote: str,
) -> LineCitation:
    return LineCitation(
        doc_type="PROTOCOL",
        doc_id=nct_id,
        line_start=line_num,
        line_end=line_num,
        verbatim_quote=quote,
        verified=False,
    )


def _line_matches_phase(line_text: str, target_phase: Optional[str]) -> bool:
    """Filter out explicitly different single-phase lines when target_phase is fixed."""
    if not target_phase:
        return True
    norm_phase = target_phase.upper()
    stripped = line_text.strip()
    if norm_phase == "PHASE3":
        if re.match(r"^[\*\-\d\.\s]*Phase\s*2\s*:", stripped, re.IGNORECASE) and not re.search(
            r"Phase\s*3", stripped, re.IGNORECASE
        ):
            return False
    elif norm_phase == "PHASE2":
        if re.match(r"^[\*\-\d\.\s]*Phase\s*3\s*:", stripped, re.IGNORECASE) and not re.search(
            r"Phase\s*2", stripped, re.IGNORECASE
        ):
            return False
    return True


def _extract_rules_deterministic(
    nct_id: str,
    protocol_lines: list[dict[str, Any]],
    target_phase: Optional[str] = None,
) -> list[CriterionRule]:
    """Deterministically compile verbatim line-cited CriterionRule items from ClinicalTrials.gov lines."""
    rules: list[CriterionRule] = []
    seen_rule_types: set[tuple[str, int]] = set()
    section: str = "INCLUSION"
    rule_idx = 1

    def add_rule(
        category: str,
        title: str,
        rule_type: str,
        operator: str,
        threshold_value: Any,
        unit: Optional[str],
        line_num: int,
        quote: str,
    ) -> None:
        nonlocal rule_idx
        key = (rule_type, line_num)
        if key in seen_rule_types:
            return
        seen_rule_types.add(key)
        rules.append(
            CriterionRule(
                rule_id=f"{nct_id}-R{rule_idx:02d}",
                category=category,  # type: ignore[arg-type]
                title=title,
                rule_type=rule_type,
                operator=operator,
                threshold_value=threshold_value,
                unit=unit,
                citation=_make_citation(nct_id, line_num, quote.strip() if quote.strip() else quote),
            )
        )
        rule_idx += 1

    for entry in protocol_lines:
        line_num = int(entry["line"])
        text = str(entry["text"])
        stripped = text.strip()
        if not stripped:
            continue

        if re.match(r"^inclusion\s+criteria\b", stripped, re.IGNORECASE):
            section = "INCLUSION"
            continue
        if re.match(r"^exclusion\s+criteria\b", stripped, re.IGNORECASE):
            section = "EXCLUSION"
            continue

        if not _line_matches_phase(text, target_phase):
            continue

        # 1. Age >= 18
        m_age = re.search(r"(?:aged?|age)\s*(?:\\?>=|≥|>=|at least)\s*(\d+)\s*years?", stripped, re.IGNORECASE)
        if m_age and section == "INCLUSION":
            add_rule(
                "INCLUSION",
                f"Minimum Age >= {m_age.group(1)} years",
                "age",
                ">=",
                int(m_age.group(1)),
                "years",
                line_num,
                stripped,
            )

        # 2. ECOG 0 or 1
        if re.search(r"ECOG.*?(?:0\s*(?:or|to|-)\s*1|[\\≤<=]+\s*1)", stripped, re.IGNORECASE):
            add_rule(
                "INCLUSION",
                "ECOG Performance Status 0 or 1",
                "ecog",
                "<=",
                1,
                "score",
                line_num,
                stripped,
            )

        # 3. Histology / Diagnosis
        if section == "INCLUSION" and re.search(r"advanced/metastatic solid tumor|solid tumors are allowed", stripped, re.IGNORECASE):
            add_rule(
                "INCLUSION",
                "Eligible advanced/metastatic solid tumor (NSCLC, TNBC, Melanoma, etc.)",
                "histology_solid_tumor",
                "IN",
                ["NSCLC", "TNBC", "Melanoma", "RCC", "SCCHN", "Solid Tumor"],
                None,
                line_num,
                stripped,
            )
        elif section == "INCLUSION" and re.search(r"\bNSCLC\b|Non-Small[- ]Cell Lung Cancer", stripped, re.IGNORECASE):
            if not re.search(r"Part\s+[AB]|Clinical Stage|Pathologic Stage", stripped, re.IGNORECASE):
                add_rule(
                    "INCLUSION",
                    "Histologically confirmed NSCLC",
                    "histology_nsclc",
                    "CONTAINS",
                    "NSCLC",
                    None,
                    line_num,
                    stripped,
                )

        if section == "INCLUSION" and re.search(r"TNBC is diagnosed|estrogen receptor.*progesterone receptor.*HER2", stripped, re.IGNORECASE):
            add_rule(
                "INCLUSION",
                "TNBC receptor profile (ER-, PR-, HER2-)",
                "tnbc_receptors",
                "ALL_NEGATIVE",
                ["ER", "PR", "HER2"],
                None,
                line_num,
                stripped,
            )

        # 3b. CNS Inclusion (stable / not needing immediate local therapy)
        if section == "INCLUSION" and re.search(r"CNS\s+Inclusion", stripped, re.IGNORECASE):
            add_rule(
                "INCLUSION",
                "CNS status: no brain metastases or stable metastases not needing immediate local therapy",
                "cns_inclusion",
                "CNS_STABLE",
                True,
                None,
                line_num,
                stripped,
            )

        # 4. KRAS G12C mutation (inclusion only)
        if section == "INCLUSION" and re.search(r"KRAS\s*G12C", stripped, re.IGNORECASE):
            add_rule(
                "INCLUSION",
                "KRAS G12C mutation required",
                "kras_g12c",
                "==",
                "POSITIVE",
                None,
                line_num,
                stripped,
            )

        # 5. PD-L1 TPS threshold or known PD-L1
        m_pdl1 = re.search(r"PD-L1\s*TPS\s*(?:\\?>=|≥|>=)\s*(\d+)\s*%", stripped, re.IGNORECASE)
        if section == "INCLUSION" and m_pdl1:
            add_rule(
                "INCLUSION",
                f"PD-L1 TPS >= {m_pdl1.group(1)}%",
                "pd_l1_tps",
                ">=",
                int(m_pdl1.group(1)),
                "%",
                line_num,
                stripped,
            )
        elif section == "INCLUSION" and re.search(r"known\s+(?:programmed\s+death-ligand\s+1\s*\(PD-L1\)|PD-L1)\s+expression", stripped, re.IGNORECASE):
            add_rule(
                "INCLUSION",
                "Known PD-L1 expression status required",
                "pd_l1_known",
                "IS_KNOWN",
                True,
                None,
                line_num,
                stripped,
            )

        # 6. Actionable driver exclusions (EGFR, ALK, TRK)
        if re.search(r"no\s+EGFR,\s*TRK\s+receptor,\s*or\s*ALK", stripped, re.IGNORECASE):
            add_rule(
                "EXCLUSION",
                "NSCLC excludes actionable EGFR, TRK, or ALK alterations",
                "driver_exclusion",
                "NOT_IN",
                ["EGFR", "ALK", "TRK"],
                None,
                line_num,
                stripped,
            )
        elif section == "EXCLUSION" and re.search(r"EGFR\s+or\s+ALK", stripped, re.IGNORECASE):
            add_rule(
                "EXCLUSION",
                "Excludes actionable EGFR or ALK gene alterations",
                "driver_exclusion",
                "NOT_IN",
                ["EGFR", "ALK"],
                None,
                line_num,
                stripped,
            )

        # 7. RECIST 1.1 measurable disease
        if section == "INCLUSION" and re.search(r"measurable\s+(?:disease|lesion).*?RECIST", stripped, re.IGNORECASE):
            add_rule(
                "INCLUSION",
                "Measurable disease per RECIST 1.1",
                "measurable_recist",
                "==",
                True,
                None,
                line_num,
                stripped,
            )

        # 8. Mandatory accessible biopsy lesion
        if section == "INCLUSION" and re.search(r"accessible\s+tumor\s+for\s+biopsy", stripped, re.IGNORECASE):
            add_rule(
                "INCLUSION",
                "Accessible tumor lesion for mandatory biopsy",
                "accessible_biopsy",
                "==",
                True,
                None,
                line_num,
                stripped,
            )

        # 9. Oral swallowing capability
        if section == "INCLUSION" and re.search(r"swallow\s+oral\s+medication", stripped, re.IGNORECASE):
            add_rule(
                "INCLUSION",
                "Able to swallow intact oral medication",
                "oral_swallow",
                "==",
                True,
                None,
                line_num,
                stripped,
            )

        # 10. Prior metastatic systemic treatment exclusion (0 prior metastatic lines)
        if section == "EXCLUSION" and re.search(
            r"Prior\s+systemic\s+treatment\s+for\s+locally\s+advanced\s+or\s+metastatic",
            stripped,
            re.IGNORECASE,
        ):
            add_rule(
                "EXCLUSION",
                "No prior systemic treatment for locally advanced/metastatic disease",
                "prior_metastatic_lines",
                "==",
                0,
                "lines",
                line_num,
                stripped,
            )

        # 11. Systemic anticancer / investigational therapy washout
        m_wash = re.search(
            r"(?:systemic\s+anticancer\s+therapy|investigational\s+agent).*?within\s+(\d+)\s*(weeks?|days?)",
            stripped,
            re.IGNORECASE,
        )
        if section == "EXCLUSION" and m_wash:
            val = int(m_wash.group(1))
            days = val * 7 if m_wash.group(2).lower().startswith("week") else val
            add_rule(
                "EXCLUSION",
                f"Systemic anticancer / investigational agent washout >= {days} days",
                "systemic_washout_days",
                ">=",
                days,
                "days",
                line_num,
                stripped,
            )

        # 12. Systemic corticosteroid ceiling (> 10 mg prednisone or prednisolone eq)
        m_steroid = re.search(
            r"(?:\\?>|>)\s*(\d+(?:\.\d+)?)\s*mg(?:/day)?\s*(?:of\s+)?(?:prednisone|prednisolone)",
            stripped,
            re.IGNORECASE,
        )
        if section == "EXCLUSION" and m_steroid:
            ceiling = float(m_steroid.group(1))
            add_rule(
                "EXCLUSION",
                f"Systemic corticosteroid dose ceiling <= {ceiling:g} mg/day Prednisone eq",
                "steroid_ceiling_mg",
                "<=",
                ceiling,
                "mg/day prednisone eq",
                line_num,
                stripped,
            )
        elif section == "EXCLUSION" and re.search(
            r"Ongoing\s+immunosuppressive\s+therapy,\s+including\s+systemic\s+or\s+enteric\s+corticosteroids",
            stripped,
            re.IGNORECASE,
        ):
            add_rule(
                "EXCLUSION",
                "No ongoing immunosuppressive systemic corticosteroids (>10 mg/day Prednisone eq)",
                "steroid_ceiling_mg",
                "<=",
                10.0,
                "mg/day prednisone eq",
                line_num,
                stripped,
            )

        # 13. Treated brain metastasis steroid washout (14 days)
        m_cns_steroid = re.search(
            r"without\s+requirement\s+of\s+steroid\s+treatment\s+for\s+at\s+least\s+(\d+)\s*days",
            stripped,
            re.IGNORECASE,
        )
        if section == "EXCLUSION" and m_cns_steroid:
            days = int(m_cns_steroid.group(1))
            add_rule(
                "EXCLUSION",
                f"Treated brain metastasis off steroids >= {days} days",
                "cns_steroid_washout_days",
                ">=",
                days,
                "days",
                line_num,
                stripped,
            )

        # 14. CNS lesion exclusions (>2.0 cm, brainstem, active CNS)
        m_cns_cm = re.search(r"untreated\s+brain\s+lesions\s*(?:\\?>|>)\s*(\d+(?:\.\d+)?)\s*cm", stripped, re.IGNORECASE)
        if section == "EXCLUSION" and m_cns_cm:
            add_rule(
                "EXCLUSION",
                f"No untreated brain lesions > {m_cns_cm.group(1)} cm",
                "cns_untreated_max_cm",
                "<=",
                float(m_cns_cm.group(1)),
                "cm",
                line_num,
                stripped,
            )
        if section == "EXCLUSION" and re.search(r"brainstem\s+lesions", stripped, re.IGNORECASE):
            add_rule(
                "EXCLUSION",
                "No brainstem lesions",
                "cns_brainstem_excl",
                "==",
                False,
                None,
                line_num,
                stripped,
            )
        if section == "EXCLUSION" and re.search(r"known\s+active\s+CNS\s+metastases|active\s+brain\s+metastases", stripped, re.IGNORECASE):
            add_rule(
                "EXCLUSION",
                "No active untreated CNS / brain metastases",
                "cns_active_excl",
                "==",
                False,
                None,
                line_num,
                stripped,
            )

        # 15. Live vaccine washout (30 days)
        m_vax = re.search(r"live\s+vaccine\s+within\s+(\d+)\s*(days?|weeks?)", stripped, re.IGNORECASE)
        if section == "EXCLUSION" and m_vax:
            val = int(m_vax.group(1))
            days = val * 7 if m_vax.group(2).lower().startswith("week") else val
            add_rule(
                "EXCLUSION",
                f"Live vaccine washout >= {days} days",
                "live_vaccine_washout_days",
                ">=",
                days,
                "days",
                line_num,
                stripped,
            )

        # 16. Major surgery washout (4 weeks / 28 days)
        m_surg = re.search(r"Major\s+surgery\s+within\s+(\d+)\s*(weeks?|days?)", stripped, re.IGNORECASE)
        if section == "EXCLUSION" and m_surg:
            val = int(m_surg.group(1))
            days = val * 7 if m_surg.group(2).lower().startswith("week") else val
            add_rule(
                "EXCLUSION",
                f"Major surgery washout >= {days} days",
                "major_surgery_washout_days",
                ">=",
                days,
                "days",
                line_num,
                stripped,
            )

        # 17. Thoracic / lung radiation > 30 Gy within 6 months (180 days)
        m_lung_rt = re.search(
            r"radiation(?:\s+therapy)?\s+to\s+the\s+lung.*?(?:\\?>|>)\s*(\d+(?:\.\d+)?)\s*Gy.*?within\s+(\d+)\s*(months?|days?)",
            stripped,
            re.IGNORECASE,
        )
        if section == "EXCLUSION" and m_lung_rt:
            gy = float(m_lung_rt.group(1))
            win_val = int(m_lung_rt.group(2))
            win_days = win_val * 30 if m_lung_rt.group(3).lower().startswith("month") else win_val
            add_rule(
                "EXCLUSION",
                f"No lung/thoracic radiation > {gy:g} Gy within {win_days} days",
                "thoracic_rt_window",
                "NO_RT_OVER_GY_IN_WINDOW",
                {"max_gy": gy, "window_days": win_days},
                "Gy / days",
                line_num,
                stripped,
            )

        # 18. Any radiotherapy within 2 weeks (14 days) or radiation pneumonitis
        m_any_rt = re.search(r"Prior\s+radiotherapy\s+within\s+(\d+)\s*(weeks?|days?)", stripped, re.IGNORECASE)
        if section == "EXCLUSION" and m_any_rt:
            val = int(m_any_rt.group(1))
            days = val * 7 if m_any_rt.group(2).lower().startswith("week") else val
            add_rule(
                "EXCLUSION",
                f"Any prior radiotherapy washout >= {days} days",
                "any_rt_washout_days",
                ">=",
                days,
                "days",
                line_num,
                stripped,
            )

        # 19. CTCAE Grade >= 2 labs / adequate laboratory parameters
        if re.search(r"laboratory\s+values.*?(?:≥|\\?>=|>=)\s*Grade\s*2", stripped, re.IGNORECASE):
            add_rule(
                "EXCLUSION",
                "No chemistry or hematology laboratory abnormalities >= CTCAE Grade 2",
                "ctcae_grade2_labs",
                "<",
                2,
                "CTCAE v5.0 Grade",
                line_num,
                stripped,
            )
        elif section == "INCLUSION" and re.search(r"adequate\s+laboratory\s+parameters", stripped, re.IGNORECASE):
            add_rule(
                "INCLUSION",
                "Adequate organ reserve laboratory parameters (CTCAE Grade < 2 floor)",
                "ctcae_grade2_labs",
                "<",
                2,
                "CTCAE v5.0 Grade",
                line_num,
                stripped,
            )

        # 20. Active autoimmune disease
        if section == "EXCLUSION" and re.search(r"active(?:\s+documented)?\s+autoimmune", stripped, re.IGNORECASE):
            add_rule(
                "EXCLUSION",
                "No active autoimmune disease requiring systemic treatment",
                "autoimmune_active",
                "==",
                False,
                None,
                line_num,
                stripped,
            )

        # 21. Prior Grade >= 3 irAE
        if section == "EXCLUSION" and re.search(
            r"(?:Grade\s*3\s*or\s*higher|≥\s*Grade\s*3|\\?>=\s*Grade\s*3).*?(?:irAE|immune-related)",
            stripped,
            re.IGNORECASE,
        ):
            add_rule(
                "EXCLUSION",
                "No prior Grade >= 3 immune-related adverse event (irAE)",
                "prior_grade3_irae",
                "==",
                False,
                None,
                line_num,
                stripped,
            )

        # 22. Other active malignancy within 2 years
        if section == "EXCLUSION" and re.search(r"another\s+(?:type\s+of\s+cancer|malignancy).*?2\s*years", stripped, re.IGNORECASE):
            add_rule(
                "EXCLUSION",
                "No other active malignancy within past 2 years",
                "prior_malignancy_2yr",
                "==",
                False,
                None,
                line_num,
                stripped,
            )

    return rules


def _enrich_with_gemini_flash(
    nct_id: str,
    protocol_lines: list[dict[str, Any]],
    existing_rules: list[CriterionRule],
) -> tuple[list[CriterionRule], bool, dict[str, int]]:
    """Optionally enrich extracted rules with Gemini 2.5 Flash when API key is configured.

    Returns (rules, llm_called, token_usage).
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return existing_rules, False, {}

    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore

        client = genai.Client(api_key=api_key)
        numbered_text = "\n".join(f"{item['line']}: {item['text']}" for item in protocol_lines if item["text"].strip())
        prompt = (
            "You are a clinical trial protocol eligibility extractor.\n"
            f"Trial: {nct_id}\n"
            "Given the line-numbered eligibility criteria below, return a JSON array of any additional structured rules "
            "not already covered. Each object must have: category (INCLUSION|EXCLUSION), title, rule_type, operator, "
            "threshold_value, unit, line_start (int), verbatim_quote (EXACT substring from that line).\n\n"
            f"{numbered_text[:12000]}"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                http_options=types.HttpOptions(timeout=8000),
            ),
        )
        usage = {}
        if getattr(response, "usage_metadata", None):
            usage = {
                "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0) or 0,
                "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0) or 0,
            }
        parsed = json.loads(response.text or "[]")
        if isinstance(parsed, list):
            line_map = {int(item["line"]): str(item["text"]) for item in protocol_lines}
            existing_types = {r.rule_type for r in existing_rules}
            next_idx = len(existing_rules) + 1
            enriched = list(existing_rules)
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                rt = str(item.get("rule_type", "")).strip()
                if not rt or rt in existing_types:
                    continue
                try:
                    lnum = int(item.get("line_start", 0))
                except (TypeError, ValueError):
                    continue
                quote = str(item.get("verbatim_quote", "")).strip()
                if lnum in line_map and quote and quote in line_map[lnum]:
                    cat = item.get("category", "INCLUSION")
                    if cat not in ("INCLUSION", "EXCLUSION"):
                        cat = "INCLUSION"
                    enriched.append(
                        CriterionRule(
                            rule_id=f"{nct_id}-R{next_idx:02d}",
                            category=cat,
                            title=str(item.get("title", rt)),
                            rule_type=rt,
                            operator=str(item.get("operator", "==")),
                            threshold_value=item.get("threshold_value"),
                            unit=item.get("unit"),
                            citation=_make_citation(nct_id, lnum, quote),
                        )
                    )
                    existing_types.add(rt)
                    next_idx += 1
            return enriched, True, usage
        return existing_rules, True, usage
    except Exception:
        return existing_rules, False, {}


def extract_protocol_rules(
    protocol: dict[str, Any],
    target_phase: Optional[str] = None,
    use_llm: bool = False,
) -> tuple[list[CriterionRule], list[dict[str, Any]], dict[str, Any]]:
    """Extract verbatim line-cited CriterionRule items from a ClinicalTrials.gov protocol dict.

    Returns (rules, protocol_lines, metadata).
    """
    nct_id = str(protocol.get("nct_id") or protocol.get("protocolSection", {}).get("identificationModule", {}).get("nctId") or "UNKNOWN")
    protocol_lines = ensure_protocol_lines(protocol)

    if not target_phase:
        phases = protocol.get("phases") or []
        if "PHASE3" in phases:
            target_phase = "PHASE3"

    rules = _extract_rules_deterministic(nct_id, protocol_lines, target_phase=target_phase)
    llm_used = False
    usage: dict[str, int] = {}

    if use_llm:
        rules, llm_used, usage = _enrich_with_gemini_flash(nct_id, protocol_lines, rules)

    meta = {
        "agent": "@extractor",
        "model": "gemini-2.5-flash" if llm_used else "deterministic-rule-compiler",
        "llm_used": llm_used,
        "token_usage": usage,
        "rule_count": len(rules),
    }
    return rules, protocol_lines, meta

# TrialSwarm Data Card (`data/DATA_CARD.md`)

> **Privacy & Provenance Statement:**  
> **100% synthetic EHR patients paired with real public ClinicalTrials.gov APIv2 protocols; zero real patient data / zero PHI.**

---

## 1. Dataset Overview & Reproducibility

| Component | Path | Records | Generator / Source |
|---|---|---|---|
| **Normalized Trial Protocols** | `data/protocols/NCT04613596.json`<br>`data/protocols/NCT04787042.json`<br>`data/protocols/NCT06890598.json` | 3 active trials (95 protocol lines total) | ClinicalTrials.gov APIv2 (`2026-11-14`) |
| **Featured Canonical Patients** | `data/patients/featured_patients.json` | 4 longitudinal records (`PT-101`–`PT-104`) | Curated synthetic clinical oncology vignettes |
| **Synthetic Screening Cohort** | `data/cohort_120.json` | 120 patient-protocol pairs (`COHORT-001`–`COHORT-120`) | `python3 -m src.data.generate_cohort` (`seed = 20261114`) |

- **Deterministic Seed:** `seed = 20261114`
- **Reference Screening Date:** `2026-11-14`
- **Clinical Evidence & Rules Specification:** [`docs/EVIDENCE.md`](../docs/EVIDENCE.md) (`status: signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)`)

---

## 2. Cohort Distributions (`data/cohort_120.json`)

### 2.1 Distribution by Clinical Trial Protocol (40 pairs per trial)
| NCT ID | Sponsor & Trial Name | Phases | Count |
|---|---|---|---|
| `NCT04613596` | Mirati Therapeutics Inc. — KRYSTAL-7 (NSCLC, KRAS G12C) | `PHASE2`, `PHASE3` | 40 |
| `NCT04787042` | Simcha IL-18, Inc. — ST-067 (Advanced Solid Tumors) | `PHASE1`, `PHASE2` | 40 |
| `NCT06890598` | Eli Lilly and Company — SUNRAY-02 (Olomorasib, NSCLC) | `PHASE3` | 40 |
| **Total** | | | **120** |

### 2.2 Distribution by Expected Verdict
| Expected Verdict | Count | Percentage |
|---|---|---|
| `ELIGIBLE` | 30 | 25.0% |
| `CONTRAINDICATED` | 75 | 62.5% |
| `NEEDS_HUMAN_REVIEW` | 15 | 12.5% |
| **Total** | **120** | **100.0%** |

### 2.3 Distribution by Clinical Trap Archetype (10 + 5×6 per trial)
| Archetype | Expected Verdict | Primary Rule Tested | Per Trial | Total |
|---|---|---|---|---|
| `ELIGIBLE` | `ELIGIBLE` | All R1–R5 pass | 10 | 30 |
| `STEROID_EQUIVALENCE_TRAP` | `CONTRAINDICATED` | **R1:** Glucocorticoid potency conversion (`> 10.0 mg/day` Prednisone eq) | 5 | 15 |
| `WASHOUT_WINDOW_TRAP` | `CONTRAINDICATED` | **R2:** Washouts (`< 28d` investigational/surgery, `< 30d` vaccine, prior metastatic lines, Grade >= 3 irAE / active autoimmune) | 5 | 15 |
| `RADIATION_TRAP` | `CONTRAINDICATED` | **R3:** Thoracic/lung RT `> 30 Gy` within `180 days`, recent RT `< 14 days`, or post-RT esophageal dysphagia | 5 | 15 |
| `ORGAN_LAB_CTCAE_TRAP` | `CONTRAINDICATED` | **R4:** CTCAE v5.0 Grade >= 2 organ reserve floors (`eGFR < 50`, `AST/ALT > 100`, `Bilirubin > 1.8`, `ANC < 1500`, `Platelets < 100k`, `ECOG >= 2`) | 5 | 15 |
| `DRIVER_EXCLUSION_TRAP` | `CONTRAINDICATED` | **R5:** Missing required KRAS G12C / PD-L1 >= 50%, or positive EGFR / ALK / HER2 exclusions | 5 | 15 |
| `MISSING_BIOMARKER_REVIEW` | `NEEDS_HUMAN_REVIEW` | **R5:** `PENDING_LAB_RESULT` / `PENDING_CLINICAL_EVAL` safety gate | 5 | 15 |
| **Total** | | | **40** | **120** |

---

## 3. Featured Canonical Cases (`data/patients/featured_patients.json`)

1. **`PT-101` — Elena Rostova (62F, `NCT04613596` Phase 3) -> `ELIGIBLE`**
   - Stage IV non-squamous NSCLC, KRAS G12C+, PD-L1 TPS 65%, EGFR/ALK negative, measurable 3.4 cm RUL mass, ECOG 1, treatment-naive metastatic, treated 1.2 cm left parietal brain met (SRS 2026-09-30, 45d ago), off steroids since 2026-10-15 (30d ago), normal labs (eGFR 78, AST 24, ALT 29, Bilirubin 0.7, ANC 4,200, Platelets 245,000).
2. **`PT-102` — Marcus Vance (68M, `NCT04613596` & `NCT04787042`) -> `CONTRAINDICATED`**
   - Dual R1 + R2 contraindication: Ongoing Dexamethasone 2 mg PO BID (`4 mg/day = 26.7 mg/day` Prednisone eq `> 10.0 mg/day`) started 2026-11-01 for peritumoral edema around a 1.6 cm right frontal brain lesion, AND completed 1 cycle of investigational anti-LAG-3 checkpoint modulator on 2026-10-26 (19d ago `< 28d` washout for `NCT04787042`; violates 0 prior metastatic lines for `NCT04613596`).
3. **`PT-103` — Sofia Morales (57F, `NCT04787042` Phase 1/2) -> `CONTRAINDICATED`**
   - Dual R3 + R4 contraindication: Metastatic TNBC (ER-/PR-/HER2-), measurable 2.8 cm liver lesion, accessible axillary biopsy site, BUT completed `45 Gy` thoracic chest wall/lung RT on 2026-07-27 (110d ago `< 180d` limit) AND 2026-11-12 labs show CTCAE Grade 2 transaminitis (`AST 142 U/L` [3.55x ULN], `ALT 156 U/L` [3.90x ULN]).
4. **`PT-104` — David Chen (64M, `NCT06890598` Phase 3) -> `NEEDS_HUMAN_REVIEW`**
   - Resected Stage IIIA (pT2bN1M0) NSCLC, KRAS G12C detected on ctDNA liquid biopsy, ECOG 0, able to swallow oral medication, normal labs, no autoimmune/irAE history, BUT reflex tissue `EGFR`/`ALK` fusion panel and `PD-L1` IHC are `PENDING_LAB_RESULT`.

---

## 4. Record Schemas

### 4.1 Normalized Protocol JSON (`data/protocols/<NCT_ID>.json`)
- `nct_id`, `brief_title`, `official_title`, `sponsor`, `phases`, `overall_status`, `conditions`, `interventions`, `source_url`
- `eligibility_module`: raw ClinicalTrials.gov `eligibilityModule`
- `eligibility_criteria_text`: raw criteria text string
- `protocol_lines`: 1-indexed array `[{"line": int, "text": str}]` for deterministic R6 citation grounding
- `protocolSection`: complete upstream ClinicalTrials.gov `protocolSection` object

### 4.2 Patient Screening Record (`featured_patients.json` & `cohort_120.json`)
- Identifiers & Metadata: `patient_id`, `name`, `age`, `sex`, `diagnosis`, `stage`, `target_nct`, `target_phase`, `reference_date`
- Ground Truth Labels: `expected_verdict`, `archetype` / `expected_trap_type` (cohort), `clinical_trap_summary` / `clinical_summary`, `earliest_rescreen_date`
- Structured Clinical State (`structured_truth`): `ecog`, `able_to_swallow_oral`, `measurable_disease_recist11`, `accessible_biopsy_lesion`, `biomarkers`, `labs`, `medications`, `radiation_history`, `cns_lesions`, `prior_lines`
- Unstructured EHR & Citation Grounding: `ehr_text` (multi-section oncology clinical note) and `ehr_lines` (1-indexed array `[{"line": int, "text": str}]`)

---

## 5. Evidence & Licensing Attribution

- **ClinicalTrials.gov APIv2 Terms:** See [`.licenses/clinical_trials_database_LICENSE.txt`](../.licenses/clinical_trials_database_LICENSE.txt) (checked 2026-11-14).
- **PubMed / NCBI Disclaimers & Policies:** See [`.licenses/pubmed_database_LICENSE.txt`](../.licenses/pubmed_database_LICENSE.txt) (checked 2026-11-14).
- **Primary Literature Alignment:** Benchmarks informed by TrialGPT (Jin et al., *Nat Commun* 2024, PMID 39557832; Syed et al., *JAMIA* 2026, PMID 41637159), AI vs Manual Prescreening RCT (Unlu et al., *JAMA* 2025, PMID 39960745), LLM Criteria Decomposition (Chen et al., *Stud Health Technol Inform* 2025, PMID 40775946), and Oncology Trial IT Review (von Itzstein et al., *JAMA Oncol* 2021, PMID 34236403).

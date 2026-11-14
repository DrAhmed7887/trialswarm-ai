# Clinical & Scientific Evidence Base (`docs/EVIDENCE.md`)

**Verification Date:** 2026-11-14  
**Clinical Rules Governance:** `status: signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)`  
**Scope:** Peer-reviewed clinical trial screening benchmarks (PubMed/NCBI), active oncology protocols (ClinicalTrials.gov APIv2), and deterministic clinical decision rules (R1–R6).

---

## 1. Peer-Reviewed Literature & Benchmark Evidence (PubMed)

| PMID | First Author & Citation | Journal & Date | DOI / URL | Verified Findings & Relevance |
|---|---|---|---|---|
| **39557832** | Jin Q, Wang Z, Floudas CS, Chen F, Gong C, Bracken-Clarke D, Xue E, Yang Y, Sun J, Lu Z. *Matching patients to clinical trials with large language models.* | *Nature communications*, 2024 Nov 18 | DOI: [`10.1038/s41467-024-53081-z`](https://doi.org/10.1038/s41467-024-53081-z)<br>PubMed: [`https://pubmed.ncbi.nlm.nih.gov/39557832/`](https://pubmed.ncbi.nlm.nih.gov/39557832/) | **TrialGPT Benchmark:** Evaluated on 3 cohorts totaling **183 synthetic patients** with **>75,000 trial annotations**. TrialGPT-Retrieval recalled >90% of relevant trials using <6% of initial collection. TrialGPT-Matching achieved **87.3% criterion-level accuracy** on **1,015 patient-criterion pairs** with faithful explanations. User study demonstrated a **42.6% screening time reduction** in patient recruitment. |
| **41637159** | Syed M, Hamidi M, Bikkanuri M, Dierschke NA, Katragadda HV, Zozus M, Teixeira AL. *Translating evidence into practice: adapting TrialGPT for real-world clinical trial eligibility screening.* | *Journal of the American Medical Informatics Association : JAMIA*, 2026 Apr 01 | DOI: [`10.1093/jamia/ocag006`](https://doi.org/10.1093/jamia/ocag006)<br>PubMed: [`https://pubmed.ncbi.nlm.nih.gov/41637159/`](https://pubmed.ncbi.nlm.nih.gov/41637159/) | **Real-World EHR Benchmark:** Locally deployed adaptation mirroring longitudinal EHR documentation evaluated at UT Health San Antonio. On expert-adjudicated gold corpus (**n=149**): **81.8% sensitivity**, **97.8% specificity**, **75.0% PPV**. In comparative validation against manual screening (**n=55**): **81.8% vs 36.4% manual sensitivity** (more than double the truly eligible patients identified) with equivalent specificity. |
| **39960745** | Unlu O, Varugheese M, Shin J, Subramaniam SM, Stein DWJ, St Laurent JJ, Mailly CJ, McPartlin MJ, Wang F, Oates MF, Cannon CP, Scirica BM, Wagholikar KB, Aronson SJ, Blood AJ. *Manual vs AI-Assisted Prescreening for Trial Eligibility Using Large Language Models-A Randomized Clinical Trial.* | *JAMA*, 2025 Mar 25 | DOI: [`10.1001/jama.2024.28047`](https://doi.org/10.1001/jama.2024.28047)<br>PubMed: [`https://pubmed.ncbi.nlm.nih.gov/39960745/`](https://pubmed.ncbi.nlm.nih.gov/39960745/) | **Randomized Clinical Trial:** Direct RCT evaluating manual prescreening versus AI-assisted prescreening for trial eligibility using large language models. (Abstract field unpopulated in E-utilities XML snapshot; cited for clinical trial prescreening RCT provenance.) |
| **40775946** | Chen H, Qian L, He X, Chen A, Huang Y, Gou Q, Wang Y, Wang Y, Ai X, Zhou Y, Cohen I, Chen Q, Xu H, Bian J. *Clinical Trial Eligibility Criteria Decomposition and Parsing with Large Language Models.* | *Studies in health technology and informatics*, 2025 Aug 07 | DOI: [`10.3233/SHTI250928`](https://doi.org/10.3233/SHTI250928)<br>PubMed: [`https://pubmed.ncbi.nlm.nih.gov/40775946/`](https://pubmed.ncbi.nlm.nih.gov/40775946/) | **Criteria Decomposition:** Introduces a Decomposition and Parsing (DP) workflow systematically decomposing free-text eligibility criteria into atomic "study traits" structured with entities, modifiers, constraints, and negations using Chain-of-Thought LLM prompting, identifying modifier nuance as a persistent failure mode. |
| **34236403** | von Itzstein MS, Hullings M, Mayo H, Beg MS, Williams EL, Gerber DE. *Application of Information Technology to Clinical Trial Evaluation and Enrollment: A Review.* | *JAMA oncology*, 2021 Oct 01 | DOI: [`10.1001/jamaoncol.2021.1165`](https://doi.org/10.1001/jamaoncol.2021.1165)<br>PubMed: [`https://pubmed.ncbi.nlm.nih.gov/34236403/`](https://pubmed.ncbi.nlm.nih.gov/34236403/) | **Oncology Enrollment Complexity:** Reviews AI/NLP information technology platforms for oncology trial matching, highlighting that cancer protocols impose stringent molecular, genomic, washout, and longitudinal constraints often buried in unstructured medical records. |

---

## 2. Active Clinical Trial Protocols (ClinicalTrials.gov APIv2)

All protocol records were retrieved directly from ClinicalTrials.gov APIv2 on `2026-11-14` and line-indexed in `data/protocols/`.

### 2.1 NCT04613596 (KRYSTAL-7)
- **URL:** `https://clinicaltrials.gov/study/NCT04613596`
- **Lead Sponsor:** Mirati Therapeutics Inc.
- **Phases:** `PHASE2`, `PHASE3`
- **Overall Status:** `RECRUITING`
- **Brief Title:** Phase 2 Trial of Adagrasib Monotherapy and in Combination With Pembrolizumab and a Phase 3 Trial of Adagrasib in Combination in Patients With a KRAS G12C Mutation KRYSTAL-7
- **Official Title:** A Phase 2 Trial of Adagrasib Monotherapy and in Combination With Pembrolizumab and a Phase 3 Trial of Adagrasib in Combination With Pembrolizumab Versus Pembrolizumab in Patients With Advanced Non-Small Cell Lung Cancer With KRAS G12C Mutation
- **Conditions:** Advanced Non-Small Cell Lung Cancer, Metastatic Non-Small Cell Lung Cancer
- **Interventions:** Adagrasib, Pembrolizumab
- **Key Protocol Gates (Lines 1–22):**
  - Phase 3 requires histologically confirmed unresectable or metastatic NSCLC with `KRAS G12C` mutation and `PD-L1 TPS >= 50%` (Line 4).
  - Presence of measurable disease per RECIST 1.1 (Line 5).
  - CNS inclusion requires no brain mets, or untreated/treated brain mets not needing immediate local therapy (Lines 6–10).
  - Excludes prior systemic treatment for locally advanced or metastatic NSCLC (Line 14).
  - Phase 3 CNS exclusions: untreated brain lesions > 2.0 cm, any brainstem lesions, ongoing systemic corticosteroids > 10 mg prednisone equivalent/day for brain lesion symptom control (Lines 18–20).
  - Phase 3 excludes lung radiation > 30 Gy within 6 months (180 days) prior to first study dose (Line 22).

### 2.2 NCT04787042 (ST-067)
- **URL:** `https://clinicaltrials.gov/study/NCT04787042`
- **Lead Sponsor:** Simcha IL-18, Inc.
- **Phases:** `PHASE1`, `PHASE2`
- **Overall Status:** `RECRUITING`
- **Brief Title:** Phase 1a and Phase 2 Study for Safety, Preliminary Efficacy, PK and PD of ST-067
- **Official Title:** A First-In-Human Phase 1/2 Open-Label Study of Intravenous ST-067, Subcutaneous ST-067 with or Without Obinutuzumab Pre-Treatment, and ST-067 in Combination with Pembrolizumab in Subjects with Advanced Solid Malignancies
- **Conditions:** Cancer, Solid Tumor, Melanoma, Renal Cell Carcinoma, Triple-negative Breast Cancer, Non Small Cell Lung Cancer, Squamous Cell Carcinoma of the Head and Neck, Carcinoma, MSI-High
- **Interventions:** ST-067, Obinutuzumab 25 MG/1 ML Intravenous Solution [GAZYVA], pembrolizumab
- **Key Protocol Gates (Lines 1–47):**
  - Age >= 18 years, ECOG 0 or 1 (Lines 3, 5).
  - Advanced/metastatic solid tumors; TNBC requires ER-/PR-/HER2 not 3+ or FISH negative; NSCLC combination arm excludes EGFR, TRK, or ALK positive mutations/fusions (Lines 10–12).
  - At least 1 measurable RECIST 1.1 lesion (Line 19) and mandatory accessible tumor for pre-/on-treatment biopsy (Line 20).
  - Excludes symptomatic brain mets requiring > 10 mg/day prednisolone or equivalent (Line 25) and ongoing immunosuppressive therapy including systemic corticosteroids (Line 34).
  - Excludes live vaccine within 30 days (Line 29), major surgery within 4 weeks / 28 days (Line 30), and systemic anticancer/investigational therapy within 4 weeks / 28 days (Line 35).
  - Excludes any chemistry or hematology lab value >= CTCAE Grade 2 (Line 38).
  - Phase 1 combination exclusions: active CNS mets, steroid requirement within 14 days for treated brain mets (Line 41), prior RT within 2 weeks / 14 days (Line 42), and lung RT > 30 Gy within 6 months / 180 days (Line 47).

### 2.3 NCT06890598 (SUNRAY-02)
- **URL:** `https://clinicaltrials.gov/study/NCT06890598`
- **Lead Sponsor:** Eli Lilly and Company
- **Phases:** `PHASE3`
- **Overall Status:** `RECRUITING`
- **Brief Title:** Study of Olomorasib (LY3537982) in Combination With Standard of Care in Participants With Resected or Unresectable KRAS G12C-mutant Non-Small Cell Lung Cancer
- **Official Title:** A Phase 3, Multicenter, Double-Blind, Placebo-controlled Study Assessing the Efficacy and Safety of Olomorasib in Combination With Standard of Care Immunotherapy in Participants With Resected or Unresectable KRAS G12C-Mutant, Non-Small Cell Lung Cancer - SUNRAY-02
- **Conditions:** Carcinoma, Non-Small-Cell Lung
- **Interventions:** Olomorasib, Pembrolizumab, Durvalumab, Placebo
- **Key Protocol Gates (Lines 1–26):**
  - Histological/cytological confirmation of NSCLC: Part A Stage II–IIIB resected (with residual tumor post-chemoimmunotherapy or upfront resection); Part B Stage III unresectable without progression on concurrent chemoradiotherapy (Lines 3–9).
  - Evidence of `KRAS G12C` mutation (Line 10) and **known** `PD-L1` expression (Line 11).
  - ECOG 0 or 1 (Line 12), able to swallow oral medication (Line 13), adequate laboratory parameters (Line 14).
  - Excludes known actionable changes in `EGFR` or `ALK` genes (Line 23).
  - Excludes another malignancy progressing/requiring treatment within 2 years (Line 24), active autoimmune disease requiring systemic treatment within 2 years (Line 25), or Grade >= 3 irAE / unresolved > Grade 1 irAE from prior immunotherapy (Line 26).

---

## 3. Clinical Decision Rules (R1–R6)

> **Governance Metadata:**  
> `status: signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)`  
> All deterministic thresholds below enforce safety floors and explicit evidence grounding before any eligibility verdict is returned.

### Rule R1: Glucocorticoid Potency Equivalence
- **Status:** `signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)`
- **Pharmacologic Conversion Formula:**
  $$\text{Prednisone\_eq\_mg} = \text{Dexamethasone\_mg} \times \frac{5.0}{0.75} = \text{Methylprednisolone\_mg} \times \frac{5.0}{4.0} = \text{Hydrocortisone\_mg} \times \frac{5.0}{20.0}$$
  *(Prednisolone is 1:1 equivalent to Prednisone: factor $5.0/5.0 = 1.0$.)*
- **Conversion Multipliers:**
  - Dexamethasone: $\times 6.6667$ (`5.0 / 0.75`) — e.g., $2\text{ mg BID} = 4\text{ mg/day} \rightarrow 26.7\text{ mg/day}$ Prednisone equivalent.
  - Methylprednisolone: $\times 1.25$ (`5.0 / 4.0`).
  - Hydrocortisone: $\times 0.25$ (`5.0 / 20.0`).
  - Prednisone / Prednisolone: $\times 1.0$.
- **Clinical Safety Gate:**
  - Ongoing total daily systemic corticosteroid dose `> 10.0 mg/day` Prednisone equivalent triggers `CONTRAINDICATED` for CNS/systemic steroid ceilings (NCT04613596 Line 20; NCT04787042 Lines 25, 34, 41; NCT06890598 Line 25 for active autoimmune immunosuppression).
  - For NCT04787042 Phase 1 combination with treated brain metastases, steroids must be discontinued for `>= 14 days` prior to first dose (Line 41).

### Rule R2: Systemic Anticancer, Investigational, Vaccine & Surgical Washout
- **Status:** `signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)`
- **Washout Windows (evaluated relative to `reference_date`):**
  - **Systemic Anticancer / Investigational Agent Washout:** `>= 28 days` (4 weeks) prior to Day 1 (NCT04787042 Exclusion #12, Line 35).
  - **Prior Metastatic Systemic Therapy Exclusion:** `0 prior metastatic lines` permitted for NCT04613596 (Exclusion #1, Line 14: excludes prior chemotherapy, immune checkpoint inhibitor, or KRAS G12C inhibitor for locally advanced or metastatic NSCLC).
  - **Live Vaccine Washout:** `>= 30 days` prior to Day 1 (NCT04787042 Exclusion #6, Line 29).
  - **Major Surgery Washout:** `>= 28 days` (4 weeks) prior to Day 1 (NCT04787042 Exclusion #7, Line 30).
- **Rescreen Computation:**
  - When a temporary washout failure occurs without permanent protocol disqualification, the auditor computes `earliest_rescreen_date = event_date + required_washout_days`.

### Rule R3: Thoracic / Lung Radiation & Recent Radiotherapy Gate
- **Status:** `signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)`
- **Thresholds:**
  - **High-Dose Lung/Thoracic Radiation:** Total dose `> 30 Gy` to the lung/thorax completed within `180 days` (6 months) prior to screening/first dose triggers `CONTRAINDICATED` (NCT04613596 Line 22; NCT04787042 Exclusion #22, Line 47).
  - **Any Prior Radiotherapy Window:** Any prior radiotherapy completed within `14 days` (2 weeks) triggers `CONTRAINDICATED` for NCT04787042 (Exclusion #17, Line 42).

### Rule R4: CTCAE v5.0 Grade >= 2 Organ Reserve Safety Floor
- **Status:** `signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)`
- **Safety Thresholds (based on NCT04787042 Excl #15 & standard CTCAE v5.0 Grade < 2 floors):**
  - **Renal:** `eGFR >= 50 mL/min/1.73m2` (values `< 50` trigger `CONTRAINDICATED`).
  - **Hepatic Transaminases:** `AST <= 100 U/L` ($\le 2.5 \times \text{ULN}$, where ULN $= 40\text{ U/L}$) and `ALT <= 100 U/L` ($\le 2.5 \times \text{ULN}$, where ULN $= 40\text{ U/L}$). Values `> 100 U/L` trigger `CONTRAINDICATED`.
  - **Hepatic Bilirubin:** `Total Bilirubin <= 1.8 mg/dL` ($\le 1.5 \times \text{ULN}$, where ULN $= 1.2\text{ mg/dL}$). Values `> 1.8 mg/dL` trigger `CONTRAINDICATED`.
  - **Hematologic ANC:** `ANC >= 1,500 / uL`. Values `< 1500 / uL` trigger `CONTRAINDICATED`.
  - **Hematologic Platelets:** `Platelets >= 100,000 / uL`. Values `< 100,000 / uL` trigger `CONTRAINDICATED`.
  - **Performance Status:** `ECOG <= 1`. Values `>= 2` trigger `CONTRAINDICATED`.

### Rule R5: Oncogenic Driver & Biomarker Gate
- **Status:** `signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)`
- **Biomarker Logic:**
  - **NCT04613596 (Phase 3):** Requires `KRAS G12C` positive AND `PD-L1 TPS >= 50%`. Non-G12C KRAS or absent KRAS G12C or TPS `< 50%` (in Phase 3) triggers `CONTRAINDICATED`.
  - **NCT04787042 (NSCLC Combination / TNBC):** NSCLC combination excludes actionable `EGFR`, `TRK`, or `ALK` positive mutations/fusions (Line 10). TNBC requires `ER-`, `PR-`, and `HER2` negative (not IHC 3+, FISH negative) (Line 12).
  - **NCT06890598:** Requires `KRAS G12C` positive AND known `PD-L1` expression; excludes actionable `EGFR` or `ALK` gene alterations (Lines 10, 11, 23).
  - **Pending / Incomplete Assay Handling:** Any required molecular/biomarker test or mandatory clinical evaluation recorded as `PENDING_LAB_RESULT` or `PENDING_CLINICAL_EVAL` MUST NOT be assumed passed or failed; it deterministically sets the verdict to `NEEDS_HUMAN_REVIEW`.

### Rule R6: Deterministic Citation Grounding
- **Status:** `signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)`
- **Verification Invariant:**
  - Every criterion citation emitted by an extraction or reasoning agent must reference an explicit source (`protocol_lines` or `ehr_lines`) with `line_start..line_end` and a quoted `verbatim_quote`.
  - The deterministic verifier validates that `verbatim_quote` matches an exact substring of the concatenated source lines `[line_start..line_end]`.
  - Any claim failing exact substring verification is automatically rejected and flagged as `UNVERIFIED_CITATION_BLOCKED`.

# TrialSwarm AI — Claims & Verification Map (`CLAIMS.md`)

> Every headline metric, clinical rule, literature citation, and system capability asserted in TrialSwarm AI documentation or UI maps directly to an executable command, code symbol, or data artifact in this repository.

---

## 1. Cohort Benchmark Claims (`n = 120` Synthetic Oncology Cohort)

| Claim | Measured Value | Scope & Conditions | Primary Source / Verifier |
|---|---|---|---|
| **Cohort Size & Seed** | `120` patient-protocol pairs (`40` per trial; `30` `ELIGIBLE`, `75` `CONTRAINDICATED`, `15` `NEEDS_HUMAN_REVIEW`) | 100% synthetic EHR notes paired with normalized ClinicalTrials.gov v2 protocols; `seed = 20261114`, `reference_date = 2026-11-14` | `data/cohort_120.json`, `src/data/generate_cohort.py`, `data/DATA_CARD.md` |
| **TrialSwarm Overall Accuracy** | `100.0%` (`120/120`, `0` mismatches) | Evaluated in `deterministic_offline` mode (`use_llm=False`) | `eval/results/benchmark_120.json`, `python3 scripts/evaluate_cohort.py --verify` |
| **TrialSwarm Sensitivity / Specificity** | `100.0%` Sensitivity / `100.0%` Specificity | Positive class = `ELIGIBLE`; Negative = `CONTRAINDICATED` or `NEEDS_HUMAN_REVIEW` | `scripts/evaluate_cohort.py` (`_compute_binary_metrics`), `eval/results/benchmark_120.json` |
| **Naive Single-Prompt Baseline** | `47.5%` Accuracy (`57/120`), `100.0%` Sensitivity, `30.0%` Specificity | Direct numeric comparison without steroid potency, washout arithmetic, CTCAE LFT/renal bounds, or pending-lab gating | `src/agents/safety_auditor.py` (`evaluate_naive_single_prompt_baseline`), `eval/results/benchmark_120.json` |
| **Per-Trial Accuracy Breakdown** | `NCT04613596`: TS `100.0%` (`40/40`) vs Naive `47.5%` (`19/40`)<br>`NCT04787042`: TS `100.0%` (`40/40`) vs Naive `42.5%` (`17/40`)<br>`NCT06890598`: TS `100.0%` (`40/40`) vs Naive `52.5%` (`21/40`) | Reproducible locally and in CI | `eval/results/benchmark_120.json` (`per_trial_breakdown`), `.github/workflows/ci.yml` |
| **Per-Archetype Trap Breakdown** | `ELIGIBLE` (`n=30`): TS `30/30` vs Naive `30/30` (`100.0%`)<br>`STEROID_EQUIVALENCE_TRAP` (`n=15`): TS `15/15` vs Naive `9/15` (`60.0%`)<br>`WASHOUT_WINDOW_TRAP` (`n=15`): TS `15/15` vs Naive `5/15` (`33.3%`)<br>`RADIATION_TRAP` (`n=15`): TS `15/15` vs Naive `0/15` (`0.0%`)<br>`ORGAN_LAB_CTCAE_TRAP` (`n=15`): TS `15/15` vs Naive `1/15` (`6.7%`)<br>`DRIVER_EXCLUSION_TRAP` (`n=15`): TS `15/15` vs Naive `12/15` (`80.0%`)<br>`MISSING_BIOMARKER_REVIEW` (`n=15`): TS `15/15` vs Naive `0/15` (`0.0%`) | `benchmark_120.json` aggregates `WASHOUT_WINDOW_TRAP + RADIATION_TRAP` as `washout_and_rt_traps` (`30/30` vs `5/30`); per-archetype counts reproducible directly from `cohort_120.json` | `eval/results/benchmark_120.json`, `scripts/evaluate_cohort.py`, `src/web/static/judge.html` |
| **Citation Verification Rate** | `100.0%` (`unverified_claims_blocked = 0` on clean runs; `>= 1` blocked on adversarial hallucination injection) | Every verdict and safety finding must carry exact substring anchors inside 1-indexed `protocol_lines` / `ehr_lines` | `src/agents/verifier.py` (`verify_single_citation`, `verify_citations_and_verdicts`, `run_adversarial_verification_probe`) |
| **Mean Offline Latency** | `~4.0–4.1 ms/case` (`4.08 ms/case` in committed run; machine-dependent) | Offline deterministic pipeline (`SwarmCoordinator.run_swarm(..., use_llm=False)`) | `eval/results/benchmark_120.json` (`mean_latency_ms`), `scripts/evaluate_cohort.py` |

---

## 2. Clinical Rules & Sign-Off Status (`R1`–`R6`)

> **Clinical Governance Notice:** All deterministic oncology clinical rules (`R1`–`R6`) carry `status: signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)` in `docs/EVIDENCE.md`. TrialSwarm AI is a clinical decision-support prototype and requires explicit human CRC / Principal Investigator attestation (`POST /api/signoff`) before any chart action.

| Rule | Logic Implemented | Canonical Demonstration Case | Code & Evidence Reference |
|---|---|---|---|
| **R1 — Glucocorticoid Potency Equivalence** | Converts systemic steroids to Prednisone equivalents (`STEROID_CONVERSION_FACTORS`, e.g., Dexamethasone `4 mg/day` × `6.667` = `26.67 mg/day > 10.0 mg/day` ceiling) | `PT-102` (Marcus Vance, Dexamethasone 2 mg PO BID) on `NCT04613596` / `NCT04787042` -> `CONTRAINDICATED` | `src/agents/safety_auditor.py` (`compute_prednisone_equivalent_mg`), `docs/EVIDENCE.md` |
| **R2 — Washout & Prior-Line Windows** | Checks elapsed days from `last_dose_date` / `live_vaccine_date` / `major_surgery_date` to `reference_date` (`< 28d` investigational/surgery, `< 30d` live vaccine), prior metastatic lines, active autoimmune / Grade >= 3 irAE | `PT-102` anti-LAG-3 `2026-10-26` (19d ago; earliest clearance `2026-11-23`) | `src/agents/safety_auditor.py` (`audit_patient_safety`), `docs/EVIDENCE.md` |
| **R3 — Thoracic Radiotherapy & Dysphagia** | Flags thoracic/lung RT `> 30 Gy` within `180 days`, recent RT `< 14 days`, or radiation-induced esophageal dysphagia | `PT-103` (Sofia Morales, `45 Gy` chest wall/lung RT `2026-07-27`, 110d ago `< 180d`) on `NCT04787042` -> `CONTRAINDICATED` | `src/agents/safety_auditor.py`, `docs/EVIDENCE.md` |
| **R4 — CTCAE v5.0 Grade >= 2 Organ Reserve** | Enforces organ reserve bounds (`eGFR < 50`, `AST/ALT > 100 U/L`, `Bilirubin > 1.8`, `ANC < 1500`, `Platelets < 100k`, `ECOG >= 2`) | `PT-103` (`AST 142 U/L`, `ALT 156 U/L`) -> `CONTRAINDICATED` | `src/agents/safety_auditor.py`, `docs/EVIDENCE.md` |
| **R5 — Driver Exclusions & Reflex Biomarker Gate** | Excludes EGFR/ALK/HER2 alterations or missing required KRAS G12C / PD-L1 TPS; routes `PENDING_LAB_RESULT` / `PENDING_CLINICAL_EVAL` to `NEEDS_HUMAN_REVIEW` instead of assuming pass | `PT-104` (David Chen, pending tissue `EGFR`/`ALK` and `PD-L1`) on `NCT06890598` -> `NEEDS_HUMAN_REVIEW` | `src/agents/safety_auditor.py`, `docs/EVIDENCE.md` |
| **R6 — Verbatim Citation Grounding Gate** | Verifies substring containment inside referenced line window; marks ungrounded verdicts `UNVERIFIED_CITATION_BLOCKED` and blocks pass | `POST /api/verify-trap` / `python3 -m src.cli verify-trap` injects fabricated `"Patient is taking 0 mg corticosteroids"` at EHR Line 1 | `src/agents/verifier.py`, `docs/EVIDENCE.md` |

---

## 3. External Data & Peer-Reviewed Literature Provenance

### ClinicalTrials.gov APIv2 (`https://clinicaltrials.gov/`)
- `NCT04613596` — Mirati Therapeutics Inc., KRYSTAL-7 (`PHASE2`/`PHASE3`), `data/protocols/NCT04613596.json`
- `NCT04787042` — Simcha IL-18, Inc., ST-067 (`PHASE1`/`PHASE2`), `data/protocols/NCT04787042.json`
- `NCT06890598` — Eli Lilly and Company, Olomorasib / SUNRAY-02 (`PHASE3`), `data/protocols/NCT06890598.json`
- Terms & attribution checked: `.licenses/clinical_trials_database_LICENSE.txt`

### PubMed (`https://pubmed.ncbi.nlm.nih.gov/`)
- `PMID: 39557832` — Jin et al., *Nat Commun* 2024 (TrialGPT; `42.6%` screening time reduction) — https://pubmed.ncbi.nlm.nih.gov/39557832/
- `PMID: 41637159` — Syed et al., *JAMIA* 2026 (EHR phenotype clinical trial screening) — https://pubmed.ncbi.nlm.nih.gov/41637159/
- `PMID: 39960745` — Unlu et al., *JAMA* 2025 (AI vs manual trial prescreening RCT) — https://pubmed.ncbi.nlm.nih.gov/39960745/
- `PMID: 40775946` — Chen et al., *Stud Health Technol Inform* 2025 (LLM criteria decomposition) — https://pubmed.ncbi.nlm.nih.gov/40775946/
- `PMID: 34236403` — von Itzstein et al., *JAMA Oncol* 2021 (Oncology clinical trial IT screening) — https://pubmed.ncbi.nlm.nih.gov/34236403/
- Terms & policies checked: `.licenses/pubmed_database_LICENSE.txt`

---

## 4. Economics & Deployment Claims Boundaries

- **Offline Deterministic Compute (`$0.0000`):** Default mode executes `@coordinator`, `@extractor`, `@phenotyper`, `@safety-auditor`, and `@verifier` locally with zero external API keys (`src/swarm/coordinator.py` `_estimate_llm_cost_usd`).
- **Optional Live Gemini Mode (`~$0.04` / patient estimate):** When `use_llm=True` and `GEMINI_API_KEY` or `GOOGLE_API_KEY` is configured, `@extractor` calls `gemini-2.5-flash` (`src/agents/extractor.py` `_enrich_with_gemini_flash`) and `@phenotyper` calls `gemini-2.5-pro` (`src/agents/phenotyper.py` `_enrich_phenotype_with_gemini_pro`), estimated at `~$0.038`–`$0.04` per dual-agent pass.
- **Screening time:** no manual-cost or time-saved figure is claimed for TrialSwarm AI (not measured). The only time figure cited is from the literature: a `42.6%` screening-time reduction in TrialGPT's user study (Jin et al., *Nat Commun* 2024, `PMID: 39557832`).
- **No Unverified Commercial / PHI Claims:** Repository contains zero real patient data / zero PHI (`data/DATA_CARD.md`) and makes no ungrounded TAM/CAGR/ARR assertions.

---

## 5. Exact Reproduction Commands

```bash
python3 -m pytest -v
python3 scripts/evaluate_cohort.py --verify
python3 -m src.cli swarm --nct NCT04613596 --patient PT-102
python3 -m src.cli verify-trap --nct NCT04613596 --patient PT-102
python3 -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080
```

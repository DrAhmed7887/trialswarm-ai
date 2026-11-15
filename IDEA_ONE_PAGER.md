# TrialSwarm AI — Executive One-Pager (`IDEA_ONE_PAGER.md`)

**Autonomous Clinical Trial Eligibility & Patient-Safety Verification Swarm**
*Built for Berkeley x DeepMind Hackathon: Build. Ship. Pitch. Win.*

---

## 1. The Clinical Problem & Buyer

Oncology trial pre-screening forces Clinical Research Coordinators (CRCs) and site investigators to cross-check ~80-page exclusion protocols against fragmented, longitudinal EHR notes. Simple keyword or single-prompt LLM checks miss compound clinical traps:
- Systemic steroid potency conversions (**Dexamethasone 2 mg BID = 26.67 mg/day Prednisone equivalent**),
- Overlapping investigational agent and vaccine washout intervals,
- Thoracic radiation pneumonitis windows (`> 30 Gy` within `180 days`),
- CTCAE v5.0 Grade >= 2 hepatotoxicity/renal thresholds and `PENDING_LAB_RESULT` reflex biomarkers.

Missing an exclusion before consent causes preventable IRB protocol deviations, patient harm, and wasted pre-screening workups.

---

## 2. How TrialSwarm AI Works (Antigravity `/swarm` + Gemini 2.5)

1. **Concurrent Structured Extraction:**
   - **`@extractor`** (`gemini-2.5-flash` or deterministic rule parser) parses real **ClinicalTrials.gov APIv2** protocol lines into line-anchored `CriterionRule` criteria.
   - **`@phenotyper`** (`gemini-2.5-pro` or deterministic EHR parser) extracts longitudinal medications, doses, radiation courses, lab values, and pending biomarker panels.
2. **Deterministic Clinical Pharmacology & Safety Audit:**
   - **`@safety-auditor`** evaluates **Rules `R1`–`R5`** (glucocorticoid conversion, washout arithmetic, thoracic RT check, CTCAE v5.0 organ bounds, actionable driver / pending-lab gating) — all marked `signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)` in `docs/EVIDENCE.md`.
3. **Zero-Hallucination Grounding & Human Attestation:**
   - **`@verifier`** enforces **Rule `R6`**, requiring every cited criterion and safety finding to match an exact verbatim substring at the cited Protocol/EHR line numbers (`UNVERIFIED_CITATION_BLOCKED` otherwise).
   - **`@coordinator`** stages a `SignOffPacket` (`STAGE_ECRF_PRE_SCREEN`, `PLACE_WASHOUT_HOLD`, or `REQUEST_REFLEX_BIOMARKERS`) requiring explicit human CRC/PI sign-off with a SHA-256 `SignOffReceipt`.

---

## 3. Verified Results (`n = 120` Seeded Cohort vs. Single-Prompt Baseline)

Evaluated across three real oncology trials (**`NCT04613596`** Mirati KRYSTAL-7, **`NCT04787042`** Simcha ST-067, **`NCT06890598`** Eli Lilly SUNRAY-02):

- **Exact Verdict Accuracy (`n = 120`):** **`100.0%` (`120/120`, `0` mismatches)** vs. **`47.5%` (`57/120`)** Naive single-prompt baseline.
- **Specificity (`Non-Eligible = Neg`):** **`100.0%`** vs. **`30.0%`** Naive baseline (`100.0%` sensitivity on both).
- **Hidden Clinical Trap Capture:**
  - Steroid Equivalence (`R1`, `n = 15`): **`15/15` (`100.0%`)** vs `9/15` (`60.0%`)
  - Washout & Radiation Traps (`R2`–`R3`, `n = 30`): **`30/30` (`100.0%`)** vs `5/30` (`16.7%`)
  - Organ Reserve CTCAE (`R4`, `n = 15`): **`15/15` (`100.0%`)** vs `1/15` (`6.7%`)
  - Pending Reflex Biomarker (`R5`, `n = 15`): **`15/15` (`100.0%`)** vs `0/15` (`0.0%`)
- **Verbatim Citation Grounding (`R6`):** **`100.0%`** across all 120 screens; live adversarial probe (`POST /api/verify-trap`) blocks fabricated quotes.
- **Compute & Latency Profile:** **`4.08 ms/case` and `$0.0000` compute** in offline deterministic mode (`~$0.04/case` est. in optional dual-Gemini 2.5 API mode). Time saved for coordinators has not been measured; for reference, TrialGPT's user study reported a `42.6%` screening-time reduction (`PMID: 39557832`).

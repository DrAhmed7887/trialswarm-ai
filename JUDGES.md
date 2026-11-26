# TrialSwarm AI — Judge & Verification Guide (`JUDGES.md`)

**Event:** Berkeley x DeepMind Hackathon: Build. Ship. Pitch. Win. (+ Nov 2026 Gemini 4 Upgrade)
**Track:** Antigravity CLI (`/swarm`) + Google Gemini 4 (`gemini-4-hydrogen` + `gemini-4-argon`) + Deterministic Clinical Verification

---

## 30-Second Judge Walkthrough (Zero Login Required)

- **Live Public URL:** `https://ahmedadel7887--trialswarm-ai-web.us-east.modal.run/` (and Judge Console: `https://ahmedadel7887--trialswarm-ai-web.us-east.modal.run/judge`)

1. **Open the live URL above (or launch locally):**
   ```bash
   python3 -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080
   ```
2. **Open `/` (`src/web/static/index.html`):**
   - Inspect **`PT-102` (Marcus Vance, 68M)** vs `NCT04613596` (pre-loaded on entry).
   - Compare **Naive LLM Baseline (`ELIGIBLE`)** against **TrialSwarm Deterministic Override (`CONTRAINDICATED`)**:
     - **Rule R1 (Glucocorticoid Conversion):** `Dexamethasone 2 mg PO BID` (`4 mg/day × 6.667 = 26.67 mg/day Prednisone eq > 10.0 mg/day` ceiling).
     - **Rule R2 (Washout Window):** Prior anti-LAG-3 on `2026-10-26` (`19 days` elapsed; earliest washout clearance `2026-11-23`; also fails `0` prior metastatic lines on `NCT04613596`).
   - Switch scenarios (`PT-101` Eligible, `PT-103` Thoracic RT + CTCAE Grade 2 LFTs, `PT-104` Pending Reflex Biomarker Gate -> `NEEDS_HUMAN_REVIEW`).
   - Click any verbatim citation pill (`Rule R6`) to highlight and scroll directly to exact line anchors in Protocol vs. EHR panes.
   - Inspect the **Antigravity `/swarm` Board** tab and execute **21 CFR Part 11-style SHA-256 Sign-Off** (`POST /api/signoff`) via the native `<dialog>` workflow.
3. **Open `/judge` (`src/web/static/judge.html`):**
   - Auto-runs `POST /api/verify-trap`, injecting a fabricated quote (`"Patient is taking 0 mg corticosteroids"` at EHR Line 1) and proving Rule `R6` blocks it (`UNVERIFIED_CITATION_BLOCKED`, `unverified_claims_blocked >= 1`).
   - Inspect the `n = 120` per-archetype scorecard (`benchmark_120.json`) and embedded architecture diagram (`/docs/workflow.svg`).

---

## Judging Rubric Mapping to Repository Evidence

| Hackathon Judging Criterion | TrialSwarm Implementation | Exact Verification Path |
|---|---|---|
| **1. Technical Complexity & Antigravity `/swarm` Architecture** | Parallel `@extractor` (`gemini-4-hydrogen` / offline) + `@phenotyper` (`gemini-4-argon` / offline) synchronized by `@coordinator`, audited by `@safety-auditor` (`R1`–`R5`), and gated by `@verifier` (`R6`) with full board transcript `#1`–`#8` | [`src/swarm/coordinator.py`](src/swarm/coordinator.py), [`src/agents/extractor.py`](src/agents/extractor.py), [`src/agents/phenotyper.py`](src/agents/phenotyper.py), [`docs/workflow.svg`](docs/workflow.svg) |
| **2. Real-World Medical Impact & Safety Reliability** | Prevents false-eligible under-triage across glucocorticoid equivalents (`R1`), washout intervals (`R2`), thoracic RT windows (`R3`), CTCAE v5.0 labs (`R4`), and pending reflex biomarkers (`R5`); all rules `status: signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)` | [`src/agents/safety_auditor.py`](src/agents/safety_auditor.py), [`docs/EVIDENCE.md`](docs/EVIDENCE.md), [`CLAIMS.md`](CLAIMS.md) |
| **3. Verifiable Evaluation (`n = 120` vs Baseline)** | TrialSwarm `100.0%` accuracy (`120/120`, `0` mismatches, `100.0%` specificity) vs Naive baseline `47.5%` (`57/120`, `30.0%` specificity) across 3 real ClinicalTrials.gov trials (`NCT04613596`, `NCT04787042`, `NCT06890598`) | `python3 scripts/evaluate_cohort.py --verify`, [`eval/results/benchmark_120.json`](eval/results/benchmark_120.json) |
| **4. Hallucination Defense & Auditability** | Rule `R6` rejects ungrounded quotes (`UNVERIFIED_CITATION_BLOCKED`); every screen requires human CRC/PI attestation with SHA-256 `SignOffReceipt` | [`src/agents/verifier.py`](src/agents/verifier.py), [`src/web/app.py`](src/web/app.py) (`POST /api/verify-trap`, `POST /api/signoff`) |
| **5. Product Polish, Accessibility & CI Reproducibility** | Responsive tables (`@container`, `role="region"`), accessible ARIA tabs (`beforematch`, `border-block-end`), native `<dialog>` modal, `15/15` automated tests + GitHub Actions CI | [`src/web/static/index.html`](src/web/static/index.html), [`src/web/static/judge.html`](src/web/static/judge.html), [`tests/`](tests), [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |

# TrialSwarm AI — Master Execution Plan & Gate Tracker (`PLAN.md`)

**Hackathon:** Berkeley x DeepMind Hackathon — Build. Ship. Pitch. Win.
**Track:** Antigravity CLI (`/swarm`) + Google Gemini (`gemini-2.5-flash` & `gemini-2.5-pro`)
**Deadline:** Nov 14, 11:59 PM PT (`Nov 15, 08:59 AM CET`)

---

## Completed Engineering Phases

### Phase 1: Evidence Base, Real Trial Ingestion & Synthetic Cohort (`@data-evidence`) — `[x] Done`
- Ingested 3 live ClinicalTrials.gov APIv2 oncology trials (`NCT04613596`, `NCT04787042`, `NCT06890598`) into `data/protocols/*.json` (`95` indexed lines).
- Verified 5 PubMed references via E-utilities (`PMID: 39557832`, `41637159`, `39960745`, `40775946`, `34236403`) and authored `docs/EVIDENCE.md` with Rules `R1`–`R6` (`status: signed_off (Dr. Ahmed Zayed, MB BCh, 2026-11-14)`).
- Authored `.licenses/clinical_trials_database_LICENSE.txt` and `.licenses/pubmed_database_LICENSE.txt`.
- Built `data/patients/featured_patients.json` (`PT-101`–`PT-104`) and deterministic generator `src/data/generate_cohort.py` (`seed = 20261114`) producing `data/cohort_120.json` + `data/DATA_CARD.md`.

### Phase 2: Antigravity `/swarm` Engine & Deterministic Verifiers (`@swarm-engine`) — `[x] Done`
- Defined strict Pydantic v2 contracts (`src/schemas.py`).
- Implemented `@extractor` (`src/agents/extractor.py`), `@phenotyper` (`src/agents/phenotyper.py`), `@safety-auditor` (`src/agents/safety_auditor.py`), `@verifier` (`src/agents/verifier.py`), `@coordinator` (`src/swarm/coordinator.py`), and CLI (`src/cli.py`).
- Supports `deterministic_offline` execution (`$0.0000`, zero network/keys) and optional `gemini-2.5-swarm` mode when `GEMINI_API_KEY`/`GOOGLE_API_KEY` is configured.

### Phase 3: Reproducible Benchmark, Tests, Diagram & CI (`@eval-devops`) — `[x] Done`
- Built `scripts/evaluate_cohort.py` and committed `eval/results/benchmark_120.json` (`100.0%` [120/120] vs Naive `47.5%` [57/120], `4.08 ms/case`, `0` mismatches).
- Wrote `15` automated tests in `tests/test_swarm.py` (`8`) and `tests/test_api.py` (`7`).
- Rendered crisp vector flow diagram (`docs/workflow.svg`), `requirements.txt`, `Dockerfile`, and `.github/workflows/ci.yml`.

### Phase 4: Zero-Login FastAPI Web Workstation & Judge Console (`@web-ui`) — `[x] Done`
- Implemented FastAPI app (`src/web/app.py`) serving `/`, `/judge`, `/docs/workflow.svg`, and `/api/{health,cases,screen,verify-trap,signoff}`.
- Built `src/web/static/index.html` and `src/web/static/judge.html` using `modern-web-guidance` patterns (`responsive-table`, native `<dialog>`, accessible ARIA `tabs`), synced to `eval/results/benchmark_120.json`.

### Phase 5: Claims Audit & Documentation Sync — `[x] Done`
- Authored `CLAIMS.md` mapping every metric, rule, PMID, NCT trial, and endpoint to source files and verification commands.
- Synchronized `README.md`, `JUDGES.md`, `PLAN.md`, `GAME_PLAN.md`, and `IDEA_ONE_PAGER.md`.

---

## Remaining Human Decision & Submission Gates

- **Physician Rule Review:** `[x]` Dr. Ahmed Zayed (MB BCh) reviewed and signed off Rules `R1`–`R6` in [`docs/EVIDENCE.md`](docs/EVIDENCE.md) (`signed_off`, 2026-11-14).
- **Gate G4 — Media Capture:** `[x] Done` (Rendered `video/pitch/trialswarm_pitch_60s.mp4` at `58.33s` and `video/demo/trialswarm_product_demo_3min.mp4` at `177.63s` with ElevenLabs VO and synchronized captions).
- **Gate G5 — Optional Deploy & Final Submission:** `[ ]` Confirm before deploying to Google Cloud Run (under GCP trial/Dev credits), making GitHub repository public, and submitting via Luma before `Nov 14, 11:59 PM PT` (`Nov 15, 08:59 AM CET`).

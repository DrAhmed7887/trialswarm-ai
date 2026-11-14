# TrialSwarm AI — Submission Gate Tracker (`GAME_PLAN.md`)

**Deadline:** Nov 14, 11:59 PM PT (`Nov 15, 08:59 AM CET` — Online Track)
**Repository / Build State:** Code, benchmark (`n = 120`), tests (`15/15`), Web UI, CI workflow, and claims audit complete.

---

## Gate Checklist (No Deploy or Public Push Without Explicit Approval)

| Gate | Deliverable | Verification Check | Status |
|---|---|---|---|
| **G0 — Evidence & Trials** | `NCT04613596`, `NCT04787042`, `NCT06890598` + 5 PubMed PMIDs + Rules `R1`–`R6` (`signed_off`, 2026-11-14) | [`docs/EVIDENCE.md`](docs/EVIDENCE.md), [`data/DATA_CARD.md`](data/DATA_CARD.md) | `[x] Done` |
| **G1 — Core `/swarm` Engine** | `@coordinator`, `@extractor`, `@phenotyper`, `@safety-auditor`, `@verifier` + Pydantic contracts + CLI | `python3 -m src.cli swarm --nct NCT04613596 --patient PT-102` | `[x] Done` |
| **G2 — Quantitative Benchmark** | `n = 120` synthetic cohort (`100.0%` vs `47.5%` Naive baseline) + automated test suite + CI | `python3 -m pytest -v && python3 scripts/evaluate_cohort.py --verify` | `[x] Done` |
| **G3 — Web UI & Claims Sync** | FastAPI workstation (`/`) + Judge console (`/judge`) + `CLAIMS.md` + synced root docs | `TestClient` smoke check across all routes; `modern-web-guidance` verified | `[x] Done` |
| **Physician Attestation** | Clinical sign-off on Rules `R1`–`R6` in `docs/EVIDENCE.md` | Explicit approval by Dr. Ahmed Zayed, MB BCh | `[x] Done` |
| **G4 — Demo & Pitch Videos** | 3-minute product demo + 60-second founder pitch (CLI `/swarm` + `/` + `/judge` trap test + `docs/workflow.svg`) | Video recordings verified cleanly under time caps (`58.33s` & `177.63s` in `video/`) | `[x] Done` |
| **G5 — Deploy & Luma Submit** | Optional Cloud Run URL (checked against GCP credits), public repo visibility toggle, and Luma submission receipt | Save Luma confirmation screenshot + SHA/tag after explicit sign-off | `[ ] Pending` |

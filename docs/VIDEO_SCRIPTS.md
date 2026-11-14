# TrialSwarm AI — Ready-to-Record Video Scripts

> **Live Demo URL for Screen Capture:** `https://ahmedadel7887--trialswarm-ai-web.us-east.modal.run/`  
> **Judge Console URL:** `https://ahmedadel7887--trialswarm-ai-web.us-east.modal.run/judge`

---

## 1. 1-Minute Playcast Product Demo (0:00 – 1:00)

| Time | On Screen (Browser Action) | Voiceover |
|---|---|---|
| **0:00 – 0:10** | Open `https://ahmedadel7887--trialswarm-ai-web.us-east.modal.run/` showing `PT-102` (Marcus Vance) vs `NCT04613596` (KRYSTAL-7). | "An oncology Clinical Research Coordinator spends ~4 hours per pre-screen—and one missed steroid conversion or washout window triggers an IRB protocol deviation and patient harm." |
| **0:10 – 0:25** | Point to **Naive LLM (`ELIGIBLE`)** vs **TrialSwarm (`/swarm` `CONTRAINDICATED`)** and the `R1` / `R2` findings. | "Here, a naive single-prompt LLM marks Marcus Vance eligible. TrialSwarm's Antigravity `/swarm` catches two hidden traps: Rule R1 converts Dexamethasone 2 mg BID to 26.67 mg/day Prednisone equivalent—above the 10 mg ceiling—and Rule R2 flags an active 19-day anti-LAG-3 washout with an exact clearance date." |
| **0:25 – 0:38** | Click a verbatim citation pill (`R1` / `R2`) to scroll/highlight the exact Protocol and EHR lines, then click the **`/swarm` Board** tab. | "Every finding is anchored to exact verbatim lines in the ClinicalTrials.gov protocol and EHR, coordinated across `@extractor`, `@phenotyper`, `@safety-auditor`, and `@verifier`." |
| **0:38 – 0:50** | Open `/judge` (`https://ahmedadel7887--trialswarm-ai-web.us-east.modal.run/judge`) showing `POST /api/verify-trap` blocking the fabricated quote (`UNVERIFIED_CITATION_BLOCKED`) and the `n=120` scorecard. | "On `/judge`, we inject a fabricated quote—Rule R6 blocks it automatically (`UNVERIFIED_CITATION_BLOCKED`). Across 120 oncology cases on three real trials, TrialSwarm scores 100% vs 47.5% for the naive baseline." |
| **0:50 – 1:00** | Return to `/`, open the **Sign-Off** `<dialog>`, enter name, and submit `POST /api/signoff` to show the SHA-256 `SignOffReceipt`. | "Finally, no chart action happens without a human CRC/PI SHA-256 sign-off receipt. Try it live—zero login required." |

---

## 2. 2-Minute Venture Pitch & Team Intro (0:00 – 2:00)

- **0:00 – 0:25 (Hook & Buyer Stake):** "I'm Dr. Ahmed Zayed—physician-turned-engineer with 12+ years of clinical practice, now M.Sc. candidate in Applied Health Informatics at RWTH Aachen. In oncology trials, a single pre-screen takes a Clinical Research Coordinator ~4 hours—about \$260 in loaded labor—and missing a hidden steroid potency conversion or radiation washout causes preventable patient harm and costly IRB deviations."
- **0:25 – 0:55 (Why Existing AI Fails):** "Tools like TrialGPT proved LLMs cut screening time by 42.6%, but LLMs alone still fail arithmetic and temporal floors. On our seeded 120-patient oncology benchmark across three real ClinicalTrials.gov protocols—KRYSTAL-7, ST-067, and SUNRAY-02—a single-prompt baseline got only 47.5% accuracy and 30% specificity, passing ineligible patients."
- **0:55 – 1:30 (TrialSwarm Architecture & Edge):** "TrialSwarm AI separates Gemini 2.5 extraction from deterministic clinical safety gates using Antigravity `/swarm`: `@extractor` (`gemini-2.5-flash`) and `@phenotyper` (`gemini-2.5-pro`) parse protocol and EHR lines concurrently; `@safety-auditor` enforces physician-signed Rules R1–R5; `@verifier` enforces Rule R6 verbatim substring grounding; and `@coordinator` stages an eCRF hold or reflex biomarker order for SHA-256 human sign-off. Result: 120/120 exact accuracy, 100% citation verification, at \$0.0000 offline compute or ~\$0.04 per live dual-Gemini pass."
- **1:30 – 2:00 (Pedigree & Ask):** "My prior triage work, SAFE-Triage, hit 35/36 (97.2%) with 0/36 critical under-triage on MIETIC English—the same safety-first engineering now applied to oncology trial enrollment. TrialSwarm is live right now on Modal with zero login required. Thank you."

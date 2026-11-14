# TrialSwarm AI — 3-Minute Product & Swarm Architecture Demo Script (`video/demo/script.md`)

**Total Measured Duration:** 177.63 seconds (2 minutes 57.6 seconds; verified under 180s cap)  
**Voice:** Daniel (`onwK4e9ZLuTAKqWW03F9`), ElevenLabs Broadcaster  
**Audio Files:** `video/demo/assets/audio/vo/*.mp3`  

---

### [00:00.00 – 00:27.63] Scene 1: The Enrollment Crisis & AI Failure Modes (27.63s)
> "Clinical trial eligibility screening is broken. While large language models can parse free text, they fail on strict medical calculations: glucocorticoid potency conversions, relative washout windows, and CTCAE laboratory thresholds. When AI guesses on eligibility, patients face lethal toxicity, and clinical trials suffer devastating protocol violations."

### [00:27.63 – 00:54.84] Scene 2: The Antigravity `/swarm` Architecture (27.21s)
> "TrialSwarm AI solves this through a multi-agent Antigravity swarm coupled with deterministic clinical verifiers. Extractor and Phenotyper parse trial protocols and electronic health records in parallel. Then, Safety-Auditor executes deterministic clinical rules R1 through R5, grounded in active oncology trials from ClinicalTrials.gov and peer-reviewed literature."

### [00:54.84 – 01:21.68] Scene 3: Live Workstation Walkthrough on Marcus Vance (26.84s)
> "Let's examine patient Marcus Vance, screened against the Mirati KRYSTAL-7 protocol. A naive language model sees four milligrams of daily Dexamethasone, compares it to the ten-milligram ceiling, and marks him eligible. But TrialSwarm's Rule R1 converts Dexamethasone to twenty-six point seven milligrams Prednisone equivalent, triggering an immediate Contraindicated verdict."

### [01:21.68 – 01:48.15] Scene 4: Swarm Board Transcript & 28-Day Washout Gate (26.47s)
> "On the Antigravity swarm board, every agent's contribution is transparently logged. The Extractor extracts ten criteria with verbatim line citations. The Phenotyper grounds fourteen clinical facts. And Rule R2 catches another critical trap: a prior anti-LAG-3 checkpoint therapy ending only nineteen days ago, violating the required twenty-eight-day washout."

### [01:48.15 – 02:10.21] Scene 5: Judge Console & Rule R6 Adversarial Probe (22.06s)
> "In the Judge console, we test our system against adversarial hallucination. When an attacker or faulty model injects a fabricated quote claiming zero milligrams of steroids, Rule R6 instantly rejects it. If a claim is not an exact substring of the cited text lines, it is deterministically blocked."

### [02:10.21 – 02:34.27] Scene 6: Oncology Archetype Cohorts & Reflex Biomarker Gating (24.06s)
> "TrialSwarm handles diverse oncology profiles seamlessly. Patient 101 clears all criteria as Eligible. Patient 103 is contraindicated due to thoracic radiation and grade-two liver enzymes. And Patient 104, with a pending EGFR and ALK panel, is safely routed to Needs Human Review rather than assuming a pass."

### [02:34.27 – 02:57.63] Scene 7: Benchmark Evaluation & 21 CFR Part 11 Digital Sign-Off (23.36s)
> "Across our benchmark of one hundred twenty synthetic oncology cases, TrialSwarm achieved one hundred percent accuracy and zero mismatches, compared to forty-seven percent for the naive baseline. Clinical coordinators then execute SHA-256 digital sign-offs, creating a tamper-evident audit trail ready for FDA inspection."

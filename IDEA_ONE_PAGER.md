# IDEA ONE-PAGER: Product, Architecture & Venture Thesis
## Berkeley x DeepMind Hackathon: Build. Ship. Pitch. Win.

### Product Name
**TrialSwarm AI**  
*Autonomous Multi-Agent Clinical Trial Protocol & Patient Safety Audit Engine*

---

### 1. The Problem ($8M/Day Clinical Trial Delay)
86% of global clinical trials fail to meet recruitment timelines, and 19% are cancelled entirely due to protocol enrollment failures. A single day of trial delay costs biopharma sponsors between **$600,000 and $8,000,000** in lost patent exclusivity and operational burn. 

The bottleneck is human cognitive overload: modern Phase II/III oncology and cardiovascular protocols contain over 50 complex inclusion/exclusion criteria, multi-drug washout windows, and biomarker thresholds. Clinical Research Coordinators (CRCs) spend 3 to 4 hours per patient manually cross-referencing messy EHR records against 80-page protocol PDFs, leading to high error rates and critical protocol deviations.

---

### 2. The Solution: Multi-Agent Swarm with Google Gemini
TrialSwarm deconstructs protocol feasibility and patient screening into an autonomous, parallel multi-agent swarm orchestrated via **Antigravity CLI (`/swarm`)** and powered by **Google Gemini 2.5**:

```
                          ┌───────────────────────────┐
                          │  Clinical Protocol (PDF)  │
                          │   + Patient Record (EHR)  │
                          └─────────────┬─────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
             ┌───────────────────────┐     ┌───────────────────────┐
             │   Protocol Extractor  │     │   EHR Phenotyper      │
             │   (Gemini 2.5 Flash)  │     │   (Gemini 2.5 Pro)    │
             └───────────┬───────────┘     └───────────┬───────────┘
                         │                             │
                         └──────────────┬──────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │   Safety & Conflict Auditor │
                         │   (Washouts, Contraind.)    │
                         └──────────────┬──────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │   Swarm Verifier Agent      │
                         │ (Deterministic Rule Engine) │
                         └──────────────┬──────────────┘
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ Instant Audit Verdict (<15s):                       │
             │ [ENROLLABLE / CONTRAINDICATED]                      │
             │ Exact Protocol & EHR Line Citations                 │
             │ Audit-Ready PDF & JSON for IRB/CRO                  │
             └─────────────────────────────────────────────────────┘
```

1. **Protocol Extraction Worker (Gemini 2.5 Flash):** Parses 80-page clinical trial protocols into machine-executable boolean criteria trees (demographics, laboratory cut-offs, prior lines of therapy).
2. **Clinical Phenotyping Worker (Gemini 2.5 Pro):** Scans unstructured clinical consultation notes, lab trends, and histology reports to extract patient phenotype vectors.
3. **Safety & Interaction Auditor (Antigravity Worker):** Performs cross-checks on drug washout periods, organ reserve thresholds (eGFR, LFTs), and active contraindications.
4. **Antigravity Swarm Verifier:** Synthesizes parallel worker outputs, reconciles contradictions, and mandates deterministic line-number citations for every single qualification or rejection claim.

---

### 3. Why Google Gemini & Antigravity CLI?
- **Massive Context Window:** Gemini 2.5 handles full 100+ page clinical trial protocols and multi-year longitudinal medical histories in a single context pass without lossy chunking.
- **Antigravity CLI `/swarm` Orchestration:** Enables distinct parallel worker roles (Extractor, Phenotyper, Safety Auditor) that run concurrently and report back to a verifier agent, reducing audit latency from 4 hours to **under 15 seconds**.
- **Deterministic Hallucination Defense:** If an agent claims a criterion is satisfied, the Verifier requires an exact verbatim quotation and line anchor from the patient record. If ungrounded, the candidate is flagged for human review.

---

### 4. Market Potential & Venture Unit Economics ($500K–$5M Seed Thesis)
- **Target Buyer:** Contract Research Organizations (CROs), Phase II/III Biopharma Sponsors, and Academic Medical Centers.
- **Unit Economics:**
  - Traditional CRC manual review: ~4 hours @ $65/hr = **$260/patient**.
  - TrialSwarm compute cost: ~120K tokens across Gemini 2.5 Flash/Pro = **~$0.04/patient**.
  - SaaS Pricing: $15/screened patient or $50K/trial site license (Gross Margin > 90%).
- **Market Size:** Global Clinical Trial Patient Recruitment & Feasibility market is **$4.2B**, expanding at 13.8% CAGR. Capturing 1% represents a $42M ARR venture opportunity.

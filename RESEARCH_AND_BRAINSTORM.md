# Berkeley x DeepMind Hackathon: Research Dossier & Product Brainstorm

**Document Date:** November 14, 2026  
**Author:** Dr. Ahmed Zayed (MB BCh) & Antigravity Assistant  
**Event:** Berkeley x DeepMind Hackathon: Build. Ship. Pitch. Win.  
**Hosts & Partners:** Google DeepMind, Google Gemini, Antigravity CLI, "Girls into VC" @ UC Berkeley  
**Participant Status:** APPROVED (Ticket `SdfIb2`, Guest: Dr. Ahmed Zayed, `approval_status: approved`)

---

## Part 1: Event Intel & Exhaustive Research Dossier

### 1.1 Event Genesis & Format Update
The event was originally planned as an in-person campus hackathon at UC Berkeley. Due to overwhelming registration demand exceeding physical venue limits, the organizers published an official format update:
- **Format:** Hybrid.
- **In-Person Track:** Local teams built from home in the morning; finalists check in at Helen Diller Anchor House in Berkeley at 2:30 PM PT for live stage pitching (5-min pitch + 5-min Q&A) before a VC panel.
- **Online Track (Remote):** An asynchronous track for remote participants.
  - **Submission Deadline:** **End of day, November 14 PT** (which converts to **Sunday, November 15 at 08:59 AM CET**).
  - **Deliverables:** Identical to the in-person track.
  - **Evaluation:** Asynchronous judging by the full panel + 7-day social engagement tracking on YouTube.
  - **Prizes:** Share of $5,000 in Google Cloud Platform (GCP) credits + private 30-minute 1-on-1 VC pitch meetings with top-tier funds.

### 1.2 Timezone Math (Madrid CET vs San Francisco PT)
* **Local Madrid/CET Time:** Saturday, Nov 14, ~12:15 CET.
* **San Francisco/PT Time:** Saturday, Nov 14, 03:15 AM PT (CET is +9 hours ahead of PT).
* **Online Hard Submission Deadline:** Nov 14, 11:59 PM PT = **Sunday, Nov 15, 08:59 AM CET**.
* **Available Build & Shipping Window:** ~20.5 hours remaining.

---

### 1.3 Key Judges & Stakeholder Personas

Understanding who grades the submission is vital for scoring:

#### A. Google & Google DeepMind Leadership
1. **Shengzhe Yao** — Creator of Antigravity CLI, Google DeepMind.
   - *Strategic Implication:* Shengzhe is the core technical evaluator. Entering the **Antigravity CLI Track** and deeply exercising the newly released `/swarm` (multi-agent) pattern directly appeals to his vision for agentic engineering.
2. **Amit Vadi** — Head of Community, Google DeepMind.
3. **Joana Carrasqueira** — Senior Manager, Google DeepMind.

#### B. Venture Capitalists ($500K – $5M Seed Investors)
- **Eugenia Trakal** (New Enterprise Associates - NEA)
- **Kristopher Kostelecky** (theGP)
- **Nicholas Rabjohn** (Amity Ventures)
- **Fannie Wang** (UpHonest Capital)
- **Matt Caspari** (Alumni Ventures)
- **Parikshit Sharma** (Partner, SOSV / IndieBio — bio & deep tech focus)
- **Vikram Venkat** (Cota Capital)
- **Magne Jul Pedersen** (Exponential VC)
- *VC Lens:* They do not grade on code complexity alone. They look for:
  - Immediate ROI: Who pays? How much money or labor is saved?
  - Unit Economics: Compute cost per run vs. customer willingness to pay.
  - Defensibility / Moat: Why can't a naive wrapper do this?
  - Addressable Market: Path to a venture-scale ($50M+ ARR) company.

#### C. Academic Partners
- **Rolando Perez, PhD** — Senior Scientist, Stanford University.
- **Emile Shah & Lisa Collier** — President & Director, Girls into VC @ UC Berkeley.

---

### 1.4 Mandatory Deliverables & Scoring Rubric

#### Deliverables Checklist:
1. **Track Selection:** Antigravity CLI Track (recommended) or Google AI Studio Track.
2. **Hosted Prototype:** Public, working URL (Google Cloud Run or hosted web app). Must load without environment setup or API key friction.
3. **Public GitHub Repository:** Clean documentation, architecture diagram, green test suite.
4. **Team One-Pager (Plain text):** Background, pedigree, relevant domain expertise.
5. **Idea One-Pager (Plain text):** Problem statement, Gemini/Antigravity architecture, business model.
6. **2-Minute Video:** Founder/team introduction and venture elevator pitch.
7. **1-Minute Video (Playcast):** High-density product demo showing the workflow end-to-end.
8. **Public YouTube Link:** Demo uploaded publicly to track Phase 1 (5 PM PT cutoff) and Phase 2 (7–14 days) social engagement metrics.

#### Official Criteria:
- **Technical Feasibility:** Does it actually run and deliver reproducible outputs?
- **Innovation & Novelty:** Is it a creative leap beyond trivial single-prompt completion?
- **Real-World Applicability:** Would enterprise/clinical users adopt this immediately?
- **Market Potential & Fundability:** Is this fundable with a $500K–$5M seed check?
- **Go-to-Market Traction:** Public engagement on the demo video.

---

## Part 2: Historical Postmortem Intelligence (Why Past 16 Entries Lost)

Based on the 10 Nov 2026 postmortem analysis (`LESSONS.md`, `process_findings.md`, and 40 build session transcripts), the following table maps the historical failure modes to their root causes and mandatory countermeasures:

| Ranked Failure Mode | Evidence from Past Events | Root Cause | Antidote for Berkeley x DeepMind |
|---|---|---|---|
| **1. No Hosted Live Demo (30-Second Rule)** | *Hathor* (localhost only), *HemoGuard* (local proof only), *SceneMedic* (unhosted URL), *Anamnesis* ("no app or server, intake is a library"). | Treating code as complete once terminal scripts pass; deferring UI/hosting to the end. | Deploy a clean web interface on **Google Cloud Run** with 3 pre-staged 1-click test cases so any judge can verify the tool in 10 seconds. |
| **2. Peripheral Sponsor Technology** | *Rapid Agent* (MCP server only saved records), *SceneMedic* (ClickHouse side lookup), *Teach Ahmes* (plain VM instead of microsandbox). | Picking the idea first, then retrofitting the sponsor's tool as a wrapper. | Build natively around **Antigravity CLI `/swarm`** and **Gemini 2.5 Flash/Pro** as the central multi-agent engine. |
| **3. No Stakeholder Stakes on Screen 1** | *Anamnesis* (evaluated on 10 synthetic voices), *Teach Ahmes* (educational robot with no costly stakes). | Building for general interest rather than a specific buyer with high financial/clinical liability. | State the quantified outcome on screen 1: *"Reduces clinical protocol feasibility screening from 4 hours to 12 seconds, saving $260/patient and eliminating trial delay penalties."* |
| **4. Submitting Early with Window Left & Missing Rubric Rows** | *Vultr Agent Rush* (submitted 3 days early with missing CI, unverified weights). | Urge to finish quickly without checking each criterion. | Maintain `JUDGES.md` as a strict pre-flight gate. Do not submit until all 5 rubric areas have verified code assets. |
| **5. Video & Presentation Neglect** | Video recorded in the final 30 minutes; unscripted voiceover; missing receipt. | Treating video as administrative overhead rather than 40% of the judging score. | Allocate dedicated time for a crisp 2-minute venture pitch and a 1-minute Playcast screen capture uploaded to YouTube. |

---

## Part 3: Brainstorming Product Concepts

To maximize win probability, a winning project must hit the sweet spot of:
1. **Dr. Ahmed Zayed's Unfair Advantage:** Physician-engineer, MB BCh, clinical safety, deterministic validation, RWTH Aachen Health Informatics.
2. **Shengzhe Yao & DeepMind Alignment:** Deep, idiomatic use of Antigravity CLI `/swarm` multi-agent orchestration and Gemini 2.5 multimodal/long-context reasoning.
3. **VC Evaluation Panel (NEA, theGP, SOSV/IndieBio):** High-stakes enterprise problem with massive dollar savings, venture-scale unit economics, and defensible moats.
4. **Feasibility in 18 Hours:** Modular build with pre-packaged data, deterministic logic, and rapid web deployment.

Here are 4 structured product options:

---

### Option A: TrialSwarm AI — Autonomous Clinical Trial Protocol Feasibility & Patient Safety Audit Engine

* **The Problem:** 86% of clinical trials fail recruitment deadlines, costing sponsors **$600K to $8M per day of delay**. Clinical Research Coordinators spend 3–4 hours per patient manually cross-referencing messy EHR records against 80-page protocol PDFs containing 50+ complex eligibility criteria, drug washout windows, and lab limits.
* **How Antigravity `/swarm` & Gemini 2.5 Work:**
  - **Protocol Extractor Agent (Gemini 2.5 Flash):** Ingests complex trial protocols and compiles a deterministic boolean rule graph (inclusion, exclusion, biomarker thresholds).
  - **EHR Phenotyper Agent (Gemini 2.5 Pro):** Scans longitudinal patient records, lab histories, and free-text clinical notes.
  - **Safety & Washout Auditor:** Flags drug-drug contraindications, liver/kidney cut-offs, and mandatory washout windows.
  - **Swarm Verifier Agent (Antigravity Coordinator):** Reconciles parallel agent findings, requires exact line-by-line textual citations from the source records, and outputs an audit-ready verdict in **under 15 seconds**.
* **Why It Wins:**
  - *Sponsor Alignment (10/10):* Perfect demonstration of `/swarm` orchestration (parallel domain workers + verifier agent).
  - *VC Appeal (10/10):* Clear B2B SaaS buyer (CROs, biopharma), massive TAM ($4.2B patient recruitment market), compelling unit economics ($0.04 Gemini compute vs. $260 manual labor).
  - *Clinical Moat (10/10):* Grounded in medical realities by a licensed physician.

---

### Option B: AegisCode Swarm — Multi-Agent Autonomous Clinical Coding & Revenue Integrity Auditor

* **The Problem:** US hospitals lose **$125B annually** in denied claims due to incorrect ICD-10-CM / CPT coding and undocumented medical necessity. Medical coders are overwhelmed by 40-page discharge summaries, leading to downcoding (lost revenue) or upcoding (severe regulatory audit penalties from CMS).
* **How Antigravity `/swarm` & Gemini 2.5 Work:**
  - **Clinical Narrative Extractor:** Parses physician notes, surgical summaries, and pathology reports.
  - **ICD-10/CPT Code Specialist Agent:** Proposes candidate billing codes with specificity modifiers.
  - **CMS Medical Necessity & NCCI Auditor:** Checks National Correct Coding Initiative (NCCI) edit rules, mutually exclusive code pairs, and documentation compliance.
  - **Swarm Verifier Agent:** Generates a clean claim packet with highlighted chart provenance, flagging missing clinical documentation before claim submission.
* **Why It Wins:**
  - *VC Appeal (9.5/10):* Massive revenue-cycle management (RCM) market. Immediate ROI ("we recovered $14,200 in undercoded sepsis cases today").
  - *Sponsor Alignment (9/10):* High-throughput document analysis with parallel coding and compliance agents.
  - *Execution Risk:* Slightly heavier on complex medical coding rule tables.

---

### Option C: PharmaShield Swarm — Real-Time Multi-Agent Pharmacovigilance & Adverse Drug Event (ADE) Sentinel

* **The Problem:** Adverse Drug Events account for over **1.3 million emergency visits** and $30B in hospital costs annually in the US. Post-market surveillance relies on voluntary FAERS reports, catching less than 5% of real-world drug toxicities.
* **How Antigravity `/swarm` & Gemini 2.5 Work:**
  - **Signal Detection Agent:** Continuously scans real-world patient records, discharge summaries, and polypharmacy regimens.
  - **Drug-Drug & Metabolic Pathway Agent:** Maps CYP450 interactions, cumulative QT prolongation, and renal clearance limits using Gemini.
  - **Causality Assessment Agent:** Applies the Naranjo Algorithm and WHO-UMC causality scales deterministically.
  - **Swarm Verifier Agent:** Collates confirmed high-confidence ADE signals into automated FDA MedWatch 3500A draft reports.
* **Why It Wins:**
  - *Clinical Rigor (9/10):* Highly relevant to acute medicine and drug safety.
  - *VC Appeal (8.5/10):* Targeted at pharma regulatory affairs and hospital risk management.

---

### Option D: BugSwarm CLI — Autonomous Multi-Agent DevSecOps & CVE Triage Sentinel

* **The Problem:** Developer teams waste **20% of engineering time** reviewing noisy static analysis alerts and triage backlogs, where 70% are false positives or non-exploitable reachability flaws.
* **How Antigravity `/swarm` & Gemini 2.5 Work:**
  - **Static AST Analyzer Agent:** Extracts dependency trees and code call graphs.
  - **CVE Threat Modeler Agent:** Evaluates exploitability and runtime reachability using Gemini code models.
  - **Patch Synthesis Agent:** Generates an automated minimal reproducible patch and regression test.
  - **Swarm Verifier Agent:** Runs the patch in an isolated sandbox, verifies that the regression test passes, and submits a verified PR.
* **Why It Wins:**
  - *Sponsor Alignment (10/10):* Directly targets developer tooling, appealing strongly to Shengzhe Yao and the Antigravity developer base.
  - *VC Appeal (8.5/10):* High developer tool market valuation, though a crowded DevSecOps space.
  - *Founder Fit:* Less differentiated than Dr. Ahmed Zayed's unique clinical-physician pedigree.

---

## Part 4: Comparative Decision Matrix

| Evaluation Criteria | Weight | Option A: TrialSwarm AI | Option B: AegisCode Swarm | Option C: PharmaShield | Option D: BugSwarm CLI |
|---|---|---|---|---|---|
| **Founder Pedigree Fit (Dr. Zayed MB BCh)** | 25% | **10 / 10** | 9 / 10 | 9.5 / 10 | 6 / 10 |
| **Antigravity `/swarm` & DeepMind Synergy** | 25% | **10 / 10** | 9 / 10 | 8.5 / 10 | 10 / 10 |
| **VC Seed Fundability ($500K–$5M Check)** | 20% | **10 / 10** | 9.5 / 10 | 8.5 / 10 | 8.5 / 10 |
| **Instant 30-Second Demo Impact** | 15% | **10 / 10** | 9 / 10 | 8 / 10 | 8.5 / 10 |
| **Feasibility in 18-Hour Window** | 15% | **9.5 / 10** | 8 / 10 | 8.5 / 10 | 9 / 10 |
| **Weighted Total** | **100%** | **9.9 / 10** | **8.9 / 10** | **8.8 / 10** | **8.4 / 10** |

---

## Part 5: Strategic Recommendation

### Selected Path: Option A — TrialSwarm AI 🩺⚡

**Why Option A is the Uncontested Champion:**
1. **Unassailable Founder Advantage:** Dr. Ahmed Zayed's credentials (physician with 12+ years clinical practice, M.Sc. in Health Informatics at RWTH Aachen) provide immediate credibility that pure software engineers cannot fake before the VC panel (especially SOSV / IndieBio and NEA).
2. **Native DeepMind & Antigravity Showcase:**
   - The Antigravity `/swarm` architecture solves the exact bottleneck of clinical trial screening: orchestrating parallel specialized agents (Protocol Parsing, Clinical Phenotyping, Safety Check) under a deterministic Verifier.
   - Leverages Gemini 2.5's massive context window to digest entire 80-page clinical trial protocols without lossy chunking.
3. **The 30-Second Judge Experience:**
   - A judge visits the hosted Cloud Run URL, clicks one of 3 realistic clinical scenarios (e.g., Phase II Non-Small Cell Lung Cancer, Severe Heart Failure, or Psoriatic Arthritis trial), clicks **"Run Swarm Audit"**, and in **12 seconds** watches the swarm evaluate 15 criteria in parallel, highlight exact document citations, and output an IRB-ready qualification report.
4. **Clean Venture Unit Economics:**
   - Manual CRC Review: 4 hours @ $65/hr = **$260/screening**.
   - TrialSwarm Compute Cost: ~120K tokens of Gemini = **$0.04/screening**.
   - Price to CRO: $15/screening = **99.7% gross margin** while saving the sponsor 94% on screening labor.

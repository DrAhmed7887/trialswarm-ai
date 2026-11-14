# JUDGES.md: Pre-Flight Verification & Rubric Mapping
## Berkeley x DeepMind Hackathon: Build. Ship. Pitch. Win.

Every row in this matrix directly counters a verified failure mode documented in `LESSONS.md` and `process_findings.md` across 16 prior entries.

---

## 1. Criterion-to-Code Mapping

| Rubric Criterion | Past Failure Mode in Postmortems | What the Berkeley Judges Demand | Concrete Implementation & Proof | Verification Gate |
|---|---|---|---|---|
| **Technical Feasibility** | Localhost demo only (Hathor, HemoGuard); replay simulation (Anteroom); unhosted CLI (Anamnesis). | Must work in 30 seconds for a stranger without API keys or environment setup. | Public hosted Cloud Run web interface. One-click case runner. Green automated CI tests. | G3 / G4 |
| **Sponsor Tech Depth** | Sponsor SDK relegated to a side lookup or trivial wrapper (Rapid Agent, SceneMedic, Teach Ahmes). | Shengzhe Yao (Antigravity Creator) & DeepMind demand core reliance on Antigravity CLI `/swarm` and Gemini 2.5 Flash/Pro. | Multi-agent swarm orchestration is the core engine: Planner, Domain Specialist, Fact-Checker/Verifier, and Output Synthesizer. | G2 / G3 |
| **Real-World Applicability** | Synthetic benchmarks with no stakeholder stakes (Anamnesis 9/10 on synthetic voices, Teach Ahmes). | A named buyer with high financial/clinical stakes who saves measurable hours or dollars. | Clear clinical/enterprise buyer: "Saves hospital networks $2.4M in missed trial billable revenue" or "Prevents critical diagnostic drop-offs in 45 seconds". | G1 |
| **Market Potential & Fundability** | No venture narrative; framed as non-profit toy or academic exercise. | NEA, theGP, SOSV VCs looking for $500K–$5M seed check scalability. | Clear Unit Economics: Cost per agent swarm run ($0.03 Gemini) vs. Value delivered ($150 clinical review fee). Defensible moat. | G4 |
| **Pitch & Demo Videos** | Video rushed in final 45 minutes; missing receipt; TestFlight link instead of live store link. | Strict split: 2-min pitch (pedigree + fundability) + 1-min crisp product walkthrough (Playcast). | Scripted, recorded via Media Studio, uploaded publicly to YouTube, receipt link verified before deadline. | G5 |

---

## 2. Hard Anti-Patterns (From `LESSONS.md` - Strictly Forbidden)

1. **NO "Code runs only in CLI/terminal":** Must have a modern, high-contrast, responsive web UI hosted on a public domain.
2. **NO login/API key prompt for the judge:** The judge lands on the page and can immediately click a pre-staged sample or live query.
3. **NO generic wrapper:** The application must showcase multi-agent collaboration (Swarm: parallel agent branches + verifier reconciliation).
4. **NO mock data without live option:** Provide 3 instant real-world test cases with immediate deterministic verification.

#!/usr/bin/env python3
"""Render crisp 1080p visual slides for TrialSwarm videos using Chrome headless."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SLIDES = {
    "slide_01_hook.html": """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { margin: 0; background: #0D1117; color: #F4F1EA; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 1080px; width: 1920px; box-sizing: border-box; padding: 80px; }
  .badge { background: rgba(232, 163, 61, 0.15); border: 1px solid #E8A33D; color: #E8A33D; padding: 10px 24px; border-radius: 999px; font-weight: 700; font-size: 24px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 30px; }
  h1 { font-size: 72px; line-height: 1.15; text-align: center; max-width: 1500px; margin: 0 0 40px 0; font-weight: 800; }
  h1 span { color: #E8A33D; }
  .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; width: 100%; max-width: 1500px; margin-top: 20px; }
  .card { background: #161B22; border: 1px solid #30363D; border-radius: 16px; padding: 40px; text-align: left; }
  .card h2 { color: #F85149; font-size: 48px; margin: 0 0 10px 0; }
  .card p { color: #8B949E; font-size: 22px; margin: 0; line-height: 1.4; }
  .source { margin-top: 50px; font-size: 20px; color: #8B949E; }
</style>
</head>
<body>
  <div class="badge">Berkeley x DeepMind Hackathon</div>
  <h1>Clinical Trial Matching Fails on <span>Hidden Pharmacology Traps</span></h1>
  <div class="grid">
    <div class="card">
      <h2>86%</h2>
      <p>Of clinical trials fail to recruit required oncology patient cohorts on schedule.</p>
    </div>
    <div class="card">
      <h2 style="color: #E8A33D;">42.6%</h2>
      <p>Screening time reduction demonstrated by AI assistance (TrialGPT, Nature Comm 2024).</p>
    </div>
    <div class="card">
      <h2>Lethal</h2>
      <p>Risk of AI under-triage when naive LLMs ignore steroid potency, washouts, and CTCAE floors.</p>
    </div>
  </div>
  <div class="source">Evidence: PMID: 39557832 · ClinicalTrials.gov APIv2 · Dr. Ahmed Zayed, MB BCh</div>
</body>
</html>""",

    "slide_02_trap.html": """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { margin: 0; background: #0D1117; color: #F4F1EA; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 1080px; width: 1920px; box-sizing: border-box; padding: 60px 80px; }
  .header { width: 100%; max-width: 1600px; margin-bottom: 40px; }
  .badge { background: rgba(248, 81, 73, 0.15); border: 1px solid #F85149; color: #F85149; padding: 8px 20px; border-radius: 999px; font-weight: 700; font-size: 20px; text-transform: uppercase; letter-spacing: 1.5px; display: inline-block; margin-bottom: 16px; }
  h1 { font-size: 56px; margin: 0; font-weight: 800; }
  .split { display: grid; grid-template-columns: 1fr 1fr; gap: 50px; width: 100%; max-width: 1600px; }
  .box { background: #161B22; border: 2px solid #30363D; border-radius: 20px; padding: 40px; box-sizing: border-box; }
  .box.danger { border-color: #F85149; background: rgba(248, 81, 73, 0.04); }
  .box.success { border-color: #3FB950; background: rgba(63, 185, 80, 0.04); }
  .box-title { font-size: 26px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }
  .pill-red { background: #F85149; color: #fff; padding: 6px 16px; border-radius: 8px; font-size: 20px; font-weight: 800; }
  .pill-green { background: #E8A33D; color: #0D1117; padding: 6px 16px; border-radius: 8px; font-size: 20px; font-weight: 800; }
  .fact { font-size: 22px; color: #C9D1D9; margin: 16px 0; line-height: 1.5; font-family: ui-monospace, monospace; }
  .highlight { background: rgba(232, 163, 61, 0.2); color: #E8A33D; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
  .calc { margin-top: 30px; padding: 20px; background: #0D1117; border-radius: 12px; border: 1px dashed #E8A33D; font-size: 22px; color: #E8A33D; font-family: ui-monospace, monospace; }
</style>
</head>
<body>
  <div class="header">
    <div class="badge">The Glucocorticoid Potency Trap</div>
    <h1>Patient PT-102 (Marcus Vance, 68M) vs NCT04613596</h1>
  </div>
  <div class="split">
    <div class="box danger">
      <div class="box-title">
        <span>Naive Single-Prompt LLM</span>
        <span class="pill-red">FALSE ELIGIBLE</span>
      </div>
      <div class="fact">• EHR Medication: Dexamethasone 2 mg PO BID</div>
      <div class="fact">• Naive Computation: 2 mg × 2 = 4 mg/day</div>
      <div class="fact">• Protocol Ceiling: &le; 10 mg/day Prednisone eq</div>
      <div class="fact" style="color: #F85149;">• Naive Logic: 4 mg &le; 10 mg &rarr; PASS</div>
      <div class="calc" style="border-color: #F85149; color: #F85149;">
        [FATAL UNDER-TRIAGE]<br>
        Tolerates massive steroid immunosuppression into checkpoint trial.
      </div>
    </div>
    <div class="box success">
      <div class="box-title">
        <span>TrialSwarm Deterministic Rule R1</span>
        <span class="pill-green">CONTRAINDICATED</span>
      </div>
      <div class="fact">• Dexamethasone Potency Multiplier: 5.0 / 0.75 = <span class="highlight">6.6667x</span></div>
      <div class="fact">• Total Daily Dose: 4.0 mg/day Dexamethasone</div>
      <div class="fact">• Prednisone Equivalent: 4.0 × 6.6667 = <span class="highlight">26.67 mg/day</span></div>
      <div class="fact" style="color: #3FB950;">• Safety Gate: 26.67 mg > 10.0 mg ceiling &rarr; BLOCKED</div>
      <div class="calc">
        [RULE R1 + RULE R2 SAFETY VERDICT]<br>
        CONTRAINDICATED · Earliest washout hold: 2026-11-23
      </div>
    </div>
  </div>
</body>
</html>""",

    "slide_05_scorecard.html": """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { margin: 0; background: #0D1117; color: #F4F1EA; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 1080px; width: 1920px; box-sizing: border-box; padding: 60px 80px; }
  .badge { background: rgba(63, 185, 80, 0.15); border: 1px solid #3FB950; color: #3FB950; padding: 8px 24px; border-radius: 999px; font-weight: 700; font-size: 22px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 24px; }
  h1 { font-size: 64px; margin: 0 0 40px 0; font-weight: 800; text-align: center; }
  table { width: 100%; max-width: 1600px; border-collapse: collapse; background: #161B22; border-radius: 16px; overflow: hidden; border: 1px solid #30363D; }
  th { background: #21262D; color: #8B949E; padding: 22px 30px; font-size: 22px; text-transform: uppercase; letter-spacing: 1px; text-align: left; }
  td { padding: 22px 30px; font-size: 26px; border-bottom: 1px solid #30363D; color: #C9D1D9; }
  tr:last-child td { border-bottom: none; }
  .ts { color: #3FB950; font-weight: bold; }
  .naive { color: #F85149; }
  .footer { margin-top: 40px; display: flex; justify-content: space-between; width: 100%; max-width: 1600px; color: #8B949E; font-size: 22px; }
  .live-pill { background: #E8A33D; color: #0D1117; font-weight: 800; padding: 8px 20px; border-radius: 8px; font-family: ui-monospace, monospace; }
</style>
</head>
<body>
  <div class="badge">Verified Benchmark Evaluation · n = 120 Synthetic Oncology Cohort</div>
  <h1>TrialSwarm AI vs Naive Single-Prompt Baseline</h1>
  <table>
    <thead>
      <tr>
        <th>Evaluation Metric / Category</th>
        <th>Naive LLM Baseline</th>
        <th>TrialSwarm AI (Offline Swarm)</th>
        <th>Clinical Safety Delta</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Overall Screening Accuracy</td>
        <td class="naive">47.50% (57/120)</td>
        <td class="ts">100.00% (120/120)</td>
        <td>+52.5% accuracy gain</td>
      </tr>
      <tr>
        <td>Specific Eligibility Classification</td>
        <td class="naive">30.00% (27/90)</td>
        <td class="ts">100.00% (90/90)</td>
        <td>Zero lethal under-triage</td>
      </tr>
      <tr>
        <td>Glucocorticoid Equivalence Traps</td>
        <td class="naive">60.00% (9/15)</td>
        <td class="ts">100.00% (15/15)</td>
        <td>Rule R1 exact potency math</td>
      </tr>
      <tr>
        <td>Washout & RT Window Traps</td>
        <td class="naive">16.67% (5/30)</td>
        <td class="ts">100.00% (30/30)</td>
        <td>Rule R2 & R3 relative day math</td>
      </tr>
      <tr>
        <td>CTCAE v5.0 Organ Reserve Traps</td>
        <td class="naive">6.67% (1/15)</td>
        <td class="ts">100.00% (15/15)</td>
        <td>Rule R4 ULN lab ceilings</td>
      </tr>
      <tr>
        <td>Verbatim Line-Citation Grounding</td>
        <td class="naive">0.0% (Ungrounded)</td>
        <td class="ts">100.00% (Verified)</td>
        <td>Rule R6 blocks hallucination</td>
      </tr>
    </tbody>
  </table>
  <div class="footer">
    <span>Reproducible: python3 scripts/evaluate_cohort.py --verify (6.02 ms/case)</span>
    <span class="live-pill">Live on Modal: trialswarm-ai-web.us-east.modal.run</span>
  </div>
</body>
</html>"""
}

def main():
    for name, html in SLIDES.items():
        src_path = ASSETS / name
        src_path.write_text(html, encoding="utf-8")
        out_png = ASSETS / name.replace(".html", ".png")
        cmd = [
            CHROME,
            "--headless",
            "--disable-gpu",
            "--window-size=1920,1080",
            f"--screenshot={out_png}",
            f"file://{src_path}",
        ]
        subprocess.run(cmd, check=True)
        print(f"Rendered: {out_png}")

if __name__ == "__main__":
    main()

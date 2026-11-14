#!/usr/bin/env python3
"""Evaluate TrialSwarm AI vs Naive Single-Prompt Baseline on the n=120 synthetic cohort."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.agents.extractor import extract_protocol_rules
from src.agents.phenotyper import extract_patient_phenotype
from src.agents.safety_auditor import (
    DEFAULT_REFERENCE_DATE,
    evaluate_naive_single_prompt_baseline,
)
from src.schemas import AuditReport
from src.swarm.coordinator import SwarmCoordinator

COHORT_PATH = REPO_ROOT / "data" / "cohort_120.json"
PROTOCOLS_DIR = REPO_ROOT / "data" / "protocols"
BENCHMARK_OUT_PATH = REPO_ROOT / "eval" / "results" / "benchmark_120.json"


def load_protocols() -> dict[str, dict[str, Any]]:
    """Load all cached ClinicalTrials.gov protocol JSON files from data/protocols/."""
    protocols: dict[str, dict[str, Any]] = {}
    for p_file in sorted(PROTOCOLS_DIR.glob("*.json")):
        with p_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        nct_id = str(data.get("nct_id") or p_file.stem).upper()
        protocols[nct_id] = data
    return protocols


def run_swarm_audit(
    coordinator: SwarmCoordinator,
    nct_id: str,
    patient: dict[str, Any],
    reference_date: str = DEFAULT_REFERENCE_DATE,
) -> AuditReport:
    """Execute TrialSwarm multi-agent audit in deterministic offline mode."""
    return coordinator.run_swarm(
        nct_id=nct_id,
        patient_ref=patient,
        reference_date=reference_date,
        use_llm=False,
        target_phase=patient.get("target_phase"),
    )


def _compute_binary_metrics(
    y_true: list[str],
    y_pred: list[str],
) -> tuple[float, float, float]:
    """Compute overall accuracy, sensitivity (Eligible=Pos), and specificity (Non-Eligible=Neg)."""
    n = len(y_true)
    if n == 0:
        return 0.0, 0.0, 0.0

    exact_matches = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = round((exact_matches / n) * 100.0, 2)

    # Clinical screening convention: Positive = ELIGIBLE, Negative = CONTRAINDICATED / NEEDS_HUMAN_REVIEW
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == "ELIGIBLE" and p == "ELIGIBLE")
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == "ELIGIBLE" and p != "ELIGIBLE")
    tn = sum(1 for t, p in zip(y_true, y_pred) if t != "ELIGIBLE" and p != "ELIGIBLE")
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != "ELIGIBLE" and p == "ELIGIBLE")

    sensitivity = round((tp / (tp + fn)) * 100.0, 2) if (tp + fn) > 0 else 0.0
    specificity = round((tn / (tn + fp)) * 100.0, 2) if (tn + fp) > 0 else 0.0
    return accuracy, sensitivity, specificity


def evaluate_cohort() -> dict[str, Any]:
    """Load cohort and protocols, evaluate both methods across n=120 cases, and aggregate metrics."""
    with COHORT_PATH.open("r", encoding="utf-8") as f:
        cohort = json.load(f)

    protocols = load_protocols()
    patients: list[dict[str, Any]] = cohort.get("patients", [])
    ref_date = str(cohort.get("reference_date") or DEFAULT_REFERENCE_DATE)

    coordinator = SwarmCoordinator()

    y_true: list[str] = []
    ts_preds: list[str] = []
    naive_preds: list[str] = []
    citation_rates: list[float] = []
    latencies_ms: list[float] = []
    mismatches: list[dict[str, Any]] = []

    # Trap counters
    steroid_total = 0
    steroid_ts = 0
    steroid_naive = 0

    washout_rt_total = 0
    washout_rt_ts = 0
    washout_rt_naive = 0

    organ_total = 0
    organ_ts = 0
    organ_naive = 0

    per_trial: dict[str, dict[str, Any]] = {}
    for nct_id in sorted(protocols.keys()):
        per_trial[nct_id] = {
            "total_cases": 0,
            "trialswarm_correct": 0,
            "naive_correct": 0,
            "trialswarm_accuracy": 0.0,
            "naive_accuracy": 0.0,
            "verdicts": {"ELIGIBLE": 0, "CONTRAINDICATED": 0, "NEEDS_HUMAN_REVIEW": 0},
        }

    for patient in patients:
        nct_id = str(patient["target_nct"]).upper()
        if nct_id not in protocols:
            raise KeyError(f"Protocol {nct_id} missing from {PROTOCOLS_DIR}")

        protocol = protocols[nct_id]
        expected_verdict = str(patient["expected_verdict"])
        archetype = str(patient.get("archetype") or "UNKNOWN")
        patient_ref_date = str(patient.get("reference_date") or ref_date)

        # (a) Explicit Naive Single-Prompt Baseline evaluation
        rules, _, _ = extract_protocol_rules(
            protocol, target_phase=patient.get("target_phase"), use_llm=False
        )
        phenotype, _, _ = extract_patient_phenotype(patient, use_llm=False)
        naive_verdict, _, _ = evaluate_naive_single_prompt_baseline(
            nct_id, rules, phenotype, reference_date=patient_ref_date
        )

        # (b) TrialSwarm Multi-Agent Swarm evaluation (deterministic offline mode)
        t0 = time.perf_counter()
        report = run_swarm_audit(
            coordinator, nct_id, patient, reference_date=patient_ref_date
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)

        ts_verdict = str(report.overall_verdict)
        citation_rates.append(float(report.citation_verification_rate))

        y_true.append(expected_verdict)
        ts_preds.append(ts_verdict)
        naive_preds.append(naive_verdict)

        # Per-trial tally
        t_bucket = per_trial.setdefault(
            nct_id,
            {
                "total_cases": 0,
                "trialswarm_correct": 0,
                "naive_correct": 0,
                "trialswarm_accuracy": 0.0,
                "naive_accuracy": 0.0,
                "verdicts": {"ELIGIBLE": 0, "CONTRAINDICATED": 0, "NEEDS_HUMAN_REVIEW": 0},
            },
        )
        t_bucket["total_cases"] += 1
        t_bucket["verdicts"][expected_verdict] = t_bucket["verdicts"].get(expected_verdict, 0) + 1
        if ts_verdict == expected_verdict:
            t_bucket["trialswarm_correct"] += 1
        else:
            mismatches.append(
                {
                    "patient_id": patient["patient_id"],
                    "nct_id": nct_id,
                    "archetype": archetype,
                    "expected_verdict": expected_verdict,
                    "trialswarm_verdict": ts_verdict,
                    "naive_verdict": naive_verdict,
                }
            )
        if naive_verdict == expected_verdict:
            t_bucket["naive_correct"] += 1

        # Trap breakdown
        if archetype == "STEROID_EQUIVALENCE_TRAP":
            steroid_total += 1
            if ts_verdict == expected_verdict:
                steroid_ts += 1
            if naive_verdict == expected_verdict:
                steroid_naive += 1
        elif archetype in ("WASHOUT_WINDOW_TRAP", "RADIATION_TRAP"):
            washout_rt_total += 1
            if ts_verdict == expected_verdict:
                washout_rt_ts += 1
            if naive_verdict == expected_verdict:
                washout_rt_naive += 1
        elif archetype == "ORGAN_LAB_CTCAE_TRAP":
            organ_total += 1
            if ts_verdict == expected_verdict:
                organ_ts += 1
            if naive_verdict == expected_verdict:
                organ_naive += 1

    for t_bucket in per_trial.values():
        tot = t_bucket["total_cases"]
        if tot > 0:
            t_bucket["trialswarm_accuracy"] = round(
                (t_bucket["trialswarm_correct"] / tot) * 100.0, 2
            )
            t_bucket["naive_accuracy"] = round(
                (t_bucket["naive_correct"] / tot) * 100.0, 2
            )

    ts_acc, ts_sens, ts_spec = _compute_binary_metrics(y_true, ts_preds)
    nv_acc, nv_sens, nv_spec = _compute_binary_metrics(y_true, naive_preds)

    mean_cit = round(sum(citation_rates) / len(citation_rates), 2) if citation_rates else 0.0
    mean_lat = round(sum(latencies_ms) / len(latencies_ms), 2) if latencies_ms else 0.0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(patients),
        "trialswarm_accuracy": ts_acc,
        "trialswarm_sensitivity": ts_sens,
        "trialswarm_specificity": ts_spec,
        "naive_accuracy": nv_acc,
        "naive_sensitivity": nv_sens,
        "naive_specificity": nv_spec,
        "steroid_traps_total": steroid_total,
        "steroid_traps_caught_trialswarm": steroid_ts,
        "steroid_traps_caught_naive": steroid_naive,
        "washout_and_rt_traps_total": washout_rt_total,
        "washout_and_rt_traps_caught_trialswarm": washout_rt_ts,
        "washout_and_rt_traps_caught_naive": washout_rt_naive,
        "organ_lab_traps_total": organ_total,
        "organ_lab_traps_caught_trialswarm": organ_ts,
        "organ_lab_traps_caught_naive": organ_naive,
        "citation_verification_rate": mean_cit,
        "mean_latency_ms": mean_lat,
        "per_trial_breakdown": per_trial,
        "mismatches": mismatches,
    }


def print_summary(results: dict[str, Any]) -> None:
    """Print clean CLI benchmark summary table."""
    print("=" * 72)
    print(f"TrialSwarm AI Cohort Benchmark Evaluation (n={results['total_cases']})")
    print("=" * 72)
    print(
        f"TrialSwarm  | Accuracy: {results['trialswarm_accuracy']:6.2f}% | "
        f"Sensitivity: {results['trialswarm_sensitivity']:6.2f}% | "
        f"Specificity: {results['trialswarm_specificity']:6.2f}%"
    )
    print(
        f"Naive LLM   | Accuracy: {results['naive_accuracy']:6.2f}% | "
        f"Sensitivity: {results['naive_sensitivity']:6.2f}% | "
        f"Specificity: {results['naive_specificity']:6.2f}%"
    )
    print("-" * 72)
    print(
        f"Steroid Equivalence Traps : TrialSwarm {results['steroid_traps_caught_trialswarm']}/{results['steroid_traps_total']} | "
        f"Naive {results['steroid_traps_caught_naive']}/{results['steroid_traps_total']}"
    )
    print(
        f"Washout & RT Window Traps : TrialSwarm {results['washout_and_rt_traps_caught_trialswarm']}/{results['washout_and_rt_traps_total']} | "
        f"Naive {results['washout_and_rt_traps_caught_naive']}/{results['washout_and_rt_traps_total']}"
    )
    print(
        f"Organ Lab CTCAE Traps     : TrialSwarm {results['organ_lab_traps_caught_trialswarm']}/{results['organ_lab_traps_total']} | "
        f"Naive {results['organ_lab_traps_caught_naive']}/{results['organ_lab_traps_total']}"
    )
    print("-" * 72)
    print(f"Citation Verification Rate: {results['citation_verification_rate']:.2f}%")
    print(f"Mean Swarm Latency        : {results['mean_latency_ms']:.2f} ms/case")
    print(f"Mismatches                : {len(results['mismatches'])}")
    print("-" * 72)
    for nct, stats in results["per_trial_breakdown"].items():
        print(
            f"  {nct} (n={stats['total_cases']}): "
            f"TrialSwarm {stats['trialswarm_correct']}/{stats['total_cases']} ({stats['trialswarm_accuracy']:.1f}%) | "
            f"Naive {stats['naive_correct']}/{stats['total_cases']} ({stats['naive_accuracy']:.1f}%)"
        )
    print("=" * 72)


def verify_against_committed(computed: dict[str, Any], committed_path: Path) -> bool:
    """Compare computed metrics against committed JSON, ignoring generated_at and mean_latency_ms."""
    if not committed_path.exists():
        print(f"[ERROR] Committed benchmark file not found: {committed_path}", file=sys.stderr)
        return False

    with committed_path.open("r", encoding="utf-8") as f:
        committed = json.load(f)

    ignored_keys = {"generated_at", "mean_latency_ms"}
    computed_cmp = {k: v for k, v in computed.items() if k not in ignored_keys}
    committed_cmp = {k: v for k, v in committed.items() if k not in ignored_keys}

    if computed_cmp == committed_cmp:
        print(f"[PASS] Computed metrics match committed {committed_path.relative_to(REPO_ROOT)} exactly.")
        return True

    print(f"[FAIL] Metric mismatch against {committed_path.relative_to(REPO_ROOT)}:", file=sys.stderr)
    all_keys = sorted(set(computed_cmp.keys()) | set(committed_cmp.keys()))
    for k in all_keys:
        if computed_cmp.get(k) != committed_cmp.get(k):
            print(
                f"  - {k}: computed={computed_cmp.get(k)!r} != committed={committed_cmp.get(k)!r}",
                file=sys.stderr,
            )
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate TrialSwarm vs Naive Baseline across the 120-patient synthetic cohort."
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify computed metrics against committed eval/results/benchmark_120.json.",
    )
    args = parser.parse_args()

    results = evaluate_cohort()
    print_summary(results)

    if args.verify:
        ok = verify_against_committed(results, BENCHMARK_OUT_PATH)
        return 0 if ok else 1

    BENCHMARK_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with BENCHMARK_OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")
    print(f"Saved benchmark results to {BENCHMARK_OUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

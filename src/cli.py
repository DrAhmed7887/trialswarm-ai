"""Antigravity /swarm CLI for TrialSwarm AI clinical trial feasibility & safety auditing."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from src.agents.safety_auditor import DEFAULT_REFERENCE_DATE
from src.agents.verifier import run_adversarial_verification_probe
from src.schemas import AdversarialTrapResult, AuditReport
from src.swarm.coordinator import (
    SwarmCoordinator,
    fetch_live_nct_protocol,
    load_patient_record,
)


def _format_board(report: AuditReport) -> str:
    lines: list[str] = []
    lines.append("=" * 88)
    lines.append(f"ANTIGRAVITY /SWARM MESSAGE BOARD  |  {report.nct_id} x {report.patient_id} ({report.patient_name})")
    lines.append(f"Run ID: {report.run_id}  |  Mode: {report.execution_mode}  |  Elapsed: {report.elapsed_seconds:.4f}s")
    lines.append("=" * 88)

    lines.append("\n[SWARM ROSTER]")
    for member in report.roster:
        lines.append(
            f"  - {member.name:<16} | {member.role:<42} | {member.model:<28} | {member.state.upper()} (#{member.latest_seq})"
        )

    lines.append("\n[BOARD TRANSCRIPT #1 - #8]")
    for post in report.board_posts:
        mentions = ", ".join(post.mentions)
        lines.append(
            f"  #{post.seq} {post.author} -> {mentions}  [{post.model_used} | {post.latency_ms}ms]"
        )
        lines.append(f"     {post.summary}")

    lines.append("=" * 88)
    return "\n".join(lines)


def _format_full_report(report: AuditReport) -> str:
    lines: list[str] = [_format_board(report)]

    lines.append("\n[CLINICAL SAFETY & PHARMACOLOGY RULES R1-R5]")
    for sf in report.safety_findings:
        extra: list[str] = []
        if sf.prednisone_eq_mg is not None:
            extra.append(f"prednisone_eq_mg={sf.prednisone_eq_mg:.2f}")
        if sf.washout_days_elapsed is not None:
            extra.append(f"elapsed={sf.washout_days_elapsed}d / req={sf.washout_days_required}d")
        if sf.earliest_rescreen_date:
            extra.append(f"earliest_rescreen={sf.earliest_rescreen_date}")
        extra_str = f" ({', '.join(extra)})" if extra else ""
        lines.append(f"  [{sf.severity:<12}] {sf.rule_code} | {sf.title}{extra_str}")
        lines.append(f"      Detail: {sf.calculation_detail}")
        for cit in sf.citations:
            v_flag = "VERIFIED" if cit.verified else "UNVERIFIED"
            lines.append(
                f"      Cite [{v_flag}] {cit.doc_type}:{cit.doc_id} L{cit.line_start}-{cit.line_end}: \"{cit.verbatim_quote[:95]}\""
            )

    lines.append("\n[GROUNDED CRITERION VERDICTS]")
    for cv in report.criterion_verdicts:
        naive_note = f" | naive={cv.naive_baseline_status}" if cv.naive_baseline_status else ""
        lines.append(
            f"  [{cv.status:<12}] {cv.rule_id} ({cv.category}){naive_note}: {cv.criterion}"
        )
        lines.append(f"      Reasoning: {cv.reasoning}")
        for cit in cv.citations:
            v_flag = "VERIFIED" if cit.verified else "UNVERIFIED"
            lines.append(
                f"      Cite [{v_flag}] {cit.doc_type}:{cit.doc_id} L{cit.line_start}: \"{cit.verbatim_quote[:95]}\""
            )

    lines.append("\n" + "=" * 88)
    lines.append(f"FINAL VERDICT:             {report.overall_verdict}")
    lines.append(f"NAIVE BASELINE VERDICT:    {report.naive_baseline_verdict}")
    lines.append(f"CAUGHT HIDDEN TRAP:        {report.caught_hidden_trap}")
    if report.trap_explanation:
        lines.append(f"TRAP EXPLANATION:          {report.trap_explanation}")
    lines.append(f"CITATION VERIFICATION:     {report.citation_verification_rate:.1f}% (blocked={report.unverified_claims_blocked})")
    lines.append(
        f"UNIT ECONOMICS:            ${report.estimated_compute_usd:.4f} compute vs "
        f"${report.manual_benchmark_usd:.2f} manual (~{report.hours_saved:.1f}h saved)"
    )
    lines.append(
        f"STAGED SIGN-OFF PACKET:    {report.signoff_packet.packet_id} "
        f"[{report.signoff_packet.action_type} | {report.signoff_packet.status}]"
    )
    if report.signoff_packet.earliest_rescreen_date:
        lines.append(f"EARLIEST RE-SCREEN DATE:   {report.signoff_packet.earliest_rescreen_date}")
    lines.append(f"EVIDENCE PMIDs:            {', '.join(report.evidence_pmids)}")
    lines.append("=" * 88)
    return "\n".join(lines)


def _format_trap_result(res: AdversarialTrapResult) -> str:
    lines = [
        "=" * 88,
        f"ADVERSARIAL VERIFICATION PROBE (RULE R6 + RULE R1) | {res.nct_id} x {res.case_id}",
        "=" * 88,
        f"Injected Hallucination:    \"{res.injected_hallucination_quote}\" (attributed to EHR Line 1)",
        f"Verifier Status:           {res.verifier_status}",
        f"Unverified Claims Blocked: {res.unverified_claims_blocked}",
        f"Naive Steroid Verdict:     {res.naive_steroid_verdict}",
        f"TrialSwarm Verdict:        {res.trialswarm_steroid_verdict}",
        f"Prednisone Equivalent:     {res.prednisone_eq_mg:.2f} mg/day",
        f"Earliest Rescreen Date:    {res.earliest_rescreen_date or 'N/A'}",
        f"Details:                   {res.details}",
        "=" * 88,
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m src.cli",
        description="TrialSwarm AI — Antigravity /swarm Clinical Trial Eligibility & Safety Auditor",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_swarm = sub.add_parser("swarm", help="Run full multi-agent /swarm eligibility audit")
    p_swarm.add_argument("--nct", required=True, help="ClinicalTrials.gov NCT ID (e.g., NCT04613596)")
    p_swarm.add_argument("--patient", required=True, help="Patient ID (e.g., PT-102, COHORT-001) or JSON path")
    p_swarm.add_argument("--ref-date", default=DEFAULT_REFERENCE_DATE, help="Reference screening date YYYY-MM-DD")
    p_swarm.add_argument("--use-llm", action="store_true", help="Enable optional Gemini 2.5 Flash/Pro enrichment")
    p_swarm.add_argument("--json", action="store_true", help="Output full AuditReport as JSON")

    p_trap = sub.add_parser("verify-trap", help="Run adversarial citation hallucination & steroid trap probe")
    p_trap.add_argument("--nct", default="NCT04613596", help="Target NCT ID (default: NCT04613596)")
    p_trap.add_argument("--patient", default="PT-102", help="Target Patient ID (default: PT-102)")
    p_trap.add_argument("--ref-date", default=DEFAULT_REFERENCE_DATE, help="Reference screening date YYYY-MM-DD")
    p_trap.add_argument("--json", action="store_true", help="Output AdversarialTrapResult as JSON")

    p_board = sub.add_parser("board", help="Display the Antigravity /swarm coordination message board")
    p_board.add_argument("--nct", default="NCT04613596", help="Target NCT ID (default: NCT04613596)")
    p_board.add_argument("--patient", default="PT-102", help="Target Patient ID (default: PT-102)")
    p_board.add_argument("--ref-date", default=DEFAULT_REFERENCE_DATE, help="Reference screening date YYYY-MM-DD")
    p_board.add_argument("--use-llm", action="store_true", help="Enable optional Gemini 2.5 Flash/Pro enrichment")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    coordinator = SwarmCoordinator()

    if args.command == "swarm":
        report = coordinator.run_swarm(
            nct_id=args.nct,
            patient_ref=args.patient,
            reference_date=args.ref_date,
            use_llm=args.use_llm,
        )
        if args.json:
            print(report.model_dump_json(indent=2))
        else:
            print(_format_full_report(report))
        return 0

    if args.command == "verify-trap":
        protocol = fetch_live_nct_protocol(args.nct)
        patient = load_patient_record(args.patient)
        trap_res = run_adversarial_verification_probe(
            protocol=protocol,
            patient=patient,
            reference_date=args.ref_date,
        )
        if args.json:
            print(trap_res.model_dump_json(indent=2))
        else:
            print(_format_trap_result(trap_res))
        return 0

    if args.command == "board":
        report = coordinator.run_swarm(
            nct_id=args.nct,
            patient_ref=args.patient,
            reference_date=args.ref_date,
            use_llm=args.use_llm,
        )
        print(_format_board(report))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

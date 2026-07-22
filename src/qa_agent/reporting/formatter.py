"""Text formatter for QA reports."""

from __future__ import annotations

from src.qa_agent.domain.schemas.aggregate_report import AggregateReport
from src.qa_agent.domain.schemas.evaluation_report import EvaluationReport


def format_evaluation(report: EvaluationReport) -> str:
    lines = [
        f"ÉVALUATION — {report.conversation_id[:16]}",
        f"Profil        : {report.runner_profile_id}",
        f"Score global  : {report.global_score:.1f}/10",
        "=" * 62,
    ]

    if report.hard_check_failures:
        lines.append("\n⚠  VIOLATIONS OBJECTIVES :")
        for f in report.hard_check_failures:
            lines.append(f"   • {f}")

    lines.append("\nSCORES PAR DIMENSION :")
    for dim, score in report.scores.items():
        filled = "█" * score.score
        empty = "░" * (5 - score.score)
        turn = f" (tour {score.cited_turn})" if score.cited_turn is not None else ""
        lines.append(f"  {dim:<26} [{filled}{empty}] {score.score}/5{turn}")
        if score.justification:
            lines.append(f"    → {score.justification}")

    if report.strengths:
        lines.append("\nFORCES :")
        for s in report.strengths:
            lines.append(f"  + {s}")

    if report.weaknesses:
        lines.append("\nFAIBLESSES :")
        for w in report.weaknesses:
            lines.append(f"  - {w}")

    if report.blockers:
        lines.append("\nPOINTS BLOQUANTS :")
        for b in report.blockers:
            lines.append(f"  ✗ {b}")

    if report.suggested_improvements:
        lines.append("\nAMÉLIORATIONS PROPOSÉES :")
        for imp in report.suggested_improvements:
            lines.append(f"  → {imp}")

    return "\n".join(lines)


def format_aggregate(report: AggregateReport) -> str:
    lines = [
        f"RAPPORT QA MIRRORPACE — {report.generated_at[:10]}",
        f"{report.total_conversations} conversation(s) analysée(s)",
        "=" * 62,
        "",
        f"Score moyen   : {report.mean_global_score:.1f}/10  (σ = {report.std_global_score:.1f})",
        "",
        "SCORES PAR DIMENSION :",
    ]

    for dim, avg in sorted(report.scores_by_dimension.items(), key=lambda x: x[1]):
        filled = "█" * round(avg)
        empty = "░" * (5 - round(avg))
        lines.append(f"  {dim:<26} [{filled}{empty}] {avg:.1f}/5")

    lines += [
        "",
        "MÉTRIQUES QUALITÉ :",
        f"  Contradictions KE        : {report.ke_contradiction_rate * 100:.0f}%",
        f"  Alerte médicale manquée  : {report.medical_flag_miss_rate * 100:.0f}%",
        f"  Mémoire non référencée   : {(1 - report.memory_utilization_rate) * 100:.0f}%",
    ]

    if report.termination_breakdown:
        lines.append("\nFIN DE CONVERSATION :")
        for reason, count in sorted(report.termination_breakdown.items()):
            lines.append(f"  {reason:<15} : {count}")

    if report.top_blockers:
        lines.append("\nTOP PROBLÈMES :")
        for blocker, count in report.top_blockers[:5]:
            lines.append(f"  ({count}x) {blocker}")

    if report.interesting_conversations:
        n = len(report.interesting_conversations)
        lines.append(f"\nCONVERSATIONS INTÉRESSANTES ({n}) :")
        for conv_id in report.interesting_conversations[:5]:
            lines.append(f"  {conv_id}")

    return "\n".join(lines)

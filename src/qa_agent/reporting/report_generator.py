"""ReportGenerator — aggregate statistics over N EvaluationReports."""

from __future__ import annotations

import statistics
from collections import Counter
from datetime import datetime, timezone

from src.qa_agent.domain.schemas.aggregate_report import AggregateReport
from src.qa_agent.domain.schemas.evaluation_report import EvaluationReport


class ReportGenerator:
    def generate(
        self,
        reports: list[EvaluationReport],
        termination_breakdown: dict[str, int] | None = None,
    ) -> AggregateReport:
        if not reports:
            return _empty_report()

        n = len(reports)
        global_scores = [r.global_score for r in reports]

        all_dims: set[str] = set()
        for r in reports:
            all_dims.update(r.scores.keys())

        scores_by_dimension: dict[str, float] = {}
        for dim in all_dims:
            dim_scores = [r.scores[dim].score for r in reports if dim in r.scores]
            scores_by_dimension[dim] = round(statistics.mean(dim_scores), 2) if dim_scores else 0.0

        ke_failures = sum(
            1 for r in reports
            if any("ke_contradiction" in f for f in r.hard_check_failures)
        )
        medical_failures = sum(
            1 for r in reports
            if any("medical_flag" in f for f in r.hard_check_failures)
        )
        memory_unused = sum(
            1 for r in reports
            if any("memory_not_utilized" in f for f in r.hard_check_failures)
        )

        all_blockers: list[str] = []
        for r in reports:
            all_blockers.extend(r.blockers)
        top_blockers = Counter(all_blockers).most_common(10)

        # Outliers: score < 3 (poor) or score > 8.5 (excellent)
        interesting = [
            r.conversation_id for r in reports
            if r.global_score < 3.0 or r.global_score > 8.5
        ]

        return AggregateReport(
            total_conversations=n,
            mean_global_score=round(statistics.mean(global_scores), 2),
            std_global_score=round(statistics.stdev(global_scores) if n > 1 else 0.0, 2),
            scores_by_dimension=scores_by_dimension,
            memory_utilization_rate=round(1.0 - memory_unused / n, 2),
            ke_contradiction_rate=round(ke_failures / n, 2),
            medical_flag_miss_rate=round(medical_failures / n, 2),
            termination_breakdown=termination_breakdown or {},
            top_blockers=top_blockers,
            interesting_conversations=interesting,
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
        )


def _empty_report() -> AggregateReport:
    return AggregateReport(
        total_conversations=0,
        mean_global_score=0.0,
        std_global_score=0.0,
        scores_by_dimension={},
        memory_utilization_rate=0.0,
        ke_contradiction_rate=0.0,
        medical_flag_miss_rate=0.0,
        termination_breakdown={},
        top_blockers=[],
        interesting_conversations=[],
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
    )

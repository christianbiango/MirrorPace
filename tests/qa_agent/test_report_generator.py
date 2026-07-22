"""Unit tests for ReportGenerator — aggregate statistics."""

from __future__ import annotations

import pytest

from src.qa_agent.domain.schemas.evaluation_report import DimensionScore, EvaluationReport
from src.qa_agent.reporting.report_generator import ReportGenerator


def _report(
    conv_id: str,
    global_score: float,
    scores: dict[str, int] | None = None,
    hard_failures: list[str] | None = None,
    blockers: list[str] | None = None,
) -> EvaluationReport:
    scores = scores or {"question_answered": 4, "tone_appropriateness": 3}
    return EvaluationReport(
        conversation_id=conv_id,
        runner_profile_id="test",
        scores={
            dim: DimensionScore(score=s, justification="", cited_turn=None)
            for dim, s in scores.items()
        },
        global_score=global_score,
        hard_check_failures=hard_failures or [],
        strengths=[],
        weaknesses=[],
        blockers=blockers or [],
        suggested_improvements=[],
        evaluated_at="2026-07-22T00:00:00Z",
    )


@pytest.fixture
def generator() -> ReportGenerator:
    return ReportGenerator()


# ── empty input ───────────────────────────────────────────────────────────────

def test_empty_reports_returns_zero_totals(generator):
    result = generator.generate([])
    assert result.total_conversations == 0
    assert result.mean_global_score == 0.0


# ── basic aggregation ─────────────────────────────────────────────────────────

def test_mean_global_score(generator):
    reports = [_report("c1", 6.0), _report("c2", 8.0), _report("c3", 7.0)]
    result = generator.generate(reports)
    assert result.total_conversations == 3
    assert result.mean_global_score == 7.0


def test_std_global_score_single_report_is_zero(generator):
    result = generator.generate([_report("c1", 7.0)])
    assert result.std_global_score == 0.0


def test_std_global_score_multiple_reports(generator):
    reports = [_report("c1", 4.0), _report("c2", 8.0)]
    result = generator.generate(reports)
    assert result.std_global_score > 0.0


# ── dimension averages ────────────────────────────────────────────────────────

def test_scores_by_dimension_averaged(generator):
    r1 = _report("c1", 6.0, scores={"question_answered": 4})
    r2 = _report("c2", 7.0, scores={"question_answered": 2})
    result = generator.generate([r1, r2])
    assert result.scores_by_dimension["question_answered"] == 3.0


# ── hard check rates ──────────────────────────────────────────────────────────

def test_ke_contradiction_rate(generator):
    r1 = _report("c1", 4.0, hard_failures=["ke_contradiction_turn_1: KE=deload"])
    r2 = _report("c2", 7.0)
    r3 = _report("c3", 8.0, hard_failures=["ke_contradiction_turn_2: KE=decrease"])
    result = generator.generate([r1, r2, r3])
    assert result.ke_contradiction_rate == pytest.approx(2 / 3, rel=0.01)


def test_medical_flag_miss_rate(generator):
    r1 = _report("c1", 5.0, hard_failures=["medical_flag_missed: KE flagged"])
    r2 = _report("c2", 7.0)
    result = generator.generate([r1, r2])
    assert result.medical_flag_miss_rate == 0.5


def test_memory_utilization_rate(generator):
    r1 = _report("c1", 4.0, hard_failures=["memory_not_utilized: 2 decisions"])
    r2 = _report("c2", 7.0)
    r3 = _report("c3", 6.0)
    result = generator.generate([r1, r2, r3])
    # 2 out of 3 used memory
    assert result.memory_utilization_rate == pytest.approx(2 / 3, rel=0.01)


# ── blockers ──────────────────────────────────────────────────────────────────

def test_top_blockers_counted(generator):
    r1 = _report("c1", 5.0, blockers=["réponse trop vague", "ton inapproprié"])
    r2 = _report("c2", 6.0, blockers=["réponse trop vague"])
    r3 = _report("c3", 7.0, blockers=["réponse trop vague", "hallucination"])
    result = generator.generate([r1, r2, r3])
    top = dict(result.top_blockers)
    assert top["réponse trop vague"] == 3
    assert top["ton inapproprié"] == 1


# ── outliers ──────────────────────────────────────────────────────────────────

def test_interesting_conversations_low_score(generator):
    r1 = _report("low-score", 2.0)
    r2 = _report("mid-score", 6.0)
    result = generator.generate([r1, r2])
    assert "low-score" in result.interesting_conversations
    assert "mid-score" not in result.interesting_conversations


def test_interesting_conversations_high_score(generator):
    r1 = _report("high-score", 9.0)
    r2 = _report("mid-score", 6.0)
    result = generator.generate([r1, r2])
    assert "high-score" in result.interesting_conversations


# ── termination breakdown ──────────────────────────────────────────────────────

def test_termination_breakdown_passed_through(generator):
    result = generator.generate(
        [_report("c1", 6.0)],
        termination_breakdown={"satisfied": 3, "max_turns": 1},
    )
    assert result.termination_breakdown["satisfied"] == 3
    assert result.termination_breakdown["max_turns"] == 1

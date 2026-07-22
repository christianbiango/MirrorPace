"""ConversationJudge — LLM-based qualitative evaluation of conversations."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from src.qa_agent.domain.rubric import (
    DIMENSION_WEIGHTS,
    SOFT_DIMENSIONS,
    build_judge_system_prompt,
)
from src.qa_agent.domain.schemas.conversation_log import ConversationLog
from src.qa_agent.domain.schemas.evaluation_report import DimensionScore, EvaluationReport
from src.qa_agent.llm import QAGeminiClient


class ConversationJudge:
    def __init__(self, api_key: str) -> None:
        self._client = QAGeminiClient(api_key=api_key)
        self._system_prompt = build_judge_system_prompt()

    def evaluate(
        self,
        log: ConversationLog,
        hard_check_failures: list[str],
    ) -> EvaluationReport:
        user_prompt = _build_user_prompt(log, hard_check_failures)

        raw = self._client.generate(
            system_prompt=self._system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=3000,
        )
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

        scores = _parse_scores(data)
        global_score = _compute_global_score(scores, hard_check_failures)

        return EvaluationReport(
            conversation_id=log.conversation_id,
            runner_profile_id=log.runner_profile.id,
            scores=scores,
            global_score=global_score,
            hard_check_failures=hard_check_failures,
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            blockers=data.get("blockers", []),
            suggested_improvements=data.get("suggested_improvements", []),
            evaluated_at=datetime.now(tz=timezone.utc).isoformat(),
        )


def _parse_scores(data: dict) -> dict[str, DimensionScore]:
    scores: dict[str, DimensionScore] = {}
    raw_scores = data.get("scores", {})
    for dim in SOFT_DIMENSIONS:
        dim_data = raw_scores.get(dim, {})
        score_val = dim_data.get("score", 3)
        try:
            score_val = max(1, min(5, int(score_val)))
        except (TypeError, ValueError):
            score_val = 3
        scores[dim] = DimensionScore(
            score=score_val,
            justification=str(dim_data.get("justification", "")),
            cited_turn=dim_data.get("cited_turn"),
        )
    return scores


def _compute_global_score(
    scores: dict[str, DimensionScore],
    hard_check_failures: list[str],
) -> float:
    weighted_sum = sum(
        scores[dim].score * DIMENSION_WEIGHTS.get(dim, 0.0)
        for dim in scores
    )
    total_weight = sum(DIMENSION_WEIGHTS.get(dim, 0.0) for dim in scores)

    if total_weight == 0:
        return 0.0

    # Normalize 1-5 range to 0-10 scale
    raw = (weighted_sum / total_weight) * 2.0

    # KE contradiction hard-caps the score at 5
    if any("ke_contradiction" in f for f in hard_check_failures):
        raw = min(raw, 5.0)

    return round(raw, 2)


def _build_user_prompt(log: ConversationLog, hard_check_failures: list[str]) -> str:
    lines = [
        f"## Profil du coureur simulé : {log.runner_profile.display_name}",
        f"Tags : {', '.join(log.runner_profile.tags)}",
        "",
        "## Conversation",
    ]

    for entry in log.entries:
        lines.append(f"\n**Tour {entry.turn_number} — Coureur :** {entry.user_message}")
        lines.append(f"**Tour {entry.turn_number} — Coach :** {entry.agent_response.text}")

        if entry.envelope_snapshot is not None:
            env = entry.envelope_snapshot
            triggered = [r.rule_id for r in env.triggered_rules if r.triggered]
            lines.append(
                f"*[KE : action={env.decision.action}, "
                f"readiness={env.readiness.score}/100, "
                f"règles={triggered}, "
                f"renvoi_médical={env.medical_referral}]*"
            )

    lines.append(f"\n**Fin de conversation :** {log.termination_reason}")

    if hard_check_failures:
        lines.append("\n## Violations objectives détectées")
        for failure in hard_check_failures:
            lines.append(f"- {failure}")

    return "\n".join(lines)

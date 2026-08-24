from __future__ import annotations

import json

import pytest

from src.qa_agent.evaluation.conversation_judge import ConversationJudge


class _FakeClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.last_call: dict | None = None

    def generate(self, system_prompt, user_prompt, temperature=0.5, max_tokens=1000):
        self.last_call = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        return self.response_text


def _all_fives_response() -> str:
    return json.dumps({
        "scores": {
            dim: {"score": 5, "justification": "ok"}
            for dim in [
                "question_answered", "factual_groundedness", "tone_appropriateness",
                "pedagogical_quality", "conversation_coherence", "empathy",
            ]
        },
        "strengths": ["clair"],
        "weaknesses": [],
        "blockers": [],
        "suggested_improvements": [],
    })


def test_requires_api_key_or_client():
    with pytest.raises(ValueError):
        ConversationJudge()


def test_uses_injected_client_instead_of_building_gemini():
    client = _FakeClient(_all_fives_response())
    judge = ConversationJudge(client=client)

    report = judge.evaluate_raw(
        conversation_id="conv-1",
        runner_profile_id="anxious_beginner",
        user_prompt="## Conversation\n...",
        hard_check_failures=[],
    )

    assert client.last_call is not None
    assert report.global_score == 10.0
    assert report.conversation_id == "conv-1"
    assert report.runner_profile_id == "anxious_beginner"


def test_ke_contradiction_caps_score_at_five():
    client = _FakeClient(_all_fives_response())
    judge = ConversationJudge(client=client)

    report = judge.evaluate_raw(
        conversation_id="conv-1",
        runner_profile_id="anxious_beginner",
        user_prompt="...",
        hard_check_failures=["ke_contradiction: coach ignored deload"],
    )

    assert report.global_score == 5.0


def test_malformed_json_falls_back_to_default_scores():
    client = _FakeClient("not json")
    judge = ConversationJudge(client=client)

    report = judge.evaluate_raw(
        conversation_id="conv-1",
        runner_profile_id="anxious_beginner",
        user_prompt="...",
        hard_check_failures=[],
    )

    assert all(s.score == 3 for s in report.scores.values())

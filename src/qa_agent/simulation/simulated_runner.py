"""SimulatedRunner — LLM-driven user simulator.

Black-box from the CoachAgent's perspective: sees only text responses,
never envelopes, sessions, or implementation internals.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass

from src.qa_agent.domain.schemas.runner_profile import RunnerProfile
from src.qa_agent.llm import QAGeminiClient

_CONTINUATION_INSTRUCTIONS = """

## Format de réponse obligatoire (JSON strict)

{"message": "<ton prochain message au coach>", "satisfied": <true|false>}

Règles :
- "message" : ton prochain message, naturel, dans ton personnage
- "satisfied" : true si tu as reçu une réponse claire et satisfaisante à ta question principale
  - Tu peux être satisfait même en n'étant pas totalement d'accord
  - Si tu poses encore une question, satisfied = false
  - Si tu conclus ou remercies, satisfied = true
- Réponds UNIQUEMENT avec ce JSON, rien d'autre
"""


@dataclass
class RunnerMessage:
    message: str
    satisfied: bool


class SimulatedRunner:
    def __init__(self, profile: RunnerProfile, api_key: str) -> None:
        self._profile = profile
        self._client = QAGeminiClient(api_key=api_key)

    def first_message(self) -> str:
        return random.choice(self._profile.opening_messages)

    def next_message(self, conversation_history: list[dict[str, str]]) -> RunnerMessage:
        """Generate next message given conversation history.

        Args:
            conversation_history: [{"role": "user"|"assistant", "content": "..."}]
        """
        system = self._profile.system_prompt + _CONTINUATION_INSTRUCTIONS

        # Format history so Gemini clearly understands its role (it IS the coureur)
        if conversation_history:
            turns = []
            for m in conversation_history:
                label = "Toi" if m["role"] == "user" else "Coach MirrorPace"
                turns.append(f"{label}: {m['content']}")
            history_block = "\n\n".join(turns)
            user_prompt = (
                f"Voici la conversation jusqu'à maintenant :\n\n{history_block}\n\n"
                "C'est maintenant TON TOUR de répondre au coach. "
                "Reste dans ton personnage. Retourne uniquement le JSON demandé."
            )
        else:
            user_prompt = "La conversation commence. Envoie ton premier message au coach."

        raw = self._client.generate(
            system_prompt=system,
            user_prompt=user_prompt,
            temperature=0.8,
            max_tokens=300,
        )
        try:
            data = json.loads(raw)
            return RunnerMessage(
                message=str(data.get("message", "")),
                satisfied=bool(data.get("satisfied", False)),
            )
        except (json.JSONDecodeError, KeyError):
            return RunnerMessage(message=raw, satisfied=False)

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..domain.schemas.coach_response import RawLLMResponse
from ..domain.schemas.reasoning_context import ReasoningContext
from .prompt_builder import SYSTEM_PROMPT, build_prompt


@runtime_checkable
class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> RawLLMResponse:
        ...


class ResponseAssembler:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client

    def assemble(self, context: ReasoningContext) -> RawLLMResponse:
        user_prompt = build_prompt(context)
        return self._llm.generate(SYSTEM_PROMPT, user_prompt)

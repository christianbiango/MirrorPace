"""Minimal Gemini client for SimulatedRunner and ConversationJudge."""

from __future__ import annotations

from google import genai
from google.genai import types

_DEFAULT_MODEL = "gemini-2.5-flash"


class QAGeminiClient:
    def __init__(self, api_key: str, model: str = _DEFAULT_MODEL) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 1000,
    ) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
                temperature=temperature,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return response.text or "{}"

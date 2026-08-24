"""Minimal LLM clients for SimulatedRunner and ConversationJudge.

QAGeminiClient is the default for both roles. QAGroqClient / QAMistralClient exist
so the judge can be run on a different model family than the one being judged —
avoids the self-preference bias of an LLM judge scoring its own family's output,
and lets several independent judges vote instead of trusting a single one.
"""

from __future__ import annotations

import openai
from google import genai
from google.genai import types

_DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
_DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_DEFAULT_MISTRAL_MODEL = "mistral-large-latest"
_MISTRAL_BASE_URL = "https://api.mistral.ai/v1"


class QAGeminiClient:
    def __init__(self, api_key: str, model: str = _DEFAULT_GEMINI_MODEL) -> None:
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


class _OpenAICompatibleClient:
    """Shared implementation for any provider exposing an OpenAI-compatible
    chat completions endpoint (Groq, Mistral, ...)."""

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 1000,
    ) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or "{}"


class QAGroqClient(_OpenAICompatibleClient):
    def __init__(self, api_key: str, model: str = _DEFAULT_GROQ_MODEL) -> None:
        super().__init__(api_key=api_key, model=model, base_url=_GROQ_BASE_URL)


class QAMistralClient(_OpenAICompatibleClient):
    def __init__(self, api_key: str, model: str = _DEFAULT_MISTRAL_MODEL) -> None:
        super().__init__(api_key=api_key, model=model, base_url=_MISTRAL_BASE_URL)

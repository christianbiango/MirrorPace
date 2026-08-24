from __future__ import annotations

from google import genai
from google.genai import types

from ..domain.schemas.coach_response import RawLLMResponse

_DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiLLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = 3000,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def generate(self, system_prompt: str, user_prompt: str) -> RawLLMResponse:
        response = self._client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=self.max_tokens,
                response_mime_type="application/json",
                # Gemini 2.5's "thinking" tokens count against max_output_tokens.
                # With thinking enabled, long reasoning prompts (decision + metrics
                # + profile + scientific/memory context) can burn most of the
                # budget on invisible thinking tokens, truncating the visible JSON
                # mid-string — which then fails to parse and leaks raw JSON text
                # to the end user (see data/qa_pipe pipe run, ambitious_marathoner
                # turn 1). Disable thinking to guarantee the full budget goes to
                # the actual response, matching src/qa_agent/llm.py.
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        usage = response.usage_metadata
        return RawLLMResponse(
            text=response.text or "",
            model=self.model,
            input_tokens=usage.prompt_token_count or 0,
            output_tokens=usage.candidates_token_count or 0,
        )

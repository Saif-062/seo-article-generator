"""Groq LLM provider implementation."""

from __future__ import annotations

import json
from typing import Any

from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.providers.llm.base import BaseLLMProvider, LLMProviderError


class GroqProvider(BaseLLMProvider):
    """
    LLM provider using Groq API.

    Groq offers free access to Llama 3.3 70B with very fast inference.
    API docs: https://console.groq.com/docs
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.groq_api_key
        self._model = model or settings.llm_model

        if not self.api_key:
            raise LLMProviderError(
                "GROQ_API_KEY not configured",
                provider=self.name,
                retryable=False,
            )

        self.client = AsyncGroq(api_key=self.api_key)

    @property
    def name(self) -> str:
        return "groq"

    @property
    def model(self) -> str:
        return self._model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        json_mode: bool = False,
    ) -> str:
        """Generate text using Groq API."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            kwargs = {
                "model": self._model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**kwargs)

            content = response.choices[0].message.content
            if content is None:
                raise LLMProviderError(
                    "Empty response from model",
                    provider=self.name,
                    retryable=True,
                )

            return content

        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise LLMProviderError(
                    "Rate limit exceeded",
                    provider=self.name,
                    retryable=True,
                )
            elif "invalid_api_key" in str(e).lower():
                raise LLMProviderError(
                    "Invalid API key",
                    provider=self.name,
                    retryable=False,
                )
            else:
                raise LLMProviderError(
                    f"Generation failed: {str(e)}",
                    provider=self.name,
                    retryable=True,
                )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> dict[str, Any]:
        """Generate structured JSON output."""
        # Add JSON instruction to system prompt
        json_system = system_prompt or ""
        if json_system:
            json_system += "\n\n"
        json_system += "You must respond with valid JSON only. No markdown, no explanation, just the JSON object."

        response = await self.generate(
            prompt=prompt,
            system_prompt=json_system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )

        try:
            # Clean response if needed
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise LLMProviderError(
                f"Failed to parse JSON response: {str(e)}\nResponse: {response[:200]}...",
                provider=self.name,
                retryable=True,
            )

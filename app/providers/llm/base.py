"""Base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging/debugging."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier being used."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        json_mode: bool = False,
    ) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            json_mode: If True, enforce JSON output

        Returns:
            Generated text

        Raises:
            LLMProviderError: If generation fails
        """
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> dict[str, Any]:
        """
        Generate structured JSON output.

        Args:
            prompt: The user prompt (should request JSON output)
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON as dictionary

        Raises:
            LLMProviderError: If generation or parsing fails
        """
        pass


class LLMProviderError(Exception):
    """Exception raised when LLM provider fails."""

    def __init__(self, message: str, provider: str, retryable: bool = True):
        self.message = message
        self.provider = provider
        self.retryable = retryable
        super().__init__(f"[{provider}] {message}")

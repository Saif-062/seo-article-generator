"""LLM provider implementations."""

from app.config import get_settings
from app.providers.llm.base import BaseLLMProvider, LLMProviderError
from app.providers.llm.groq import GroqProvider
from app.providers.llm.mock import MockLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function to get the appropriate LLM provider.

    Returns MockLLMProvider if USE_MOCK_LLM=true or no API key configured.
    Otherwise returns GroqProvider.
    """
    settings = get_settings()

    if settings.use_mock_llm:
        return MockLLMProvider()

    if settings.has_groq_key:
        return GroqProvider()

    # Fallback to mock if no API key
    return MockLLMProvider()


__all__ = [
    "BaseLLMProvider",
    "LLMProviderError",
    "GroqProvider",
    "MockLLMProvider",
    "get_llm_provider",
]

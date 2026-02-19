"""SERP provider implementations."""

from app.config import get_settings
from app.providers.serp.base import BaseSerpProvider, SerpProviderError
from app.providers.serp.mock import MockSerpProvider
from app.providers.serp.serper import SerperProvider


def get_serp_provider() -> BaseSerpProvider:
    """
    Factory function to get the appropriate SERP provider.

    Returns MockSerpProvider if USE_MOCK_SERP=true or no API key configured.
    Otherwise returns SerperProvider.
    """
    settings = get_settings()

    if settings.use_mock_serp:
        return MockSerpProvider()

    if settings.has_serper_key:
        return SerperProvider()

    # Fallback to mock if no API key
    return MockSerpProvider()


__all__ = [
    "BaseSerpProvider",
    "SerpProviderError",
    "SerperProvider",
    "MockSerpProvider",
    "get_serp_provider",
]

"""Base class for SERP providers."""

from abc import ABC, abstractmethod

from app.models.serp import SerpData


class BaseSerpProvider(ABC):
    """Abstract base class for SERP data providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging/debugging."""
        pass

    @abstractmethod
    async def search(self, query: str, num_results: int = 10) -> SerpData:
        """
        Perform a search and return SERP data.

        Args:
            query: The search query
            num_results: Number of results to return (max 10 for most providers)

        Returns:
            SerpData with results, PAA questions, and related searches

        Raises:
            SerpProviderError: If the search fails
        """
        pass


class SerpProviderError(Exception):
    """Exception raised when SERP provider fails."""

    def __init__(self, message: str, provider: str, retryable: bool = True):
        self.message = message
        self.provider = provider
        self.retryable = retryable
        super().__init__(f"[{provider}] {message}")

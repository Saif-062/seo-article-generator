"""Serper.dev SERP provider implementation."""

from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models.serp import PeopleAlsoAsk, SerpData, SerpResult
from app.providers.serp.base import BaseSerpProvider, SerpProviderError


class SerperProvider(BaseSerpProvider):
    """
    SERP provider using Serper.dev API.

    Serper.dev offers 2,500 free searches, making it ideal for this project.
    API docs: https://serper.dev/docs
    """

    BASE_URL = "https://google.serper.dev/search"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_settings().serper_api_key
        if not self.api_key:
            raise SerpProviderError(
                "SERPER_API_KEY not configured",
                provider=self.name,
                retryable=False,
            )

    @property
    def name(self) -> str:
        return "serper.dev"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def search(self, query: str, num_results: int = 10) -> SerpData:
        """
        Search using Serper.dev API.

        Args:
            query: Search query
            num_results: Number of results (max 10)

        Returns:
            SerpData with results, PAA, and related searches
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "q": query,
            "num": min(num_results, 10),
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 401:
                    raise SerpProviderError(
                        "Invalid API key",
                        provider=self.name,
                        retryable=False,
                    )
                elif response.status_code == 429:
                    raise SerpProviderError(
                        "Rate limit exceeded",
                        provider=self.name,
                        retryable=True,
                    )
                elif response.status_code != 200:
                    raise SerpProviderError(
                        f"API error: {response.status_code} - {response.text}",
                        provider=self.name,
                        retryable=response.status_code >= 500,
                    )

                data = response.json()
                return self._parse_response(query, data)

        except httpx.TimeoutException:
            raise SerpProviderError(
                "Request timed out",
                provider=self.name,
                retryable=True,
            )
        except httpx.RequestError as e:
            raise SerpProviderError(
                f"Request failed: {str(e)}",
                provider=self.name,
                retryable=True,
            )

    def _parse_response(self, query: str, data: dict) -> SerpData:
        """Parse Serper.dev response into SerpData."""
        # Parse organic results
        results = []
        for item in data.get("organic", []):
            results.append(
                SerpResult(
                    rank=item.get("position", len(results) + 1),
                    url=item.get("link", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                )
            )

        # Parse People Also Ask
        paa = []
        for item in data.get("peopleAlsoAsk", []):
            paa.append(
                PeopleAlsoAsk(
                    question=item.get("question", ""),
                    snippet=item.get("snippet", ""),
                )
            )

        # Parse related searches
        related = [
            item.get("query", "")
            for item in data.get("relatedSearches", [])
            if item.get("query")
        ]

        return SerpData(
            query=query,
            results=results,
            people_also_ask=paa,
            related_searches=related,
        )

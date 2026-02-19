"""SERP analysis step - fetches and processes search results."""

import logging

from app.models.serp import SerpData
from app.providers.serp.base import BaseSerpProvider

logger = logging.getLogger(__name__)


class SerpAnalysisStep:
    """
    Step 1: Fetch and analyze SERP data.

    This step:
    - Queries the SERP provider for the given topic
    - Returns structured SERP data including results, PAA, and related searches
    """

    def __init__(self, serp_provider: BaseSerpProvider):
        self.serp_provider = serp_provider

    async def execute(self, topic: str, num_results: int = 10) -> SerpData:
        """
        Fetch SERP data for the given topic.

        Args:
            topic: The topic/keyword to search for
            num_results: Number of results to fetch (max 10)

        Returns:
            SerpData with search results and related information
        """
        logger.info(f"Fetching SERP data for: {topic}")

        serp_data = await self.serp_provider.search(
            query=topic,
            num_results=num_results,
        )

        logger.info(
            f"SERP analysis complete: {len(serp_data.results)} results, "
            f"{len(serp_data.people_also_ask)} PAA questions"
        )

        return serp_data

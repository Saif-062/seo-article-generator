"""Theme extraction step - analyzes SERP data to identify themes and intent."""

import json
import logging

from app.models.job import ThemeAnalysis
from app.models.serp import SerpData
from app.providers.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class ThemeExtractionStep:
    """
    Step 2: Extract themes and search intent from SERP data.

    This step:
    - Analyzes SERP titles, snippets, and PAA questions
    - Identifies common themes and patterns
    - Determines search intent
    - Suggests content angles and gaps
    """

    SYSTEM_PROMPT = """You are an SEO content strategist. Analyze search results data to identify:
1. The primary search intent (informational, commercial, transactional, navigational)
2. Common themes and topics covered by top-ranking content
3. Common section headings and content structure patterns
4. Content gaps - topics that should be covered but aren't well addressed
5. Unique angles that could differentiate new content
6. Common questions users are asking (from PAA and implied from content)

Respond with valid JSON only."""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    async def execute(self, topic: str, serp_data: SerpData) -> ThemeAnalysis:
        """
        Extract themes from SERP data.

        Args:
            topic: The original topic/keyword
            serp_data: SERP data from the analysis step

        Returns:
            ThemeAnalysis with extracted themes and insights
        """
        logger.info(f"Extracting themes for: {topic}")

        # Prepare SERP summary for the LLM
        serp_summary = self._prepare_serp_summary(serp_data)

        prompt = f"""Analyze the following search results for the topic "{topic}":

{serp_summary}

Based on this SERP data, provide a JSON response with the following structure:
{{
    "search_intent": "string - primary intent type",
    "primary_themes": ["list of 5-7 main themes/topics covered"],
    "common_sections": ["list of common section headings found across results"],
    "content_gaps": ["list of 2-4 topics that could be better covered"],
    "suggested_angles": ["list of 2-3 unique angles for differentiation"],
    "faq_questions": ["list of 4-6 common questions users are asking"]
}}"""

        response = await self.llm_provider.generate_structured(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=2000,
        )

        # Parse response into ThemeAnalysis
        theme_analysis = ThemeAnalysis(
            search_intent=response.get("search_intent", "informational"),
            primary_themes=response.get("primary_themes", []),
            common_sections=response.get("common_sections", []),
            content_gaps=response.get("content_gaps", []),
            suggested_angles=response.get("suggested_angles", []),
            faq_questions=response.get("faq_questions", []),
        )

        logger.info(
            f"Theme extraction complete: {len(theme_analysis.primary_themes)} themes, "
            f"{len(theme_analysis.faq_questions)} FAQ questions"
        )

        return theme_analysis

    def _prepare_serp_summary(self, serp_data: SerpData) -> str:
        """Prepare a compact summary of SERP data for the LLM."""
        lines = ["## Top 10 Search Results:"]

        for result in serp_data.top_10:
            lines.append(f"\n### Rank {result.rank}: {result.title}")
            lines.append(f"URL: {result.url}")
            lines.append(f"Snippet: {result.snippet}")

        if serp_data.people_also_ask:
            lines.append("\n## People Also Ask:")
            for paa in serp_data.people_also_ask:
                lines.append(f"- {paa.question}")

        if serp_data.related_searches:
            lines.append("\n## Related Searches:")
            for related in serp_data.related_searches:
                lines.append(f"- {related}")

        return "\n".join(lines)

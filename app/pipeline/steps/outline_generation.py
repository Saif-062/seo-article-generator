"""Outline generation step - creates article structure using LLM."""

import json
import logging

from app.models.article import ArticleOutline, OutlineSection
from app.models.job import ThemeAnalysis
from app.providers.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OutlineGenerationStep:
    """
    Step 3: Generate article outline based on theme analysis.

    This step:
    - Creates a structured outline with H1/H2/H3 hierarchy
    - Allocates target word counts per section
    - Includes FAQ section based on common questions
    - Ensures coverage of key themes
    """

    SYSTEM_PROMPT = """You are an expert content strategist creating SEO-optimized article outlines.

Your outlines should:
1. Have a compelling H1 title with the primary keyword
2. Include 6-8 main H2 sections covering the topic comprehensively
3. Use H3 subsections where appropriate for detailed topics
4. Include a FAQ section at the end with 4-5 questions
5. Allocate word counts that total to the target
6. Follow a logical flow that matches search intent

Respond with valid JSON only."""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    async def execute(
        self,
        topic: str,
        theme_analysis: ThemeAnalysis,
        word_count: int = 1500,
        language: str = "en",
    ) -> ArticleOutline:
        """
        Generate an article outline.

        Args:
            topic: The article topic
            theme_analysis: Extracted themes from SERP analysis
            word_count: Target word count for the article
            language: Language code for the article

        Returns:
            ArticleOutline with sections and word allocations
        """
        logger.info(f"Generating outline for: {topic} ({word_count} words)")

        prompt = f"""Create a detailed article outline for the topic: "{topic}"

Target word count: {word_count}
Language: {language}

## Theme Analysis:
- Search Intent: {theme_analysis.search_intent}
- Primary Themes: {', '.join(theme_analysis.primary_themes[:5])}
- Common Sections: {', '.join(theme_analysis.common_sections[:8])}
- Content Gaps to Address: {', '.join(theme_analysis.content_gaps)}
- FAQ Questions: {', '.join(theme_analysis.faq_questions[:5])}

Create a JSON outline with this structure:
{{
    "title": "H1 title for the article (include primary keyword)",
    "sections": [
        {{
            "heading": "H2 section heading",
            "level": 2,
            "target_words": 200,
            "key_points": ["point 1", "point 2"],
            "subsections": [
                {{
                    "heading": "H3 subsection",
                    "level": 3,
                    "target_words": 100,
                    "key_points": ["point"]
                }}
            ]
        }}
    ],
    "faq_questions": ["Question 1?", "Question 2?"],
    "total_target_words": {word_count}
}}

Include:
- Introduction section
- 4-6 main content sections (H2)
- 2-4 subsections (H3) where appropriate
- FAQ section
- Conclusion

Allocate word counts realistically to match the {word_count} word target."""

        response = await self.llm_provider.generate_structured(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.5,
            max_tokens=3000,
        )

        # Parse response into ArticleOutline
        outline = self._parse_outline(response, word_count)

        logger.info(
            f"Outline generated: {len(outline.sections)} sections, "
            f"{outline.total_target_words} target words"
        )

        return outline

    def _parse_outline(self, response: dict, target_words: int) -> ArticleOutline:
        """Parse LLM response into ArticleOutline model."""
        sections = []

        for section_data in response.get("sections", []):
            subsections = []
            for sub_data in section_data.get("subsections", []):
                subsections.append(
                    OutlineSection(
                        heading=sub_data.get("heading", ""),
                        level=sub_data.get("level", 3),
                        target_words=sub_data.get("target_words", 100),
                        key_points=sub_data.get("key_points", []),
                    )
                )

            sections.append(
                OutlineSection(
                    heading=section_data.get("heading", ""),
                    level=section_data.get("level", 2),
                    target_words=section_data.get("target_words", 200),
                    key_points=section_data.get("key_points", []),
                    subsections=subsections,
                )
            )

        return ArticleOutline(
            title=response.get("title", ""),
            sections=sections,
            faq_questions=response.get("faq_questions", []),
            total_target_words=response.get("total_target_words", target_words),
        )

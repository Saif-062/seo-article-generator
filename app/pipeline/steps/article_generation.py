"""Article generation step - generates full article content using LLM."""

from __future__ import annotations

import logging

from app.models.article import ArticleOutline
from app.models.job import ThemeAnalysis
from app.providers.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class ArticleGenerationStep:
    """
    Step 4: Generate full article content.

    This step:
    - Generates a complete article following the outline
    - Follows SEO best practices (keyword placement, heading structure)
    - Includes the FAQ section
    - Produces natural, human-readable content
    """

    SYSTEM_PROMPT = """You are an expert content writer creating SEO-optimized articles.

Your articles should:
1. Follow the provided outline exactly (maintain heading hierarchy)
2. Use markdown formatting with proper headings (# for H1, ## for H2, ### for H3)
3. Include the primary keyword in the title, first paragraph, and at least one heading
4. Write naturally - the content should read like a human expert wrote it
5. Be comprehensive and provide real value to readers
6. Include smooth transitions between sections
7. Use bullet points and lists where appropriate for readability
8. Include a FAQ section at the end with proper formatting
9. End with a conclusion that summarizes key points

Do NOT:
- Stuff keywords unnaturally
- Use generic filler content
- Include placeholder text like [insert here]
- Be overly promotional or salesy

Output the full article in markdown format."""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    async def execute(
        self,
        topic: str,
        outline: ArticleOutline,
        theme_analysis: ThemeAnalysis | None,
        word_count: int = 1500,
        language: str = "en",
    ) -> str:
        """
        Generate the full article content.

        Args:
            topic: The article topic
            outline: The article outline to follow
            theme_analysis: Theme analysis for context (optional)
            word_count: Target word count
            language: Language code

        Returns:
            Full article in markdown format
        """
        logger.info(f"Generating article for: {topic} ({word_count} words)")

        # Format outline for the prompt
        outline_text = self._format_outline(outline)

        # Build context from theme analysis
        context = ""
        if theme_analysis:
            context = f"""
## Content Context:
- Search Intent: {theme_analysis.search_intent}
- Key Themes to Cover: {', '.join(theme_analysis.primary_themes[:5])}
- Questions to Answer: {', '.join(theme_analysis.faq_questions[:4])}
"""

        prompt = f"""Write a complete, publish-ready article on: "{topic}"

Target word count: {word_count} words
Language: {language}

## Article Outline to Follow:
{outline_text}
{context}

## Requirements:
1. Follow the outline structure exactly
2. Use proper markdown: # for H1, ## for H2, ### for H3
3. Include the primary keyword "{topic}" in:
   - The title (H1)
   - The first paragraph
   - At least one H2 heading
   - Naturally throughout the content
4. Write approximately {word_count} words total
5. Make content informative, engaging, and valuable
6. Include the FAQ section with proper Q&A formatting
7. End with a compelling conclusion

Write the complete article now in markdown format:"""

        article = await self.llm_provider.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=8000,
        )

        # Count words
        word_count_actual = len(article.split())
        logger.info(f"Article generated: {word_count_actual} words")

        return article

    def _format_outline(self, outline: ArticleOutline) -> str:
        """Format outline for the prompt."""
        lines = [f"# {outline.title}"]

        for section in outline.sections:
            prefix = "#" * section.level
            lines.append(f"\n{prefix} {section.heading}")

            if section.key_points:
                for point in section.key_points:
                    lines.append(f"- {point}")

            for subsection in section.subsections:
                sub_prefix = "#" * subsection.level
                lines.append(f"\n{sub_prefix} {subsection.heading}")
                if subsection.key_points:
                    for point in subsection.key_points:
                        lines.append(f"- {point}")

        if outline.faq_questions:
            lines.append("\n## Frequently Asked Questions")
            for q in outline.faq_questions:
                lines.append(f"- {q}")

        return "\n".join(lines)

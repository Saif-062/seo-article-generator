"""SEO validation step - validates article and triggers revisions if needed."""

import logging
import re
from typing import Any

from app.config import get_settings
from app.models.article import (
    ArticleOutline,
    ExternalReference,
    GeneratedArticle,
    HeadingNode,
    InternalLink,
    KeywordAnalysis,
    SEOMetadata,
    SEOValidationCheck,
    SEOValidationResult,
)
from app.providers.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class SEOValidationStep:
    """
    Step 5: Validate SEO requirements and package final article.

    This step:
    - Validates the article against SEO criteria
    - Extracts SEO metadata (title, description, keywords)
    - Analyzes keyword usage
    - Generates internal/external link suggestions
    - Optionally triggers revision if validation fails
    """

    MAX_REVISIONS = 2

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider
        self.settings = get_settings()

    async def execute(
        self,
        draft_article: str,
        outline: ArticleOutline,
        topic: str,
        target_word_count: int,
    ) -> GeneratedArticle:
        """
        Validate article and package final output.

        Args:
            draft_article: The draft article in markdown
            outline: The article outline
            topic: The original topic
            target_word_count: Target word count

        Returns:
            GeneratedArticle with all metadata and validation
        """
        logger.info("Starting SEO validation")

        article = draft_article
        revision_count = 0

        while revision_count < self.MAX_REVISIONS:
            # Run validation
            validation = self._validate_article(article, topic, target_word_count)

            if validation.passed:
                logger.info(f"SEO validation passed (score: {validation.score})")
                break

            # Attempt revision if validation failed
            revision_count += 1
            logger.info(
                f"SEO validation failed (score: {validation.score}), "
                f"attempting revision {revision_count}/{self.MAX_REVISIONS}"
            )

            article = await self._revise_article(article, validation.issues, topic)

        # Final validation
        validation = self._validate_article(article, topic, target_word_count)

        # Extract metadata and build final package
        seo_metadata = await self._extract_metadata(article, topic, outline)
        keyword_analysis = self._analyze_keywords(article, topic)
        heading_structure = self._extract_headings(article)
        internal_links = await self._suggest_internal_links(article, topic)
        external_refs = await self._suggest_external_refs(article, topic)

        return GeneratedArticle(
            article_markdown=article,
            heading_structure=heading_structure,
            seo_metadata=seo_metadata,
            keyword_analysis=keyword_analysis,
            internal_links=internal_links,
            external_references=external_refs,
            seo_validation=validation,
            word_count=len(article.split()),
        )

    def _validate_article(
        self,
        article: str,
        topic: str,
        target_word_count: int,
    ) -> SEOValidationResult:
        """Run SEO validation checks on the article."""
        checks = []
        issues = []

        # Word count check
        word_count = len(article.split())
        min_words = int(target_word_count * self.settings.min_word_count_tolerance)
        max_words = int(target_word_count * self.settings.max_word_count_tolerance)

        if min_words <= word_count <= max_words:
            checks.append(SEOValidationCheck(
                name="word_count",
                passed=True,
                message=f"Word count ({word_count}) is within target range",
            ))
        else:
            checks.append(SEOValidationCheck(
                name="word_count",
                passed=False,
                message=f"Word count ({word_count}) outside target range ({min_words}-{max_words})",
                severity="warning",
            ))
            issues.append(f"Adjust word count to {target_word_count} words (currently {word_count})")

        # H1 check (exactly one)
        h1_matches = re.findall(r"^# [^#]", article, re.MULTILINE)
        h1_count = len(h1_matches)

        if h1_count == 1:
            checks.append(SEOValidationCheck(
                name="single_h1",
                passed=True,
                message="Article has exactly one H1",
            ))
        else:
            checks.append(SEOValidationCheck(
                name="single_h1",
                passed=False,
                message=f"Article has {h1_count} H1 headings (should be exactly 1)",
                severity="error",
            ))
            issues.append("Ensure exactly one H1 heading at the start of the article")

        # H2 count check
        h2_matches = re.findall(r"^## [^#]", article, re.MULTILINE)
        h2_count = len(h2_matches)

        if h2_count >= self.settings.min_h2_count:
            checks.append(SEOValidationCheck(
                name="h2_count",
                passed=True,
                message=f"Article has {h2_count} H2 headings",
            ))
        else:
            checks.append(SEOValidationCheck(
                name="h2_count",
                passed=False,
                message=f"Article has only {h2_count} H2 headings (minimum {self.settings.min_h2_count})",
                severity="warning",
            ))
            issues.append(f"Add more H2 sections (currently {h2_count}, need {self.settings.min_h2_count}+)")

        # H3 check
        h3_matches = re.findall(r"^### [^#]", article, re.MULTILINE)
        h3_count = len(h3_matches)

        if h3_count >= self.settings.min_h3_count:
            checks.append(SEOValidationCheck(
                name="h3_count",
                passed=True,
                message=f"Article has {h3_count} H3 headings",
            ))
        else:
            checks.append(SEOValidationCheck(
                name="h3_count",
                passed=False,
                message=f"Article has only {h3_count} H3 headings (minimum {self.settings.min_h3_count})",
                severity="info",
            ))

        # Keyword in title check
        topic_lower = topic.lower()
        title_match = re.search(r"^# (.+)$", article, re.MULTILINE)
        title = title_match.group(1) if title_match else ""

        if topic_lower in title.lower():
            checks.append(SEOValidationCheck(
                name="keyword_in_title",
                passed=True,
                message="Primary keyword appears in title",
            ))
        else:
            checks.append(SEOValidationCheck(
                name="keyword_in_title",
                passed=False,
                message="Primary keyword not found in title",
                severity="error",
            ))
            issues.append(f"Include '{topic}' in the H1 title")

        # Keyword in first 100 words
        first_100_words = " ".join(article.split()[:100]).lower()
        if topic_lower in first_100_words:
            checks.append(SEOValidationCheck(
                name="keyword_in_intro",
                passed=True,
                message="Primary keyword appears in introduction",
            ))
        else:
            checks.append(SEOValidationCheck(
                name="keyword_in_intro",
                passed=False,
                message="Primary keyword not in first 100 words",
                severity="warning",
            ))
            issues.append(f"Include '{topic}' in the first paragraph")

        # Keyword density check
        article_lower = article.lower()
        keyword_count = article_lower.count(topic_lower)
        keyword_density = keyword_count / word_count if word_count > 0 else 0

        if keyword_density <= self.settings.max_keyword_density:
            checks.append(SEOValidationCheck(
                name="keyword_density",
                passed=True,
                message=f"Keyword density ({keyword_density:.1%}) is acceptable",
            ))
        else:
            checks.append(SEOValidationCheck(
                name="keyword_density",
                passed=False,
                message=f"Keyword density ({keyword_density:.1%}) too high (max {self.settings.max_keyword_density:.1%})",
                severity="warning",
            ))
            issues.append("Reduce keyword repetition to avoid stuffing")

        # Calculate overall score
        passed_count = sum(1 for c in checks if c.passed)
        score = (passed_count / len(checks)) * 100 if checks else 0

        # Determine if passed (no errors, score >= 70)
        has_errors = any(not c.passed and c.severity == "error" for c in checks)
        passed = not has_errors and score >= 70

        return SEOValidationResult(
            passed=passed,
            score=score,
            checks=checks,
            issues=issues,
        )

    async def _revise_article(
        self,
        article: str,
        issues: list[str],
        topic: str,
    ) -> str:
        """Use LLM to revise article based on issues."""
        issues_text = "\n".join(f"- {issue}" for issue in issues)

        prompt = f"""Revise the following article to fix these SEO issues:

{issues_text}

## Current Article:
{article}

## Instructions:
1. Fix all the listed issues
2. Maintain the same structure and tone
3. Keep the content quality high
4. Do not add unnecessary content
5. Return the complete revised article in markdown

Write the revised article:"""

        revised = await self.llm_provider.generate(
            prompt=prompt,
            system_prompt="You are an SEO editor. Fix the issues while maintaining content quality.",
            temperature=0.5,
            max_tokens=8000,
        )

        return revised

    async def _extract_metadata(
        self,
        article: str,
        topic: str,
        outline: ArticleOutline,
    ) -> SEOMetadata:
        """Extract SEO metadata from the article."""
        # Extract title from H1
        title_match = re.search(r"^# (.+)$", article, re.MULTILINE)
        title = title_match.group(1) if title_match else outline.title

        # Generate meta description using LLM
        prompt = f"""Based on this article about "{topic}", generate SEO metadata:

Article title: {title}

First 500 words of article:
{' '.join(article.split()[:500])}

Provide JSON with:
{{
    "title_tag": "SEO title (50-60 chars, include primary keyword)",
    "meta_description": "Meta description (120-160 chars, compelling, include keyword)",
    "slug": "url-friendly-slug",
    "primary_keyword": "main keyword",
    "secondary_keywords": ["keyword1", "keyword2", "keyword3"]
}}"""

        response = await self.llm_provider.generate_structured(
            prompt=prompt,
            system_prompt="You are an SEO specialist creating metadata.",
            temperature=0.3,
            max_tokens=500,
        )

        return SEOMetadata(
            title_tag=response.get("title_tag", title[:60]),
            meta_description=response.get("meta_description", "")[:160],
            slug=response.get("slug", topic.lower().replace(" ", "-")),
            primary_keyword=response.get("primary_keyword", topic),
            secondary_keywords=response.get("secondary_keywords", []),
        )

    def _analyze_keywords(self, article: str, topic: str) -> KeywordAnalysis:
        """Analyze keyword usage in the article."""
        article_lower = article.lower()
        word_count = len(article.split())

        # Count primary keyword
        primary_count = article_lower.count(topic.lower())
        primary_density = primary_count / word_count if word_count > 0 else 0

        # Extract potential secondary keywords (simple approach)
        words = topic.lower().split()
        secondary_keywords = words if len(words) > 1 else []
        secondary_counts = {kw: article_lower.count(kw) for kw in secondary_keywords}

        return KeywordAnalysis(
            primary_keyword=topic,
            primary_count=primary_count,
            primary_density=primary_density,
            secondary_keywords=secondary_keywords,
            secondary_counts=secondary_counts,
        )

    def _extract_headings(self, article: str) -> list[HeadingNode]:
        """Extract heading structure from the article."""
        headings = []

        for match in re.finditer(r"^(#{1,6}) (.+)$", article, re.MULTILINE):
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append(HeadingNode(level=level, text=text))

        return headings

    async def _suggest_internal_links(
        self,
        article: str,
        topic: str,
    ) -> list[InternalLink]:
        """Generate internal link suggestions."""
        prompt = f"""Analyze this article about "{topic}" and suggest 3-5 internal links.

Article excerpt:
{' '.join(article.split()[:800])}

For each link, identify:
1. A phrase in the article that could be anchor text
2. A related topic/page it should link to
3. Where in the article this link would fit

Provide JSON array:
[
    {{
        "anchor_text": "phrase to use as link text",
        "target_topic": "related topic or page",
        "placement_hint": "section where this fits"
    }}
]

Return 3-5 link suggestions."""

        response = await self.llm_provider.generate_structured(
            prompt=prompt,
            system_prompt="You are an SEO specialist creating internal linking strategies.",
            temperature=0.3,
            max_tokens=1000,
        )

        links = []
        if isinstance(response, list):
            for item in response[:5]:
                links.append(InternalLink(
                    anchor_text=item.get("anchor_text", ""),
                    target_topic=item.get("target_topic", ""),
                    placement_hint=item.get("placement_hint", ""),
                ))
        elif isinstance(response, dict) and "links" in response:
            for item in response["links"][:5]:
                links.append(InternalLink(
                    anchor_text=item.get("anchor_text", ""),
                    target_topic=item.get("target_topic", ""),
                    placement_hint=item.get("placement_hint", ""),
                ))

        return links

    async def _suggest_external_refs(
        self,
        article: str,
        topic: str,
    ) -> list[ExternalReference]:
        """Generate external reference suggestions."""
        prompt = f"""Suggest 2-4 authoritative external sources to cite in this article about "{topic}".

Article excerpt:
{' '.join(article.split()[:600])}

For each source, suggest:
1. Type of source (study, report, publication)
2. Name of authority/publication
3. Why it would add credibility
4. Where in the article to place the citation

Provide JSON array:
[
    {{
        "url": "example: https://example.com/study",
        "source_name": "Name of source",
        "why_authoritative": "Why this adds credibility",
        "placement_hint": "Section where citation fits"
    }}
]

Return 2-4 suggestions."""

        response = await self.llm_provider.generate_structured(
            prompt=prompt,
            system_prompt="You are an SEO specialist identifying authoritative sources.",
            temperature=0.3,
            max_tokens=1000,
        )

        refs = []
        if isinstance(response, list):
            for item in response[:4]:
                refs.append(ExternalReference(
                    url=item.get("url", ""),
                    source_name=item.get("source_name", ""),
                    why_authoritative=item.get("why_authoritative", ""),
                    placement_hint=item.get("placement_hint", ""),
                ))
        elif isinstance(response, dict) and "references" in response:
            for item in response["references"][:4]:
                refs.append(ExternalReference(
                    url=item.get("url", ""),
                    source_name=item.get("source_name", ""),
                    why_authoritative=item.get("why_authoritative", ""),
                    placement_hint=item.get("placement_hint", ""),
                ))

        return refs

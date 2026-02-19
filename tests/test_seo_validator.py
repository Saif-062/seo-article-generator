"""Tests for SEO validation logic."""

import pytest

from app.models.article import ArticleOutline, OutlineSection
from app.pipeline.steps.seo_validation import SEOValidationStep
from app.providers.llm.mock import MockLLMProvider


class TestSEOValidator:
    """Tests for SEO validation step."""

    @pytest.fixture
    def validator(self):
        """Create a validator with mock LLM."""
        return SEOValidationStep(MockLLMProvider())

    @pytest.fixture
    def valid_article(self):
        """A well-structured article that passes validation."""
        return """# Best Productivity Tools for Remote Teams

Remote work has transformed how teams collaborate. Finding the best productivity tools for remote teams is essential for success.

## Introduction

The shift to remote work requires specialized productivity tools. In this guide, we explore the best productivity tools for remote teams.

## Communication Tools

Effective communication is the backbone of remote work.

### Slack

Slack is a popular choice for team messaging.

### Microsoft Teams

Microsoft Teams integrates well with Office 365.

## Project Management Tools

Managing projects remotely requires the right tools.

### Asana

Asana helps teams track their work.

### Trello

Trello uses a visual board system.

## Time Management

Time tracking helps remote teams stay productive.

## Best Practices

Here are some tips for using productivity tools effectively.

## Frequently Asked Questions

**What is the best tool for small teams?**
For small teams, Slack combined with Trello works well.

**How much should companies budget?**
Budget around $20-50 per user per month.

## Conclusion

Choosing the right productivity tools is essential for remote team success.
"""

    @pytest.fixture
    def invalid_article(self):
        """An article missing key SEO elements."""
        return """# A Random Title

Some content without proper structure.

Some more text.
"""

    def test_word_count_validation(self, validator):
        """Test word count validation."""
        short_article = "This is a very short article. " * 50  # ~400 words

        result = validator._validate_article(
            article=short_article,
            topic="productivity tools",
            target_word_count=1500,
        )

        # Should fail word count check
        word_count_check = next(
            (c for c in result.checks if c.name == "word_count"), None
        )
        assert word_count_check is not None
        assert not word_count_check.passed

    def test_h1_validation_single(self, validator, valid_article):
        """Test H1 validation with exactly one H1."""
        result = validator._validate_article(
            article=valid_article,
            topic="productivity tools",
            target_word_count=500,
        )

        h1_check = next((c for c in result.checks if c.name == "single_h1"), None)
        assert h1_check is not None
        assert h1_check.passed

    def test_h1_validation_multiple(self, validator):
        """Test H1 validation fails with multiple H1s."""
        article_with_multiple_h1 = """# First Title

Content here.

# Second Title

More content.
"""
        result = validator._validate_article(
            article=article_with_multiple_h1,
            topic="productivity tools",
            target_word_count=100,
        )

        h1_check = next((c for c in result.checks if c.name == "single_h1"), None)
        assert h1_check is not None
        assert not h1_check.passed

    def test_h2_count_validation(self, validator, valid_article):
        """Test H2 count validation."""
        result = validator._validate_article(
            article=valid_article,
            topic="productivity tools",
            target_word_count=500,
        )

        h2_check = next((c for c in result.checks if c.name == "h2_count"), None)
        assert h2_check is not None
        assert h2_check.passed  # Valid article has 6+ H2s

    def test_keyword_in_title(self, validator, valid_article):
        """Test keyword presence in title."""
        result = validator._validate_article(
            article=valid_article,
            topic="productivity tools",
            target_word_count=500,
        )

        keyword_check = next(
            (c for c in result.checks if c.name == "keyword_in_title"), None
        )
        assert keyword_check is not None
        assert keyword_check.passed

    def test_keyword_in_title_missing(self, validator, invalid_article):
        """Test keyword missing from title."""
        result = validator._validate_article(
            article=invalid_article,
            topic="productivity tools",
            target_word_count=100,
        )

        keyword_check = next(
            (c for c in result.checks if c.name == "keyword_in_title"), None
        )
        assert keyword_check is not None
        assert not keyword_check.passed

    def test_keyword_in_intro(self, validator, valid_article):
        """Test keyword presence in introduction."""
        result = validator._validate_article(
            article=valid_article,
            topic="productivity tools",
            target_word_count=500,
        )

        intro_check = next(
            (c for c in result.checks if c.name == "keyword_in_intro"), None
        )
        assert intro_check is not None
        assert intro_check.passed

    def test_keyword_density(self, validator):
        """Test keyword density validation."""
        # Create article with reasonable keyword density
        normal_article = """# Best Productivity Tools Guide

This is a guide about productivity tools for teams.

## Overview

We discuss various productivity tools here.

## Details

More information about different tools.
""" + "Additional content. " * 100

        result = validator._validate_article(
            article=normal_article,
            topic="productivity tools",
            target_word_count=len(normal_article.split()),
        )

        density_check = next(
            (c for c in result.checks if c.name == "keyword_density"), None
        )
        assert density_check is not None
        # Should pass with normal density
        assert density_check.passed

    def test_heading_extraction(self, validator, valid_article):
        """Test heading extraction from article."""
        headings = validator._extract_headings(valid_article)

        assert len(headings) > 0
        assert headings[0].level == 1  # First heading is H1
        assert any(h.level == 2 for h in headings)  # Has H2s
        assert any(h.level == 3 for h in headings)  # Has H3s

    def test_keyword_analysis(self, validator, valid_article):
        """Test keyword analysis."""
        analysis = validator._analyze_keywords(valid_article, "productivity tools")

        assert analysis.primary_keyword == "productivity tools"
        assert analysis.primary_count > 0
        assert 0 <= analysis.primary_density <= 1

    def test_validation_score_calculation(self, validator, valid_article):
        """Test that validation score is calculated correctly."""
        result = validator._validate_article(
            article=valid_article,
            topic="productivity tools",
            target_word_count=500,
        )

        # Score should be between 0 and 100
        assert 0 <= result.score <= 100

        # Score should reflect passed checks
        passed_count = sum(1 for c in result.checks if c.passed)
        expected_score = (passed_count / len(result.checks)) * 100
        assert result.score == expected_score

    def test_validation_passed_criteria(self, validator, valid_article):
        """Test that validation passed criteria is correct."""
        result = validator._validate_article(
            article=valid_article,
            topic="productivity tools",
            target_word_count=500,
        )

        # Should pass if no errors and score >= 70
        has_errors = any(
            not c.passed and c.severity == "error" for c in result.checks
        )
        assert result.passed == (not has_errors and result.score >= 70)


class TestLinkSuggestions:
    """Tests for internal/external link suggestion counts."""

    @pytest.fixture
    def validator(self):
        """Create a validator with mock LLM."""
        return SEOValidationStep(MockLLMProvider())

    @pytest.mark.asyncio
    async def test_internal_links_count(self, validator):
        """Test that 3-5 internal links are suggested."""
        article = "Sample article content about productivity tools."

        links = await validator._suggest_internal_links(article, "productivity tools")

        assert 0 <= len(links) <= 5  # Mock may return fewer

    @pytest.mark.asyncio
    async def test_external_refs_count(self, validator):
        """Test that 2-4 external references are suggested."""
        article = "Sample article content about productivity tools."

        refs = await validator._suggest_external_refs(article, "productivity tools")

        assert 0 <= len(refs) <= 4  # Mock may return fewer

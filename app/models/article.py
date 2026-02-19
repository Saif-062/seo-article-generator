"""Article and SEO output models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SEOMetadata(BaseModel):
    """SEO metadata for the article."""

    title_tag: str = Field(..., description="Title tag for SEO (50-60 chars ideal)")
    meta_description: str = Field(..., description="Meta description (120-160 chars)")
    slug: str = Field(..., description="URL-friendly slug")
    primary_keyword: str = Field(..., description="Primary target keyword")
    secondary_keywords: list[str] = Field(default_factory=list, description="Secondary keywords")


class KeywordAnalysis(BaseModel):
    """Keyword usage analysis for the article."""

    primary_keyword: str
    primary_count: int = 0
    primary_density: float = 0.0
    secondary_keywords: list[str] = Field(default_factory=list)
    secondary_counts: dict[str, int] = Field(default_factory=dict)


class InternalLink(BaseModel):
    """Suggested internal link."""

    anchor_text: str = Field(..., description="The clickable text")
    target_topic: str = Field(..., description="Topic/page to link to")
    placement_hint: str = Field(..., description="Where in article to place this link")


class ExternalReference(BaseModel):
    """Suggested external citation/reference."""

    url: str = Field(..., description="URL to cite")
    source_name: str = Field(..., description="Name of the source")
    why_authoritative: str = Field(..., description="Why this source adds credibility")
    placement_hint: str = Field(..., description="Where in article to place this citation")


class HeadingNode(BaseModel):
    """A heading in the article structure."""

    level: int = Field(..., ge=1, le=6, description="Heading level (1-6)")
    text: str = Field(..., description="Heading text")
    target_words: int = Field(default=0, description="Target word count for this section")


class OutlineSection(BaseModel):
    """A section in the article outline."""

    heading: str
    level: int = 2  # H2 by default
    target_words: int = 200
    subsections: list["OutlineSection"] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)


class ArticleOutline(BaseModel):
    """Complete article outline."""

    title: str
    sections: list[OutlineSection]
    faq_questions: list[str] = Field(default_factory=list)
    total_target_words: int = 1500


class SEOValidationCheck(BaseModel):
    """A single SEO validation check."""

    name: str
    passed: bool
    message: str
    severity: str = "warning"  # "error", "warning", "info"


class SEOValidationResult(BaseModel):
    """Complete SEO validation results."""

    passed: bool = False
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    checks: list[SEOValidationCheck] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.severity == "warning")


class GeneratedArticle(BaseModel):
    """The complete generated article package."""

    # Article content
    article_markdown: str = Field(..., description="Full article in markdown")
    heading_structure: list[HeadingNode] = Field(
        default_factory=list, description="Extracted heading hierarchy"
    )

    # SEO metadata
    seo_metadata: SEOMetadata

    # Keyword analysis
    keyword_analysis: KeywordAnalysis

    # Linking
    internal_links: list[InternalLink] = Field(default_factory=list)
    external_references: list[ExternalReference] = Field(default_factory=list)

    # Validation
    seo_validation: SEOValidationResult

    # Word count
    word_count: int = 0

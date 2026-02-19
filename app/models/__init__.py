"""Data models for the SEO article generator."""

from app.models.article import (
    ArticleOutline,
    ExternalReference,
    GeneratedArticle,
    HeadingNode,
    InternalLink,
    KeywordAnalysis,
    OutlineSection,
    SEOMetadata,
    SEOValidationCheck,
    SEOValidationResult,
)
from app.models.job import (
    Job,
    JobArtifacts,
    JobError,
    JobInput,
    JobStatus,
    PipelineStep,
    ThemeAnalysis,
)
from app.models.serp import PageSignals, PeopleAlsoAsk, SerpData, SerpResult

__all__ = [
    # SERP
    "SerpResult",
    "PeopleAlsoAsk",
    "SerpData",
    "PageSignals",
    # Article
    "SEOMetadata",
    "KeywordAnalysis",
    "InternalLink",
    "ExternalReference",
    "HeadingNode",
    "OutlineSection",
    "ArticleOutline",
    "SEOValidationCheck",
    "SEOValidationResult",
    "GeneratedArticle",
    # Job
    "JobStatus",
    "PipelineStep",
    "JobInput",
    "ThemeAnalysis",
    "JobArtifacts",
    "JobError",
    "Job",
]

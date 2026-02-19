"""Job state and persistence models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.article import ArticleOutline, GeneratedArticle
from app.models.serp import PageSignals, SerpData


class JobStatus(str, Enum):
    """Job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStep(str, Enum):
    """Pipeline execution steps."""

    CREATED = "created"
    SERP_ANALYSIS = "serp_analysis"
    THEME_EXTRACTION = "theme_extraction"
    OUTLINE_GENERATION = "outline_generation"
    ARTICLE_GENERATION = "article_generation"
    SEO_VALIDATION = "seo_validation"
    COMPLETED = "completed"


class JobInput(BaseModel):
    """Input parameters for article generation."""

    topic: str = Field(..., min_length=3, max_length=500, description="Topic or primary keyword")
    word_count: int = Field(default=1500, ge=500, le=5000, description="Target word count")
    language: str = Field(default="en", description="Language code (e.g., 'en', 'es', 'de')")


class ThemeAnalysis(BaseModel):
    """Extracted themes and intent from SERP analysis."""

    search_intent: str = Field(..., description="Detected search intent type")
    primary_themes: list[str] = Field(default_factory=list, description="Main themes found")
    common_sections: list[str] = Field(default_factory=list, description="Common section headings")
    content_gaps: list[str] = Field(default_factory=list, description="Topics not well covered")
    suggested_angles: list[str] = Field(default_factory=list, description="Unique angles to explore")
    faq_questions: list[str] = Field(default_factory=list, description="Common questions found")


class JobArtifacts(BaseModel):
    """Artifacts produced during pipeline execution."""

    serp_data: SerpData | None = None
    page_signals: list[PageSignals] = Field(default_factory=list)
    theme_analysis: ThemeAnalysis | None = None
    outline: ArticleOutline | None = None
    draft_article: str | None = None
    final_article: GeneratedArticle | None = None


class JobError(BaseModel):
    """Error information for failed jobs."""

    step: PipelineStep
    message: str
    details: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Job(BaseModel):
    """Complete job state for persistence and tracking."""

    job_id: str = Field(..., description="Unique job identifier")
    input: JobInput
    status: JobStatus = JobStatus.PENDING
    current_step: PipelineStep = PipelineStep.CREATED

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    # Artifacts and results
    artifacts: JobArtifacts = Field(default_factory=JobArtifacts)

    # Error tracking
    error: JobError | None = None
    retry_count: int = 0

    def mark_step(self, step: PipelineStep) -> None:
        """Update current step and timestamp."""
        self.current_step = step
        self.updated_at = datetime.utcnow()
        if step == PipelineStep.COMPLETED:
            self.status = JobStatus.COMPLETED
            self.completed_at = datetime.utcnow()

    def mark_failed(self, step: PipelineStep, message: str, details: str | None = None) -> None:
        """Mark job as failed with error info."""
        self.status = JobStatus.FAILED
        self.error = JobError(step=step, message=message, details=details)
        self.updated_at = datetime.utcnow()

    def mark_running(self) -> None:
        """Mark job as running."""
        self.status = JobStatus.RUNNING
        self.updated_at = datetime.utcnow()

    class Config:
        use_enum_values = True

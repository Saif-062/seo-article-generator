"""API request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.article import GeneratedArticle
from app.models.job import JobStatus, PipelineStep


class CreateJobRequest(BaseModel):
    """Request to create a new article generation job."""

    topic: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Topic or primary keyword for the article",
        json_schema_extra={"example": "best productivity tools for remote teams"},
    )
    word_count: int = Field(
        default=1500,
        ge=500,
        le=5000,
        description="Target word count for the article",
    )
    language: str = Field(
        default="en",
        description="Language code for the article",
        json_schema_extra={"example": "en"},
    )


class JobStatusResponse(BaseModel):
    """Response showing job status."""

    job_id: str
    status: JobStatus
    current_step: PipelineStep
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None

    class Config:
        use_enum_values = True


class JobResultResponse(BaseModel):
    """Response with complete job results."""

    job_id: str
    status: JobStatus
    current_step: PipelineStep
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    # Input echo
    topic: str
    word_count: int
    language: str

    # Results (only present when completed)
    article: GeneratedArticle | None = None

    # Error info (only present when failed)
    error_message: str | None = None
    error_step: str | None = None

    class Config:
        use_enum_values = True


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    serp_provider: str
    llm_provider: str

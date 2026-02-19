"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from app.models.article import (
    GeneratedArticle,
    HeadingNode,
    InternalLink,
    KeywordAnalysis,
    SEOMetadata,
    SEOValidationResult,
)
from app.models.job import Job, JobInput, JobStatus, PipelineStep
from app.models.serp import SerpData, SerpResult


class TestSerpModels:
    """Tests for SERP data models."""

    def test_serp_result_valid(self):
        """Test creating a valid SERP result."""
        result = SerpResult(
            rank=1,
            url="https://example.com",
            title="Test Title",
            snippet="Test snippet",
        )
        assert result.rank == 1
        assert result.url == "https://example.com"

    def test_serp_result_rank_validation(self):
        """Test that rank must be between 1 and 100."""
        with pytest.raises(ValidationError):
            SerpResult(rank=0, url="https://example.com", title="Test")

        with pytest.raises(ValidationError):
            SerpResult(rank=101, url="https://example.com", title="Test")

    def test_serp_data_top_10(self):
        """Test the top_10 property."""
        results = [
            SerpResult(rank=i, url=f"https://example{i}.com", title=f"Title {i}")
            for i in range(1, 15)
        ]
        serp_data = SerpData(query="test", results=results)

        assert len(serp_data.top_10) == 10
        assert serp_data.top_10[0].rank == 1


class TestJobModels:
    """Tests for job data models."""

    def test_job_input_valid(self):
        """Test creating valid job input."""
        job_input = JobInput(
            topic="best productivity tools",
            word_count=1500,
            language="en",
        )
        assert job_input.topic == "best productivity tools"
        assert job_input.word_count == 1500

    def test_job_input_topic_validation(self):
        """Test topic length validation."""
        with pytest.raises(ValidationError):
            JobInput(topic="ab")  # Too short

    def test_job_input_word_count_validation(self):
        """Test word count range validation."""
        with pytest.raises(ValidationError):
            JobInput(topic="valid topic", word_count=100)  # Too low

        with pytest.raises(ValidationError):
            JobInput(topic="valid topic", word_count=10000)  # Too high

    def test_job_creation(self):
        """Test creating a job."""
        job = Job(
            job_id="test123",
            input=JobInput(topic="test topic"),
        )
        assert job.status == JobStatus.PENDING
        assert job.current_step == PipelineStep.CREATED

    def test_job_mark_step(self):
        """Test marking job step."""
        job = Job(
            job_id="test123",
            input=JobInput(topic="test topic"),
        )
        job.mark_step(PipelineStep.SERP_ANALYSIS)

        assert job.current_step == PipelineStep.SERP_ANALYSIS

    def test_job_mark_completed(self):
        """Test marking job as completed."""
        job = Job(
            job_id="test123",
            input=JobInput(topic="test topic"),
        )
        job.mark_step(PipelineStep.COMPLETED)

        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None

    def test_job_mark_failed(self):
        """Test marking job as failed."""
        job = Job(
            job_id="test123",
            input=JobInput(topic="test topic"),
        )
        job.mark_failed(
            step=PipelineStep.SERP_ANALYSIS,
            message="API error",
        )

        assert job.status == JobStatus.FAILED
        assert job.error is not None
        assert job.error.message == "API error"


class TestArticleModels:
    """Tests for article data models."""

    def test_seo_metadata(self):
        """Test SEO metadata model."""
        metadata = SEOMetadata(
            title_tag="Best Productivity Tools for Remote Teams",
            meta_description="Discover the top productivity tools...",
            slug="best-productivity-tools-remote-teams",
            primary_keyword="productivity tools",
        )
        assert len(metadata.title_tag) <= 70
        assert metadata.primary_keyword == "productivity tools"

    def test_keyword_analysis(self):
        """Test keyword analysis model."""
        analysis = KeywordAnalysis(
            primary_keyword="productivity tools",
            primary_count=15,
            primary_density=0.02,
            secondary_keywords=["remote teams", "collaboration"],
            secondary_counts={"remote teams": 8, "collaboration": 5},
        )
        assert analysis.primary_density == 0.02

    def test_internal_link(self):
        """Test internal link model."""
        link = InternalLink(
            anchor_text="project management tools",
            target_topic="project management guide",
            placement_hint="tools comparison section",
        )
        assert link.anchor_text == "project management tools"

    def test_heading_node(self):
        """Test heading node model."""
        heading = HeadingNode(level=2, text="Introduction")
        assert heading.level == 2

        with pytest.raises(ValidationError):
            HeadingNode(level=7, text="Invalid")  # Level must be 1-6

    def test_seo_validation_result(self):
        """Test SEO validation result model."""
        result = SEOValidationResult(
            passed=True,
            score=85.0,
            checks=[],
            issues=[],
        )
        assert result.passed
        assert result.score == 85.0

        # Test score validation
        with pytest.raises(ValidationError):
            SEOValidationResult(passed=True, score=150.0)  # Score > 100

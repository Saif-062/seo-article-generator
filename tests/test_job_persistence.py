"""Tests for job persistence and resume functionality."""

import tempfile
from pathlib import Path

import pytest

from app.models.job import Job, JobInput, JobStatus, PipelineStep
from app.persistence.job_store import JobStore


class TestJobStore:
    """Tests for job persistence."""

    @pytest.fixture
    def temp_jobs_dir(self):
        """Create a temporary directory for job storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def job_store(self, temp_jobs_dir):
        """Create a job store with temporary storage."""
        return JobStore(jobs_dir=temp_jobs_dir)

    def test_create_job(self, job_store):
        """Test creating a new job."""
        job_input = JobInput(topic="test topic", word_count=1000)
        job = job_store.create(job_input)

        assert job.job_id is not None
        assert len(job.job_id) == 8  # Short UUID
        assert job.status == JobStatus.PENDING
        assert job.input.topic == "test topic"

    def test_save_and_load_job(self, job_store):
        """Test saving and loading a job."""
        job_input = JobInput(topic="test topic")
        job = job_store.create(job_input)

        # Modify job
        job.mark_running()
        job.mark_step(PipelineStep.SERP_ANALYSIS)
        job_store.save(job)

        # Load job
        loaded = job_store.get(job.job_id)

        assert loaded is not None
        assert loaded.job_id == job.job_id
        assert loaded.status == JobStatus.RUNNING
        assert loaded.current_step == PipelineStep.SERP_ANALYSIS

    def test_get_nonexistent_job(self, job_store):
        """Test loading a job that doesn't exist."""
        job = job_store.get("nonexistent")
        assert job is None

    def test_list_jobs(self, job_store):
        """Test listing jobs."""
        # Create multiple jobs
        for i in range(5):
            job_store.create(JobInput(topic=f"topic {i}"))

        jobs = job_store.list_jobs()
        assert len(jobs) == 5

    def test_list_jobs_by_status(self, job_store):
        """Test filtering jobs by status."""
        # Create jobs with different statuses
        job1 = job_store.create(JobInput(topic="topic 1"))
        job2 = job_store.create(JobInput(topic="topic 2"))
        job3 = job_store.create(JobInput(topic="topic 3"))

        # Modify statuses
        job1.status = JobStatus.COMPLETED
        job_store.save(job1)

        job2.status = JobStatus.FAILED
        job_store.save(job2)

        # List by status
        pending = job_store.list_jobs(status=JobStatus.PENDING)
        completed = job_store.list_jobs(status=JobStatus.COMPLETED)
        failed = job_store.list_jobs(status=JobStatus.FAILED)

        assert len(pending) == 1
        assert len(completed) == 1
        assert len(failed) == 1

    def test_delete_job(self, job_store):
        """Test deleting a job."""
        job = job_store.create(JobInput(topic="test"))
        job_id = job.job_id

        assert job_store.exists(job_id)

        result = job_store.delete(job_id)
        assert result is True
        assert not job_store.exists(job_id)

    def test_delete_nonexistent_job(self, job_store):
        """Test deleting a job that doesn't exist."""
        result = job_store.delete("nonexistent")
        assert result is False

    def test_atomic_save(self, job_store, temp_jobs_dir):
        """Test that saves are atomic (no partial writes)."""
        job = job_store.create(JobInput(topic="test"))
        job_path = temp_jobs_dir / f"{job.job_id}.json"

        # Save multiple times
        for i in range(10):
            job.retry_count = i
            job_store.save(job)

        # Verify no temp files left behind
        temp_files = list(temp_jobs_dir.glob(".*"))
        assert len(temp_files) == 0

        # Verify final state
        loaded = job_store.get(job.job_id)
        assert loaded.retry_count == 9

    def test_get_resumable_jobs(self, job_store):
        """Test getting jobs that can be resumed."""
        # Create jobs with different statuses
        pending = job_store.create(JobInput(topic="pending"))

        running = job_store.create(JobInput(topic="running"))
        running.status = JobStatus.RUNNING
        job_store.save(running)

        failed = job_store.create(JobInput(topic="failed"))
        failed.status = JobStatus.FAILED
        job_store.save(failed)

        completed = job_store.create(JobInput(topic="completed"))
        completed.status = JobStatus.COMPLETED
        job_store.save(completed)

        # Get resumable
        resumable = job_store.get_resumable_jobs()

        # Should include running and failed, but not pending or completed
        job_ids = [j.job_id for j in resumable]
        assert running.job_id in job_ids
        assert failed.job_id in job_ids
        assert pending.job_id not in job_ids
        assert completed.job_id not in job_ids


class TestJobResume:
    """Tests for job resume functionality."""

    @pytest.fixture
    def temp_jobs_dir(self):
        """Create a temporary directory for job storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def job_store(self, temp_jobs_dir):
        """Create a job store with temporary storage."""
        return JobStore(jobs_dir=temp_jobs_dir)

    def test_resume_preserves_artifacts(self, job_store):
        """Test that resume preserves existing artifacts."""
        from app.models.serp import SerpData, SerpResult

        # Create job and simulate partial progress
        job = job_store.create(JobInput(topic="test"))
        job.mark_running()
        job.mark_step(PipelineStep.SERP_ANALYSIS)

        # Add some artifacts
        job.artifacts.serp_data = SerpData(
            query="test",
            results=[SerpResult(rank=1, url="https://example.com", title="Test")],
        )
        job_store.save(job)

        # Simulate crash and reload
        loaded = job_store.get(job.job_id)

        # Artifacts should be preserved
        assert loaded.artifacts.serp_data is not None
        assert len(loaded.artifacts.serp_data.results) == 1
        assert loaded.current_step == PipelineStep.SERP_ANALYSIS

    def test_resume_from_failed_state(self, job_store):
        """Test resuming a failed job."""
        job = job_store.create(JobInput(topic="test"))
        job.mark_running()
        job.mark_step(PipelineStep.THEME_EXTRACTION)
        job.mark_failed(PipelineStep.THEME_EXTRACTION, "API error")
        job_store.save(job)

        # Reload
        loaded = job_store.get(job.job_id)

        # Should be resumable
        assert loaded.status == JobStatus.FAILED
        assert loaded.current_step == PipelineStep.THEME_EXTRACTION
        assert loaded.error is not None

        # Clear error and resume
        loaded.error = None
        loaded.retry_count += 1
        loaded.mark_running()

        assert loaded.status == JobStatus.RUNNING
        assert loaded.retry_count == 1

    def test_checkpoint_step_order(self, job_store):
        """Test that checkpoints follow correct step order."""
        from app.pipeline.orchestrator import PipelineOrchestrator

        # Verify step order
        expected_order = [
            PipelineStep.CREATED,
            PipelineStep.SERP_ANALYSIS,
            PipelineStep.THEME_EXTRACTION,
            PipelineStep.OUTLINE_GENERATION,
            PipelineStep.ARTICLE_GENERATION,
            PipelineStep.SEO_VALIDATION,
            PipelineStep.COMPLETED,
        ]

        assert PipelineOrchestrator.STEP_ORDER == expected_order

    def test_job_with_all_artifacts(self, job_store):
        """Test job with complete artifacts can be serialized/deserialized."""
        from app.models.article import (
            ArticleOutline,
            GeneratedArticle,
            KeywordAnalysis,
            OutlineSection,
            SEOMetadata,
            SEOValidationResult,
        )
        from app.models.job import ThemeAnalysis
        from app.models.serp import SerpData, SerpResult

        job = job_store.create(JobInput(topic="test"))

        # Add all artifacts
        job.artifacts.serp_data = SerpData(
            query="test",
            results=[SerpResult(rank=1, url="https://example.com", title="Test")],
        )
        job.artifacts.theme_analysis = ThemeAnalysis(
            search_intent="informational",
            primary_themes=["theme1"],
        )
        job.artifacts.outline = ArticleOutline(
            title="Test",
            sections=[OutlineSection(heading="Intro", level=2)],
        )
        job.artifacts.draft_article = "# Draft\n\nContent"
        job.artifacts.final_article = GeneratedArticle(
            article_markdown="# Final\n\nContent",
            seo_metadata=SEOMetadata(
                title_tag="Test",
                meta_description="Test description",
                slug="test",
                primary_keyword="test",
            ),
            keyword_analysis=KeywordAnalysis(primary_keyword="test"),
            seo_validation=SEOValidationResult(passed=True, score=90),
        )

        job_store.save(job)

        # Reload and verify
        loaded = job_store.get(job.job_id)
        assert loaded.artifacts.serp_data is not None
        assert loaded.artifacts.theme_analysis is not None
        assert loaded.artifacts.outline is not None
        assert loaded.artifacts.draft_article is not None
        assert loaded.artifacts.final_article is not None

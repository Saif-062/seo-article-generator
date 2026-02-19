"""End-to-end test for the full pipeline with mock providers."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from app.models.job import JobInput, JobStatus, PipelineStep
from app.persistence.job_store import JobStore
from app.pipeline.orchestrator import PipelineOrchestrator
from app.providers.llm.mock import MockLLMProvider
from app.providers.serp.mock import MockSerpProvider


class TestEndToEnd:
    """End-to-end tests for the full article generation pipeline."""

    @pytest.fixture
    def temp_jobs_dir(self):
        """Create a temporary directory for job storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def orchestrator(self, temp_jobs_dir):
        """Create an orchestrator with mock providers."""
        return PipelineOrchestrator(
            job_store=JobStore(jobs_dir=temp_jobs_dir),
            serp_provider=MockSerpProvider(),
            llm_provider=MockLLMProvider(),
        )

    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, orchestrator):
        """Test complete pipeline from topic to finished article."""
        # Create job
        job_input = JobInput(
            topic="best productivity tools for remote teams",
            word_count=1500,
            language="en",
        )
        job = orchestrator.job_store.create(job_input)

        # Run pipeline
        result = await orchestrator.run(job)

        # Verify completion
        assert result.status == JobStatus.COMPLETED
        assert result.current_step == PipelineStep.COMPLETED

        # Verify artifacts
        assert result.artifacts.serp_data is not None
        assert len(result.artifacts.serp_data.results) == 10

        assert result.artifacts.theme_analysis is not None
        assert result.artifacts.theme_analysis.search_intent

        assert result.artifacts.outline is not None
        assert result.artifacts.outline.title

        assert result.artifacts.draft_article is not None
        assert len(result.artifacts.draft_article) > 0

        assert result.artifacts.final_article is not None

    @pytest.mark.asyncio
    async def test_final_article_structure(self, orchestrator):
        """Test that the final article has all required components."""
        job_input = JobInput(topic="productivity tools", word_count=1500)
        job = orchestrator.job_store.create(job_input)
        result = await orchestrator.run(job)

        article = result.artifacts.final_article
        assert article is not None

        # Check article content
        assert article.article_markdown
        assert "# " in article.article_markdown  # Has H1

        # Check SEO metadata
        assert article.seo_metadata.title_tag
        assert article.seo_metadata.meta_description
        assert article.seo_metadata.slug
        assert article.seo_metadata.primary_keyword

        # Check keyword analysis
        assert article.keyword_analysis.primary_keyword

        # Check heading structure
        assert len(article.heading_structure) > 0
        assert article.heading_structure[0].level == 1  # First is H1

        # Check validation
        assert article.seo_validation is not None
        assert 0 <= article.seo_validation.score <= 100

        # Check word count
        assert article.word_count > 0

    @pytest.mark.asyncio
    async def test_job_persistence_during_pipeline(self, orchestrator, temp_jobs_dir):
        """Test that job is persisted at each step."""
        job_input = JobInput(topic="test topic", word_count=1000)
        job = orchestrator.job_store.create(job_input)
        job_id = job.job_id

        # Run pipeline
        await orchestrator.run(job)

        # Reload from disk
        loaded = orchestrator.job_store.get(job_id)
        assert loaded is not None
        assert loaded.status == JobStatus.COMPLETED
        assert loaded.artifacts.final_article is not None

    @pytest.mark.asyncio
    async def test_pipeline_progress_callback(self, orchestrator):
        """Test that progress callback is called at each step."""
        progress_updates = []

        def on_progress(job):
            progress_updates.append(job.current_step)

        job_input = JobInput(topic="test topic")
        job = orchestrator.job_store.create(job_input)

        await orchestrator.run(job, on_progress=on_progress)

        # Should have updates for each step
        assert len(progress_updates) >= 5  # At least 5 steps
        assert PipelineStep.SERP_ANALYSIS in progress_updates
        assert PipelineStep.COMPLETED in progress_updates

    @pytest.mark.asyncio
    async def test_resume_from_checkpoint(self, orchestrator):
        """Test resuming a job from a checkpoint."""
        # Create and partially run a job
        job_input = JobInput(topic="test topic")
        job = orchestrator.job_store.create(job_input)

        # Run full pipeline
        await orchestrator.run(job)

        # Simulate a "resume" by loading and checking state
        loaded = orchestrator.job_store.get(job.job_id)
        assert loaded.status == JobStatus.COMPLETED

        # Try to resume (should just return since already complete)
        resumed = await orchestrator.resume(job.job_id)
        assert resumed.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_different_word_counts(self, orchestrator):
        """Test pipeline with different word count targets."""
        for word_count in [500, 1000, 2000]:
            job_input = JobInput(topic="test topic", word_count=word_count)
            job = orchestrator.job_store.create(job_input)
            result = await orchestrator.run(job)

            assert result.status == JobStatus.COMPLETED
            assert result.artifacts.final_article is not None

    @pytest.mark.asyncio
    async def test_serp_data_contains_expected_fields(self, orchestrator):
        """Test that SERP data has all expected fields."""
        job_input = JobInput(topic="productivity tools")
        job = orchestrator.job_store.create(job_input)
        await orchestrator.run(job)

        serp = job.artifacts.serp_data
        assert serp is not None
        assert serp.query == "productivity tools"
        assert len(serp.results) == 10

        for result in serp.results:
            assert result.rank >= 1
            assert result.url
            assert result.title

        assert len(serp.people_also_ask) > 0
        assert len(serp.related_searches) > 0

    @pytest.mark.asyncio
    async def test_theme_analysis_contains_expected_fields(self, orchestrator):
        """Test that theme analysis has all expected fields."""
        job_input = JobInput(topic="productivity tools")
        job = orchestrator.job_store.create(job_input)
        await orchestrator.run(job)

        themes = job.artifacts.theme_analysis
        assert themes is not None
        assert themes.search_intent
        assert len(themes.primary_themes) > 0
        assert len(themes.common_sections) > 0
        assert len(themes.faq_questions) > 0


if __name__ == "__main__":
    # Run a quick test
    async def main():
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = PipelineOrchestrator(
                job_store=JobStore(jobs_dir=Path(tmpdir)),
                serp_provider=MockSerpProvider(),
                llm_provider=MockLLMProvider(),
            )

            job_input = JobInput(
                topic="best productivity tools for remote teams",
                word_count=1500,
            )
            job = orchestrator.job_store.create(job_input)

            print(f"Created job: {job.job_id}")
            print(f"Topic: {job.input.topic}")
            print(f"Status: {job.status}")
            print()

            result = await orchestrator.run(job)

            print(f"Final status: {result.status}")
            print(f"Final step: {result.current_step}")
            print()

            if result.artifacts.final_article:
                article = result.artifacts.final_article
                print("=== Generated Article ===")
                print(f"Title: {article.seo_metadata.title_tag}")
                print(f"Meta: {article.seo_metadata.meta_description}")
                print(f"Word count: {article.word_count}")
                print(f"SEO Score: {article.seo_validation.score}")
                print()
                print("=== Article Preview (first 500 chars) ===")
                print(article.article_markdown[:500])
                print("...")

    asyncio.run(main())

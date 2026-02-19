"""Pipeline orchestrator that manages the article generation workflow."""

from __future__ import annotations

import logging
from typing import Callable

from app.models.job import Job, JobStatus, PipelineStep
from app.persistence.job_store import JobStore, get_job_store
from app.pipeline.steps.article_generation import ArticleGenerationStep
from app.pipeline.steps.outline_generation import OutlineGenerationStep
from app.pipeline.steps.seo_validation import SEOValidationStep
from app.pipeline.steps.serp_analysis import SerpAnalysisStep
from app.pipeline.steps.theme_extraction import ThemeExtractionStep
from app.providers.llm import get_llm_provider
from app.providers.serp import get_serp_provider

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates the article generation pipeline.

    The pipeline consists of the following steps:
    1. SERP Analysis - Fetch and analyze search results
    2. Theme Extraction - Extract themes and intent from SERP data
    3. Outline Generation - Create article outline using LLM
    4. Article Generation - Generate full article using LLM
    5. SEO Validation - Validate and optionally revise the article

    Each step is checkpointed, allowing the pipeline to resume from
    the last successful step after a crash.
    """

    # Define the step order for resumption
    STEP_ORDER = [
        PipelineStep.CREATED,
        PipelineStep.SERP_ANALYSIS,
        PipelineStep.THEME_EXTRACTION,
        PipelineStep.OUTLINE_GENERATION,
        PipelineStep.ARTICLE_GENERATION,
        PipelineStep.SEO_VALIDATION,
        PipelineStep.COMPLETED,
    ]

    def __init__(
        self,
        job_store: JobStore | None = None,
        serp_provider=None,
        llm_provider=None,
    ):
        self.job_store = job_store or get_job_store()
        self.serp_provider = serp_provider or get_serp_provider()
        self.llm_provider = llm_provider or get_llm_provider()

        # Initialize steps
        self.serp_step = SerpAnalysisStep(self.serp_provider)
        self.theme_step = ThemeExtractionStep(self.llm_provider)
        self.outline_step = OutlineGenerationStep(self.llm_provider)
        self.article_step = ArticleGenerationStep(self.llm_provider)
        self.seo_step = SEOValidationStep(self.llm_provider)

    def _get_next_step(self, current_step: PipelineStep) -> PipelineStep | None:
        """Get the next step in the pipeline."""
        try:
            current_index = self.STEP_ORDER.index(current_step)
            if current_index + 1 < len(self.STEP_ORDER):
                return self.STEP_ORDER[current_index + 1]
        except ValueError:
            pass
        return None

    def _checkpoint(self, job: Job, step: PipelineStep) -> None:
        """Save a checkpoint after completing a step."""
        job.mark_step(step)
        self.job_store.save(job)
        logger.info(f"Job {job.job_id}: Checkpoint saved at step {step}")

    async def run(self, job: Job, on_progress: Callable[[Job], None] | None = None) -> Job:
        """
        Run the pipeline for a job.

        Args:
            job: The job to process
            on_progress: Optional callback for progress updates

        Returns:
            The completed job with generated article
        """
        job.mark_running()
        self.job_store.save(job)

        if on_progress:
            on_progress(job)

        try:
            # Determine starting point (for resume capability)
            start_index = self.STEP_ORDER.index(job.current_step)

            # Execute each step from the current position
            for i in range(start_index, len(self.STEP_ORDER) - 1):
                current_step = self.STEP_ORDER[i]
                next_step = self.STEP_ORDER[i + 1]

                logger.info(f"Job {job.job_id}: Executing step {next_step}")

                # Execute the appropriate step
                await self._execute_step(job, next_step)

                # Checkpoint after each step
                self._checkpoint(job, next_step)

                if on_progress:
                    on_progress(job)

                # Check if completed
                if next_step == PipelineStep.COMPLETED:
                    break

            return job

        except Exception as e:
            logger.error(f"Job {job.job_id}: Pipeline failed at {job.current_step}: {e}")
            job.mark_failed(
                step=job.current_step,
                message=str(e),
                details=repr(e),
            )
            self.job_store.save(job)

            if on_progress:
                on_progress(job)

            raise

    async def _execute_step(self, job: Job, step: PipelineStep) -> None:
        """Execute a specific pipeline step."""
        if step == PipelineStep.SERP_ANALYSIS:
            serp_data = await self.serp_step.execute(job.input.topic)
            job.artifacts.serp_data = serp_data

        elif step == PipelineStep.THEME_EXTRACTION:
            if not job.artifacts.serp_data:
                raise ValueError("SERP data required for theme extraction")
            theme_analysis = await self.theme_step.execute(
                job.input.topic,
                job.artifacts.serp_data,
            )
            job.artifacts.theme_analysis = theme_analysis

        elif step == PipelineStep.OUTLINE_GENERATION:
            if not job.artifacts.theme_analysis:
                raise ValueError("Theme analysis required for outline generation")
            outline = await self.outline_step.execute(
                topic=job.input.topic,
                theme_analysis=job.artifacts.theme_analysis,
                word_count=job.input.word_count,
                language=job.input.language,
            )
            job.artifacts.outline = outline

        elif step == PipelineStep.ARTICLE_GENERATION:
            if not job.artifacts.outline:
                raise ValueError("Outline required for article generation")
            draft = await self.article_step.execute(
                topic=job.input.topic,
                outline=job.artifacts.outline,
                theme_analysis=job.artifacts.theme_analysis,
                word_count=job.input.word_count,
                language=job.input.language,
            )
            job.artifacts.draft_article = draft

        elif step == PipelineStep.SEO_VALIDATION:
            if not job.artifacts.draft_article or not job.artifacts.outline:
                raise ValueError("Draft article required for SEO validation")
            final_article = await self.seo_step.execute(
                draft_article=job.artifacts.draft_article,
                outline=job.artifacts.outline,
                topic=job.input.topic,
                target_word_count=job.input.word_count,
            )
            job.artifacts.final_article = final_article

        elif step == PipelineStep.COMPLETED:
            job.status = JobStatus.COMPLETED

    async def resume(self, job_id: str) -> Job:
        """
        Resume a failed or interrupted job.

        Args:
            job_id: The ID of the job to resume

        Returns:
            The completed job

        Raises:
            ValueError: If job not found or cannot be resumed
        """
        job = self.job_store.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status == JobStatus.COMPLETED:
            logger.info(f"Job {job_id} already completed")
            return job

        if job.status not in [JobStatus.FAILED, JobStatus.RUNNING]:
            raise ValueError(f"Job {job_id} cannot be resumed (status: {job.status})")

        # Reset error state
        job.error = None
        job.retry_count += 1

        logger.info(f"Resuming job {job_id} from step {job.current_step}")
        return await self.run(job)

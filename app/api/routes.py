"""API routes for the SEO article generator."""

from __future__ import annotations

import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path

from app.api.schemas import (
    CreateJobRequest,
    HealthResponse,
    JobResultResponse,
    JobStatusResponse,
)
from app.models.job import Job, JobInput, JobStatus
from app.persistence.job_store import get_job_store
from app.pipeline.orchestrator import PipelineOrchestrator
from app.providers.llm import get_llm_provider
from app.providers.serp import get_serp_provider

logger = logging.getLogger(__name__)

router = APIRouter()

# Store for tracking background tasks
_running_tasks: dict[str, asyncio.Task] = {}


def _get_orchestrator() -> PipelineOrchestrator:
    """Get a configured pipeline orchestrator."""
    return PipelineOrchestrator(
        job_store=get_job_store(),
        serp_provider=get_serp_provider(),
        llm_provider=get_llm_provider(),
    )


async def _run_pipeline(job_id: str) -> None:
    """Background task to run the pipeline."""
    job_store = get_job_store()
    job = job_store.get(job_id)

    if not job:
        logger.error(f"Job {job_id} not found for pipeline execution")
        return

    orchestrator = _get_orchestrator()

    try:
        await orchestrator.run(job)
        logger.info(f"Job {job_id} completed successfully")
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
    finally:
        # Clean up task reference
        _running_tasks.pop(job_id, None)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check API health and provider status."""
    serp_provider = get_serp_provider()
    llm_provider = get_llm_provider()

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        serp_provider=serp_provider.name,
        llm_provider=llm_provider.name,
    )


@router.post("/jobs", response_model=JobStatusResponse, status_code=201)
async def create_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks,
) -> JobStatusResponse:
    """
    Create a new article generation job.

    The job will be processed asynchronously in the background.
    Use GET /jobs/{job_id} to check status and retrieve results.
    """
    job_store = get_job_store()

    # Create job input
    job_input = JobInput(
        topic=request.topic,
        word_count=request.word_count,
        language=request.language,
    )

    # Create and persist job
    job = job_store.create(job_input)
    logger.info(f"Created job {job.job_id} for topic: {request.topic}")

    # Start pipeline in background
    task = asyncio.create_task(_run_pipeline(job.job_id))
    _running_tasks[job.job_id] = task

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        current_step=job.current_step,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/jobs/{job_id}", response_model=JobResultResponse)
async def get_job(
    job_id: Annotated[str, Path(description="The job ID")],
) -> JobResultResponse:
    """
    Get job status and results.

    Returns the current status of the job. If completed, includes
    the full generated article with all metadata.
    """
    job_store = get_job_store()
    job = job_store.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobResultResponse(
        job_id=job.job_id,
        status=job.status,
        current_step=job.current_step,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        topic=job.input.topic,
        word_count=job.input.word_count,
        language=job.input.language,
        article=job.artifacts.final_article,
        error_message=job.error.message if job.error else None,
        error_step=job.error.step if job.error else None,
    )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: Annotated[str, Path(description="The job ID")],
) -> JobStatusResponse:
    """Get lightweight job status (without full results)."""
    job_store = get_job_store()
    job = job_store.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        current_step=job.current_step,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        error_message=job.error.message if job.error else None,
    )


@router.post("/jobs/{job_id}/resume", response_model=JobStatusResponse)
async def resume_job(
    job_id: Annotated[str, Path(description="The job ID")],
) -> JobStatusResponse:
    """
    Resume a failed or interrupted job.

    The job will continue from the last successful checkpoint.
    """
    job_store = get_job_store()
    job = job_store.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status == JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job already completed")

    if job.status == JobStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Job is currently running")

    if job.status not in [JobStatus.FAILED, JobStatus.PENDING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume job with status {job.status}",
        )

    # Start pipeline in background
    task = asyncio.create_task(_run_pipeline(job.job_id))
    _running_tasks[job.job_id] = task

    logger.info(f"Resuming job {job.job_id} from step {job.current_step}")

    return JobStatusResponse(
        job_id=job.job_id,
        status=JobStatus.RUNNING,
        current_step=job.current_step,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/jobs", response_model=list[JobStatusResponse])
async def list_jobs(
    status: JobStatus | None = None,
    limit: int = 20,
) -> list[JobStatusResponse]:
    """List all jobs, optionally filtered by status."""
    job_store = get_job_store()
    jobs = job_store.list_jobs(status=status, limit=limit)

    return [
        JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            current_step=job.current_step,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            error_message=job.error.message if job.error else None,
        )
        for job in jobs
    ]

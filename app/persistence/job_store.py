"""Job persistence layer using JSON files."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from app.config import get_settings
from app.models.job import Job, JobInput, JobStatus, PipelineStep


class JobStore:
    """
    Persistent storage for jobs using JSON files.

    Each job is stored as a separate JSON file in the jobs directory.
    Atomic writes are used to prevent corruption on crashes.
    """

    def __init__(self, jobs_dir: Path | None = None):
        self.jobs_dir = jobs_dir or get_settings().jobs_dir
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def _job_path(self, job_id: str) -> Path:
        """Get the file path for a job."""
        return self.jobs_dir / f"{job_id}.json"

    def create(self, input_data: JobInput) -> Job:
        """
        Create a new job and persist it.

        Args:
            input_data: The job input parameters

        Returns:
            The created Job with a unique ID
        """
        job_id = str(uuid.uuid4())[:8]  # Short ID for convenience
        job = Job(
            job_id=job_id,
            input=input_data,
            status=JobStatus.PENDING,
            current_step=PipelineStep.CREATED,
        )
        self.save(job)
        return job

    def save(self, job: Job) -> None:
        """
        Save a job to disk atomically.

        Uses write-to-temp-then-rename pattern to prevent corruption.

        Args:
            job: The job to save
        """
        job.updated_at = datetime.utcnow()
        job_path = self._job_path(job.job_id)

        # Write to temp file first, then rename (atomic on most filesystems)
        fd, temp_path = tempfile.mkstemp(
            dir=self.jobs_dir,
            prefix=f".{job.job_id}_",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w") as f:
                f.write(job.model_dump_json(indent=2))
            os.rename(temp_path, job_path)
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def get(self, job_id: str) -> Job | None:
        """
        Load a job from disk.

        Args:
            job_id: The job ID to load

        Returns:
            The Job if found, None otherwise
        """
        job_path = self._job_path(job_id)
        if not job_path.exists():
            return None

        try:
            with open(job_path) as f:
                data = json.load(f)
            return Job.model_validate(data)
        except (json.JSONDecodeError, Exception):
            return None

    def exists(self, job_id: str) -> bool:
        """Check if a job exists."""
        return self._job_path(job_id).exists()

    def list_jobs(
        self,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[Job]:
        """
        List jobs, optionally filtered by status.

        Args:
            status: Filter by job status (optional)
            limit: Maximum number of jobs to return

        Returns:
            List of jobs, sorted by created_at descending
        """
        jobs = []
        for path in self.jobs_dir.glob("*.json"):
            if path.name.startswith("."):
                continue  # Skip temp files
            try:
                with open(path) as f:
                    data = json.load(f)
                job = Job.model_validate(data)
                if status is None or job.status == status:
                    jobs.append(job)
            except Exception:
                continue  # Skip invalid files

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def delete(self, job_id: str) -> bool:
        """
        Delete a job from disk.

        Args:
            job_id: The job ID to delete

        Returns:
            True if deleted, False if not found
        """
        job_path = self._job_path(job_id)
        if job_path.exists():
            job_path.unlink()
            return True
        return False

    def get_resumable_jobs(self) -> list[Job]:
        """
        Get jobs that can be resumed (failed or running).

        Returns:
            List of jobs with status RUNNING or FAILED
        """
        jobs = []
        for status in [JobStatus.RUNNING, JobStatus.FAILED]:
            jobs.extend(self.list_jobs(status=status))
        return jobs


# Singleton instance
_job_store: JobStore | None = None


def get_job_store() -> JobStore:
    """Get the singleton JobStore instance."""
    global _job_store
    if _job_store is None:
        _job_store = JobStore()
    return _job_store

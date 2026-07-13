"""Queue contracts and deterministic queue adapters for background jobs."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

from aevryn.workers.models import BackgroundJob, BackgroundQueueSnapshot

logger = logging.getLogger(__name__)


class BackgroundJobQueue(Protocol):
    """Queue boundary used by the platform API and workers."""

    def enqueue(self, job: BackgroundJob) -> None:
        """Add a queued job."""

    def claim_next(self, claimed_at: str) -> BackgroundJob | None:
        """Claim the next queued job in deterministic order."""

    def complete(self, job_id: str, completed_at: str) -> BackgroundJob:
        """Mark a running job as succeeded."""

    def fail(self, job_id: str, failed_at: str, error_summary: str) -> BackgroundJob:
        """Mark a running job as failed."""

    def get(self, job_id: str) -> BackgroundJob:
        """Return a job by ID."""

    def has_job(self, job_id: str) -> bool:
        """Return whether a job ID already exists."""

    def list_jobs(self) -> tuple[BackgroundJob, ...]:
        """Return all jobs in deterministic order."""

    def delete_project_jobs(self, project_id: str) -> int:
        """Delete all jobs scoped to a hard-deleted project."""

    def delete_story_jobs(self, story_id: str) -> int:
        """Delete all jobs scoped to a hard-deleted story."""

    def snapshot(self) -> BackgroundQueueSnapshot:
        """Return deterministic queue status counts."""


class JobQueueError(Exception):
    """Base error for background queue failures."""


class DuplicateJobError(JobQueueError):
    """Raised when a job ID is submitted more than once."""


class JobNotFoundError(JobQueueError):
    """Raised when a required job does not exist."""


class InvalidJobTransitionError(JobQueueError):
    """Raised when a queue status transition is invalid."""


class InMemoryJobQueue:
    """Deterministic in-memory queue for tests and local platform runs."""

    def __init__(self) -> None:
        """Create an empty queue."""
        self._jobs: dict[str, BackgroundJob] = {}
        self._order: list[str] = []

    def enqueue(self, job: BackgroundJob) -> None:
        """Add a queued job."""
        if job.status != "queued":
            raise InvalidJobTransitionError("Only queued jobs can be enqueued.")
        if job.job_id in self._jobs:
            raise DuplicateJobError(f"Duplicate background job: {job.job_id}")
        self._jobs[job.job_id] = job
        self._order.append(job.job_id)
        logger.debug("background_job_enqueued", extra={"job_id": job.job_id})

    def claim_next(self, claimed_at: str) -> BackgroundJob | None:
        """Claim the next queued job in deterministic FIFO order."""
        for job_id in self._order:
            job = self._jobs[job_id]
            if job.status != "queued":
                continue
            claimed = BackgroundJob(
                job_id=job.job_id,
                kind=job.kind,
                run_id=job.run_id,
                project_id=job.project_id,
                story_id=job.story_id,
                import_id=job.import_id,
                status="running",
                queued_at=job.queued_at,
                status_updated_at=claimed_at,
                attempts=job.attempts + 1,
                max_attempts=job.max_attempts,
            )
            self._jobs[job_id] = claimed
            logger.debug("background_job_claimed", extra={"job_id": job_id})
            return claimed

        return None

    def complete(self, job_id: str, completed_at: str) -> BackgroundJob:
        """Mark a running job as succeeded."""
        job = self.get(job_id)
        if job.status != "running":
            raise InvalidJobTransitionError("Only running jobs can succeed.")
        _require_transition_timestamp_not_before_current(
            current=job.status_updated_at,
            next_value=completed_at,
            label="Background job completed_at",
        )
        completed = BackgroundJob(
            job_id=job.job_id,
            kind=job.kind,
            run_id=job.run_id,
            project_id=job.project_id,
            story_id=job.story_id,
            import_id=job.import_id,
            status="succeeded",
            queued_at=job.queued_at,
            status_updated_at=completed_at,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
        )
        self._jobs[job_id] = completed
        logger.debug("background_job_succeeded", extra={"job_id": job_id})
        return completed

    def fail(self, job_id: str, failed_at: str, error_summary: str) -> BackgroundJob:
        """Mark a running job as failed."""
        job = self.get(job_id)
        if job.status != "running":
            raise InvalidJobTransitionError("Only running jobs can fail.")
        _require_transition_timestamp_not_before_current(
            current=job.status_updated_at,
            next_value=failed_at,
            label="Background job failed_at",
        )
        failed = BackgroundJob(
            job_id=job.job_id,
            kind=job.kind,
            run_id=job.run_id,
            project_id=job.project_id,
            story_id=job.story_id,
            import_id=job.import_id,
            status="failed",
            queued_at=job.queued_at,
            status_updated_at=failed_at,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            error_summary=error_summary,
        )
        self._jobs[job_id] = failed
        logger.debug("background_job_failed", extra={"job_id": job_id})
        return failed

    def get(self, job_id: str) -> BackgroundJob:
        """Return a job by ID."""
        job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFoundError(f"Unknown background job: {job_id}")
        return job

    def has_job(self, job_id: str) -> bool:
        """Return whether a job ID already exists."""
        return job_id in self._jobs

    def list_jobs(self) -> tuple[BackgroundJob, ...]:
        """Return all jobs in deterministic FIFO order."""
        return tuple(self._jobs[job_id] for job_id in self._order)

    def delete_project_jobs(self, project_id: str) -> int:
        """Delete all jobs scoped to a hard-deleted project."""
        return self._delete_jobs(
            job_id
            for job_id in self._order
            if self._jobs[job_id].project_id == project_id
        )

    def delete_story_jobs(self, story_id: str) -> int:
        """Delete all jobs scoped to a hard-deleted story."""
        return self._delete_jobs(
            job_id
            for job_id in self._order
            if self._jobs[job_id].story_id == story_id
        )

    def snapshot(self) -> BackgroundQueueSnapshot:
        """Return deterministic queue status counts."""
        jobs = self.list_jobs()
        next_job_id = next(
            (job.job_id for job in jobs if job.status == "queued"),
            "",
        )
        return BackgroundQueueSnapshot(
            total_jobs=len(jobs),
            queued_jobs=sum(1 for job in jobs if job.status == "queued"),
            running_jobs=sum(1 for job in jobs if job.status == "running"),
            succeeded_jobs=sum(1 for job in jobs if job.status == "succeeded"),
            failed_jobs=sum(1 for job in jobs if job.status == "failed"),
            next_job_id=next_job_id,
        )

    def _delete_jobs(self, job_ids: Iterable[str]) -> int:
        """Delete queued job IDs while preserving deterministic order."""
        deleted_ids = set(job_ids)
        if not deleted_ids:
            return 0
        for job_id in deleted_ids:
            del self._jobs[job_id]
        self._order = [job_id for job_id in self._order if job_id not in deleted_ids]
        return len(deleted_ids)


def _require_transition_timestamp_not_before_current(
    *,
    current: str,
    next_value: str,
    label: str,
) -> None:
    """Require a queue transition timestamp to be monotonic."""
    current_timestamp = _parse_utc_timestamp(current, "Background job current status")
    next_timestamp = _parse_utc_timestamp(next_value, label)
    if next_timestamp < current_timestamp:
        raise InvalidJobTransitionError(f"{label} cannot be before current status.")


def _parse_utc_timestamp(value: str, label: str) -> datetime:
    """Parse a UTC timestamp ending in Z."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidJobTransitionError(f"{label} cannot be blank.")
    if "T" not in value or not value.endswith("Z"):
        raise InvalidJobTransitionError(
            f"{label} must be an ISO UTC timestamp ending in Z."
        )
    try:
        return datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise InvalidJobTransitionError(
            f"{label} must be an ISO UTC timestamp ending in Z."
        ) from error

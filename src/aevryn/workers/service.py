"""Background job submission and worker execution services."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import datetime
from typing import Protocol

from aevryn.persistence import EngineRunRecord, ProjectRepository
from aevryn.workers.models import BackgroundJob, BackgroundWorkerRunSummary
from aevryn.workers.queue import BackgroundJobQueue, DuplicateJobError

logger = logging.getLogger(__name__)


class BackgroundJobHandler(Protocol):
    """Handler that performs a claimed background job."""

    def process(self, job: BackgroundJob) -> None:
        """Execute a claimed job or raise a clear exception."""


class BackgroundJobService:
    """Submit background jobs without executing engine logic inline."""

    def __init__(
        self,
        repository: ProjectRepository,
        queue: BackgroundJobQueue,
        engine_version: str,
    ) -> None:
        """Create a background job submission service."""
        if not engine_version.strip():
            raise ValueError("Engine version cannot be blank.")
        self._repository = repository
        self._queue = queue
        self._engine_version = engine_version

    def submit_import_processing_job(
        self,
        *,
        job_id: str,
        run_id: str,
        project_id: str,
        story_id: str,
        import_id: str,
        queued_at: str,
    ) -> BackgroundJob:
        """Record a pending engine run and enqueue import processing.

        The service owns job submission only. The worker owns execution, and the
        engine remains the only owner of continuity behavior.
        """
        job = BackgroundJob(
            job_id=job_id,
            kind="process_import",
            run_id=run_id,
            project_id=project_id,
            story_id=story_id,
            import_id=import_id,
            status="queued",
            queued_at=queued_at,
            status_updated_at=queued_at,
        )
        if self._queue.has_job(job_id):
            raise DuplicateJobError(f"Duplicate background job: {job_id}")
        run = EngineRunRecord(
            run_id=run_id,
            project_id=project_id,
            story_id=story_id,
            import_id=import_id,
            status="pending",
            engine_version=self._engine_version,
            started_at=queued_at,
            status_updated_at=queued_at,
            job_ref=f"queue://{job_id}",
        )
        self._repository.record_engine_run(run)
        try:
            self._queue.enqueue(job)
        except Exception as error:
            self._repository.update_engine_run(
                replace(
                    run,
                    status="failed",
                    status_updated_at=queued_at,
                    finished_at=queued_at,
                    error_summary=_error_summary(error),
                )
            )
            raise
        logger.debug(
            "background_job_submitted",
            extra={"job_id": job_id, "run_id": run_id},
        )
        return job


class BackgroundWorker:
    """Claim queued jobs and synchronize engine run lifecycle records."""

    def __init__(
        self,
        repository: ProjectRepository,
        queue: BackgroundJobQueue,
        handler: BackgroundJobHandler,
    ) -> None:
        """Create a background worker."""
        self._repository = repository
        self._queue = queue
        self._handler = handler

    def process_next(self, *, started_at: str, finished_at: str) -> BackgroundJob | None:
        """Process one queued job and return its final queue record.

        Returns:
            The succeeded or failed job, or ``None`` when the queue is empty.
        """
        _require_worker_timestamp_order(started_at=started_at, finished_at=finished_at)
        job = self._queue.claim_next(claimed_at=started_at)
        if job is None:
            logger.debug("background_worker_idle")
            return None

        run = self._repository.get_engine_run_for_worker(job.run_id)
        scope_error = _job_scope_error(job=job, run=run)
        if scope_error:
            self._repository.update_engine_run(
                replace(
                    run,
                    status="failed",
                    status_updated_at=finished_at,
                    finished_at=finished_at,
                    error_summary=scope_error,
                )
            )
            return self._queue.fail(
                job_id=job.job_id,
                failed_at=finished_at,
                error_summary=scope_error,
            )
        self._repository.update_engine_run(
            replace(run, status="running", status_updated_at=started_at)
        )
        try:
            self._handler.process(job)
        except Exception as error:
            summary = _error_summary(error)
            latest_run = self._repository.get_engine_run_for_worker(job.run_id)
            self._repository.update_engine_run(
                replace(
                    latest_run,
                    status="failed",
                    status_updated_at=finished_at,
                    finished_at=finished_at,
                    error_summary=summary,
                )
            )
            return self._queue.fail(
                job_id=job.job_id,
                failed_at=finished_at,
                error_summary=summary,
            )

        latest_run = self._repository.get_engine_run_for_worker(job.run_id)
        self._repository.update_engine_run(
            replace(
                latest_run,
                status="succeeded",
                status_updated_at=finished_at,
                finished_at=finished_at,
            )
        )
        return self._queue.complete(job_id=job.job_id, completed_at=finished_at)

    def process_available(
        self,
        *,
        started_at: str,
        finished_at: str,
        max_jobs: int,
    ) -> BackgroundWorkerRunSummary:
        """Process queued jobs until idle or the job limit is reached.

        Parameters:
            started_at: UTC timestamp applied to each claimed job.
            finished_at: UTC timestamp applied to each completed job.
            max_jobs: Maximum number of jobs to process in this drain loop.

        Returns:
            Summary of claimed, succeeded, and failed jobs.
        """
        if isinstance(max_jobs, bool) or max_jobs < 1:
            raise ValueError("max_jobs must be a positive integer.")
        succeeded_jobs = 0
        failed_jobs = 0
        for _ in range(max_jobs):
            job = self.process_next(started_at=started_at, finished_at=finished_at)
            if job is None:
                break
            if job.status == "succeeded":
                succeeded_jobs += 1
            elif job.status == "failed":
                failed_jobs += 1

        return BackgroundWorkerRunSummary(
            claimed_jobs=succeeded_jobs + failed_jobs,
            succeeded_jobs=succeeded_jobs,
            failed_jobs=failed_jobs,
        )


def _require_worker_timestamp_order(started_at: str, finished_at: str) -> None:
    """Require worker finish timestamps to be at or after start timestamps."""
    started = _parse_utc_timestamp(started_at, "Worker started_at")
    finished = _parse_utc_timestamp(finished_at, "Worker finished_at")
    if finished < started:
        raise ValueError("Worker finished_at cannot be before started_at.")


def _parse_utc_timestamp(value: str, label: str) -> datetime:
    """Parse a UTC timestamp ending in Z."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} cannot be blank.")
    if "T" not in value or not value.endswith("Z"):
        raise ValueError(f"{label} must be an ISO UTC timestamp ending in Z.")
    try:
        return datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO UTC timestamp ending in Z.") from error


def _job_scope_error(job: BackgroundJob, run: EngineRunRecord) -> str:
    """Return a scope error when a job does not match its engine run."""
    if (
        job.project_id != run.project_id
        or job.story_id != run.story_id
        or job.import_id != run.import_id
    ):
        return "Background job scope does not match engine run scope."
    expected_job_ref = f"queue://{job.job_id}"
    if run.job_ref != expected_job_ref:
        return "Background job reference does not match engine run job_ref."
    return ""


def _error_summary(error: Exception) -> str:
    """Return a short stable worker error summary."""
    message = str(error).strip()
    if not message:
        return error.__class__.__name__
    return message[:500]

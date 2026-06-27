"""Models for Aevryn background jobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

BackgroundJobKind = Literal["process_import"]
BackgroundJobStatus = Literal["queued", "running", "succeeded", "failed"]

@dataclass(frozen=True, slots=True)
class BackgroundQueueSnapshot:
    """Deterministic queue status summary for platform observability.

    Attributes:
        total_jobs: Total jobs known to the queue.
        queued_jobs: Jobs waiting to be claimed.
        running_jobs: Jobs currently claimed by workers.
        succeeded_jobs: Jobs completed successfully.
        failed_jobs: Jobs completed with failure.
        next_job_id: Next queued job that would be claimed, if any.
    """

    total_jobs: int
    queued_jobs: int
    running_jobs: int
    succeeded_jobs: int
    failed_jobs: int
    next_job_id: str = ""

    def __post_init__(self) -> None:
        """Validate queue snapshot counts."""
        counts = (
            self.total_jobs,
            self.queued_jobs,
            self.running_jobs,
            self.succeeded_jobs,
            self.failed_jobs,
        )
        if any(isinstance(count, bool) or count < 0 for count in counts):
            raise ValueError("Background queue snapshot counts must be non-negative.")
        if self.total_jobs != (
            self.queued_jobs
            + self.running_jobs
            + self.succeeded_jobs
            + self.failed_jobs
        ):
            raise ValueError("Background queue snapshot total does not match counts.")
        if self.next_job_id:
            _require_machine_token(self.next_job_id, "Background queue next job ID")



@dataclass(frozen=True, slots=True)
class BackgroundWorkerRunSummary:
    """Summary of a worker drain loop.

    Attributes:
        claimed_jobs: Number of jobs claimed from the queue.
        succeeded_jobs: Number of claimed jobs that succeeded.
        failed_jobs: Number of claimed jobs that failed.
    """

    claimed_jobs: int
    succeeded_jobs: int
    failed_jobs: int

    def __post_init__(self) -> None:
        """Validate worker run summary counts."""
        counts = (self.claimed_jobs, self.succeeded_jobs, self.failed_jobs)
        if any(isinstance(count, bool) or count < 0 for count in counts):
            raise ValueError("Background worker summary counts must be non-negative.")
        if self.claimed_jobs != self.succeeded_jobs + self.failed_jobs:
            raise ValueError("Background worker summary counts do not match.")


@dataclass(frozen=True, slots=True)
class BackgroundJob:
    """One queued platform job.

    Attributes:
        job_id: Permanent queue identity for the job.
        kind: Worker action to perform.
        run_id: Engine run record controlled by this job.
        project_id: Project scope for the job.
        story_id: Story scope for the job.
        import_id: Import scope for the job.
        status: Current queue lifecycle status.
        queued_at: UTC timestamp when the job was submitted.
        status_updated_at: UTC timestamp for the latest status change.
        attempts: Number of worker attempts already made.
        max_attempts: Maximum attempts before the job must fail.
        error_summary: Failure summary for failed jobs.
    """

    job_id: str
    kind: BackgroundJobKind
    run_id: str
    project_id: str
    story_id: str
    import_id: str
    status: BackgroundJobStatus
    queued_at: str
    status_updated_at: str
    attempts: int = 0
    max_attempts: int = 1
    error_summary: str = ""

    def __post_init__(self) -> None:
        """Validate background job identity, scope, and lifecycle fields."""
        _require_machine_token(self.job_id, "Background job ID")
        if self.kind != "process_import":
            raise ValueError("Background job kind is invalid.")
        _require_machine_token(self.run_id, "Background job run ID")
        _require_machine_token(self.project_id, "Background job project ID")
        _require_machine_token(self.story_id, "Background job story ID")
        _require_machine_token(self.import_id, "Background job import ID")
        if self.status not in {"queued", "running", "succeeded", "failed"}:
            raise ValueError("Background job status is invalid.")
        queued_at = _require_timestamp(self.queued_at, "Background job queued_at")
        status_updated_at = _require_timestamp(
            self.status_updated_at,
            "Background job status_updated_at",
        )
        if status_updated_at < queued_at:
            raise ValueError("Background job status_updated_at cannot be before queued_at.")
        if isinstance(self.attempts, bool) or self.attempts < 0:
            raise ValueError("Background job attempts must be a non-negative integer.")
        if isinstance(self.max_attempts, bool) or self.max_attempts < 1:
            raise ValueError("Background job max_attempts must be a positive integer.")
        if self.attempts > self.max_attempts:
            raise ValueError("Background job attempts cannot exceed max_attempts.")
        if self.status == "queued" and self.attempts != 0:
            raise ValueError("Queued background jobs cannot have attempts.")
        if self.status == "failed" and not self.error_summary:
            raise ValueError("Failed background jobs require an error summary.")
        if self.status != "failed" and self.error_summary:
            raise ValueError("Only failed background jobs can store an error summary.")


def _require_machine_token(value: str, label: str) -> None:
    """Require a stable machine-readable token."""
    if not isinstance(value, str) or not value.replace("_", "").isalnum():
        raise ValueError(f"{label} must be a machine-readable token.")
    if value[0].isdigit():
        raise ValueError(f"{label} cannot start with a digit.")


def _require_timestamp(value: str, label: str) -> datetime:
    """Require and return a UTC timestamp string ending in Z."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} cannot be blank.")
    if "T" not in value or not value.endswith("Z"):
        raise ValueError(f"{label} must be an ISO UTC timestamp ending in Z.")
    try:
        return datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO UTC timestamp ending in Z.") from error

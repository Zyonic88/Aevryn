"""PostgreSQL-backed background job queue."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable
from typing import Any, cast

from aevryn.persistence.repository import PersistenceError
from aevryn.workers.models import BackgroundJob, BackgroundQueueSnapshot
from aevryn.workers.queue import (
    DuplicateJobError,
    InvalidJobTransitionError,
    JobNotFoundError,
    _require_transition_timestamp_not_before_current,
)

logger = logging.getLogger(__name__)

ConnectFactory = Callable[[str], Any]


class PostgresqlBackgroundJobQueue:
    """Durable PostgreSQL implementation of the background job queue contract."""

    def __init__(
        self,
        database_url: str,
        *,
        connect_factory: ConnectFactory | None = None,
    ) -> None:
        """Create a durable queue bound to the Project Database."""
        self._database_url = _required_database_url(database_url)
        self._connect_factory = connect_factory or _default_connect_factory()

    def enqueue(self, job: BackgroundJob) -> None:
        """Add a queued job to the durable queue."""
        if job.status != "queued":
            raise InvalidJobTransitionError("Only queued jobs can be enqueued.")
        with self._connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO background_jobs (
                            job_id,
                            kind,
                            run_id,
                            project_id,
                            story_id,
                            import_id,
                            status,
                            queued_at,
                            status_updated_at,
                            attempts,
                            max_attempts,
                            error_summary
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """,
                        _job_values(job),
                    )
                connection.commit()
            except Exception as error:
                connection.rollback()
                if _is_unique_violation(error):
                    raise DuplicateJobError(
                        f"Duplicate background job: {job.job_id}"
                    ) from error
                raise
        logger.debug("background_job_enqueued", extra={"job_id": job.job_id})

    def claim_next(self, claimed_at: str) -> BackgroundJob | None:
        """Claim the next queued job in deterministic FIFO order."""
        with self._connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            job_id,
                            kind,
                            run_id,
                            project_id,
                            story_id,
                            import_id,
                            status,
                            queued_at,
                            status_updated_at,
                            attempts,
                            max_attempts,
                            error_summary
                        FROM background_jobs
                        WHERE status = 'queued'
                        ORDER BY queued_at, job_id
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED;
                        """
                    )
                    row = cursor.fetchone()
                    if row is None:
                        connection.commit()
                        return None
                    job = _job_from_row(row)
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
                    cursor.execute(
                        """
                        UPDATE background_jobs
                        SET
                            status = %s,
                            status_updated_at = %s,
                            attempts = %s,
                            error_summary = %s
                        WHERE job_id = %s;
                        """,
                        (
                            claimed.status,
                            claimed.status_updated_at,
                            claimed.attempts,
                            claimed.error_summary,
                            claimed.job_id,
                        ),
                    )
                    _require_updated_row(cursor, claimed.job_id)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        logger.debug("background_job_claimed", extra={"job_id": claimed.job_id})
        return claimed

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
        self._update_terminal_job(completed)
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
        self._update_terminal_job(failed)
        logger.debug("background_job_failed", extra={"job_id": job_id})
        return failed

    def get(self, job_id: str) -> BackgroundJob:
        """Return a job by ID."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        job_id,
                        kind,
                        run_id,
                        project_id,
                        story_id,
                        import_id,
                        status,
                        queued_at,
                        status_updated_at,
                        attempts,
                        max_attempts,
                        error_summary
                    FROM background_jobs
                    WHERE job_id = %s;
                    """,
                    (job_id,),
                )
                row = cursor.fetchone()
        if row is None:
            raise JobNotFoundError(f"Unknown background job: {job_id}")
        return _job_from_row(row)

    def has_job(self, job_id: str) -> bool:
        """Return whether a job ID already exists."""
        try:
            self.get(job_id)
        except JobNotFoundError:
            return False
        return True

    def list_jobs(self) -> tuple[BackgroundJob, ...]:
        """Return all jobs in deterministic FIFO order."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        job_id,
                        kind,
                        run_id,
                        project_id,
                        story_id,
                        import_id,
                        status,
                        queued_at,
                        status_updated_at,
                        attempts,
                        max_attempts,
                        error_summary
                    FROM background_jobs
                    ORDER BY queued_at, job_id;
                    """
                )
                rows = cursor.fetchall()
        return tuple(_job_from_row(row) for row in rows)

    def delete_project_jobs(self, project_id: str) -> int:
        """Delete all jobs scoped to a hard-deleted project."""
        return self._delete_scoped_jobs("project_id", project_id)

    def delete_story_jobs(self, story_id: str) -> int:
        """Delete all jobs scoped to a hard-deleted story."""
        return self._delete_scoped_jobs("story_id", story_id)

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

    def _connect(self) -> Any:
        """Return a new PostgreSQL connection."""
        return self._connect_factory(self._database_url)

    def _delete_scoped_jobs(self, column_name: str, scope_id: str) -> int:
        """Delete jobs for one trusted machine-token scope."""
        if column_name not in {"project_id", "story_id"}:
            raise ValueError("Unsupported queue deletion scope.")
        with self._connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"DELETE FROM background_jobs WHERE {column_name} = %s;",  # nosec B608
                        (scope_id,),
                    )
                    deleted_count = int(cursor.rowcount)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        logger.debug(
            "background_jobs_deleted",
            extra={"scope_column": column_name, "deleted_count": deleted_count},
        )
        return deleted_count

    def _update_terminal_job(self, job: BackgroundJob) -> None:
        """Persist a succeeded or failed job state."""
        with self._connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE background_jobs
                        SET
                            status = %s,
                            status_updated_at = %s,
                            attempts = %s,
                            error_summary = %s
                        WHERE job_id = %s;
                        """,
                        (
                            job.status,
                            job.status_updated_at,
                            job.attempts,
                            job.error_summary,
                            job.job_id,
                        ),
                    )
                    _require_updated_row(cursor, job.job_id)
                connection.commit()
            except Exception:
                connection.rollback()
                raise


def _required_database_url(database_url: str) -> str:
    """Return a nonblank PostgreSQL database URL."""
    if not isinstance(database_url, str):
        raise ValueError("PostgreSQL database URL cannot be blank.")
    normalized_url = _normalized_database_url(database_url)
    if not normalized_url:
        raise ValueError("PostgreSQL database URL cannot be blank.")
    if not normalized_url.startswith(("postgresql://", "postgres://")):
        raise ValueError("PostgreSQL database URL must use postgresql:// or postgres://.")
    return normalized_url


def _normalized_database_url(database_url: str) -> str:
    """Trim copy/paste wrapping without weakening URL validation."""
    normalized_url = database_url.strip()
    if len(normalized_url) >= 2 and normalized_url[0] == normalized_url[-1]:
        if normalized_url[0] in {"'", '"'}:
            normalized_url = normalized_url[1:-1].strip()
    return normalized_url


def _default_connect_factory() -> ConnectFactory:
    """Return psycopg's connect function, or raise with install guidance."""
    try:
        psycopg = importlib.import_module("psycopg")
    except ModuleNotFoundError as error:
        raise PersistenceError(
            "psycopg is required for the PostgreSQL background job queue. "
            "Install the Aevryn postgresql optional dependencies."
        ) from error

    def connect(database_url: str) -> Any:
        return psycopg.connect(database_url, prepare_threshold=None)

    return cast(ConnectFactory, connect)


def _job_values(job: BackgroundJob) -> tuple[object, ...]:
    """Return PostgreSQL parameter values for one job."""
    return (
        job.job_id,
        job.kind,
        job.run_id,
        job.project_id,
        job.story_id,
        job.import_id,
        job.status,
        job.queued_at,
        job.status_updated_at,
        job.attempts,
        job.max_attempts,
        job.error_summary,
    )


def _job_from_row(row: Any) -> BackgroundJob:
    """Convert one PostgreSQL row to a background job."""
    (
        job_id,
        kind,
        run_id,
        project_id,
        story_id,
        import_id,
        status,
        queued_at,
        status_updated_at,
        attempts,
        max_attempts,
        error_summary,
    ) = row
    return BackgroundJob(
        job_id=job_id,
        kind=kind,
        run_id=run_id,
        project_id=project_id,
        story_id=story_id,
        import_id=import_id,
        status=status,
        queued_at=_timestamp_string(queued_at),
        status_updated_at=_timestamp_string(status_updated_at),
        attempts=attempts,
        max_attempts=max_attempts,
        error_summary=error_summary or "",
    )


def _timestamp_string(value: Any) -> str:
    """Return a UTC timestamp string from PostgreSQL or test values."""
    if isinstance(value, str):
        return value
    isoformat = getattr(value, "isoformat", None)
    if not callable(isoformat):
        raise PersistenceError("Background job timestamp must be a string or datetime value.")
    timestamp = isoformat()
    if not isinstance(timestamp, str):
        raise PersistenceError("Background job timestamp conversion must return text.")
    return timestamp.replace("+00:00", "Z")


def _is_unique_violation(error: Exception) -> bool:
    """Return whether a database error is a duplicate primary key failure."""
    sqlstate = getattr(error, "sqlstate", "")
    if sqlstate == "23505":
        return True
    diagnostic = getattr(error, "diag", None)
    return getattr(diagnostic, "sqlstate", "") == "23505"


def _require_updated_row(cursor: Any, job_id: str) -> None:
    """Require one job row to have been updated."""
    if int(cursor.rowcount) != 1:
        raise JobNotFoundError(f"Background job disappeared during update: {job_id}")

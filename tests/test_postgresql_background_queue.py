"""Tests for the durable PostgreSQL background queue adapter."""

from __future__ import annotations

import pytest

from aevryn.persistence import PersistenceError
from aevryn.workers import (
    BackgroundJob,
    DuplicateJobError,
    InvalidJobTransitionError,
    JobNotFoundError,
    PostgresqlBackgroundJobQueue,
)
from aevryn.workers import postgresql_queue as queue_postgresql


def queued_job(job_id: str = "job_demo") -> BackgroundJob:
    """Return a valid queued process-import job."""
    return BackgroundJob(
        job_id=job_id,
        kind="process_import",
        run_id=f"run_{job_id}",
        project_id="project_demo",
        story_id="story_demo",
        import_id="import_demo",
        status="queued",
        queued_at="2026-07-13T00:00:00Z",
        status_updated_at="2026-07-13T00:00:00Z",
        max_attempts=3,
    )


def test_postgresql_background_queue_runs_durable_lifecycle() -> None:
    """The PostgreSQL queue adapter should persist queue lifecycle state."""
    connection = FakeConnection()
    queue = PostgresqlBackgroundJobQueue(
        "postgresql://example.invalid/aevryn",
        connect_factory=lambda _: connection,
    )

    queue.enqueue(queued_job("job_alpha"))
    queue.enqueue(queued_job("job_beta"))
    claimed = queue.claim_next("2026-07-13T00:01:00Z")
    completed = queue.complete("job_alpha", "2026-07-13T00:02:00Z")

    assert claimed is not None
    assert claimed.job_id == "job_alpha"
    assert claimed.status == "running"
    assert claimed.attempts == 1
    assert completed.status == "succeeded"
    assert queue.get("job_alpha").status == "succeeded"
    assert queue.get("job_beta").status == "queued"
    assert queue.has_job("job_alpha") is True
    assert queue.has_job("job_missing") is False
    assert queue.snapshot().queued_jobs == 1
    assert queue.snapshot().succeeded_jobs == 1
    assert queue.snapshot().next_job_id == "job_beta"
    assert connection.commits == 4
    assert connection.rollbacks == 0


def test_postgresql_background_queue_rejects_duplicate_jobs() -> None:
    """Duplicate durable queue IDs should use the queue contract error."""
    connection = FakeConnection()
    queue = PostgresqlBackgroundJobQueue(
        "postgresql://example.invalid/aevryn",
        connect_factory=lambda _: connection,
    )

    queue.enqueue(queued_job("job_alpha"))

    with pytest.raises(DuplicateJobError, match="Duplicate background job"):
        queue.enqueue(queued_job("job_alpha"))

    assert connection.rollbacks == 1


def test_postgresql_background_queue_rejects_invalid_transitions() -> None:
    """Terminal transitions should require running jobs and monotonic timestamps."""
    connection = FakeConnection()
    queue = PostgresqlBackgroundJobQueue(
        "postgresql://example.invalid/aevryn",
        connect_factory=lambda _: connection,
    )
    queue.enqueue(queued_job("job_alpha"))

    with pytest.raises(InvalidJobTransitionError, match="Only running jobs can succeed"):
        queue.complete("job_alpha", "2026-07-13T00:02:00Z")

    queue.claim_next("2026-07-13T00:03:00Z")

    with pytest.raises(InvalidJobTransitionError, match="cannot be before current status"):
        queue.fail("job_alpha", "2026-07-13T00:02:00Z", "Timed out.")


def test_postgresql_background_queue_reports_missing_jobs() -> None:
    """Missing durable jobs should use the queue contract error."""
    queue = PostgresqlBackgroundJobQueue(
        "postgresql://example.invalid/aevryn",
        connect_factory=lambda _: FakeConnection(),
    )

    with pytest.raises(JobNotFoundError, match="Unknown background job"):
        queue.get("job_missing")


def test_postgresql_background_queue_deletes_scoped_jobs() -> None:
    """Durable queue rows should be purgeable during hard deletes."""
    connection = FakeConnection()
    queue = PostgresqlBackgroundJobQueue(
        "postgresql://example.invalid/aevryn",
        connect_factory=lambda _: connection,
    )
    queue.enqueue(queued_job("job_alpha"))
    queue.enqueue(
        BackgroundJob(
            job_id="job_other",
            kind="process_import",
            run_id="run_other",
            project_id="project_other",
            story_id="story_other",
            import_id="import_other",
            status="queued",
            queued_at="2026-07-13T00:00:00Z",
            status_updated_at="2026-07-13T00:00:00Z",
            max_attempts=3,
        )
    )

    assert queue.delete_story_jobs("story_demo") == 1
    assert queue.delete_project_jobs("project_missing") == 0

    with pytest.raises(JobNotFoundError):
        queue.get("job_alpha")
    assert queue.get("job_other").project_id == "project_other"


def test_postgresql_background_queue_rejects_disappearing_update_rows() -> None:
    """Durable queue updates should not report success when no row changed."""
    connection = FakeConnection()
    queue = PostgresqlBackgroundJobQueue(
        "postgresql://example.invalid/aevryn",
        connect_factory=lambda _: connection,
    )
    queue.enqueue(queued_job("job_alpha"))
    queue.claim_next("2026-07-13T00:01:00Z")
    connection.drop_on_update_job_ids.add("job_alpha")

    with pytest.raises(JobNotFoundError, match="disappeared during update"):
        queue.complete("job_alpha", "2026-07-13T00:02:00Z")

    assert connection.rollbacks == 1


def test_postgresql_background_queue_requires_psycopg_when_no_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The durable queue should explain the optional PostgreSQL dependency."""

    def missing_psycopg(module_name: str) -> object:
        if module_name == "psycopg":
            raise ModuleNotFoundError(module_name)
        raise AssertionError(f"Unexpected import: {module_name}")

    monkeypatch.setattr(
        "aevryn.workers.postgresql_queue.importlib.import_module",
        missing_psycopg,
    )

    with pytest.raises(PersistenceError, match="psycopg is required"):
        PostgresqlBackgroundJobQueue("postgresql://example.invalid/aevryn")


def test_postgresql_background_queue_normalizes_pasted_database_url() -> None:
    """Durable queue config should tolerate whitespace around PostgreSQL URLs."""
    assert queue_postgresql._required_database_url(
        "  postgresql://example.invalid/aevryn  "
    ) == "postgresql://example.invalid/aevryn"


class FakeUniqueViolation(Exception):
    """Test double for PostgreSQL duplicate-key errors."""

    sqlstate = "23505"


class FakeConnection:
    """Minimal connection test double for queue SQL."""

    def __init__(self) -> None:
        self.jobs: dict[str, tuple[object, ...]] = {}
        self.commits = 0
        self.rollbacks = 0
        self.drop_on_update_job_ids: set[str] = set()

    def __enter__(self) -> FakeConnection:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeCursor:
    """Minimal cursor test double for queue SQL."""

    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self._fetchone: tuple[object, ...] | None = None
        self._fetchall: list[tuple[object, ...]] = []
        self.rowcount = 0

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, statement: str, params: tuple[object, ...] = ()) -> None:
        normalized = " ".join(statement.lower().split())
        if normalized.startswith("insert into background_jobs"):
            job_id = str(params[0])
            if job_id in self.connection.jobs:
                raise FakeUniqueViolation("duplicate job")
            self.connection.jobs[job_id] = params
            return
        if "from background_jobs where status = 'queued'" in normalized:
            queued = [
                row
                for row in self.connection.jobs.values()
                if row[_STATUS_INDEX] == "queued"
            ]
            self._fetchone = sorted(queued, key=lambda row: (row[_QUEUED_AT_INDEX], row[0]))[
                0
            ] if queued else None
            return
        if normalized.startswith("update background_jobs"):
            job_id = str(params[4])
            if job_id in self.connection.drop_on_update_job_ids:
                self.connection.jobs.pop(job_id, None)
                self.rowcount = 0
                return
            existing = self.connection.jobs[job_id]
            self.connection.jobs[job_id] = (
                *existing[:_STATUS_INDEX],
                params[0],
                existing[_QUEUED_AT_INDEX],
                params[1],
                params[2],
                existing[_MAX_ATTEMPTS_INDEX],
                params[3],
            )
            self.rowcount = 1
            return
        if normalized.startswith("delete from background_jobs where"):
            column_name = normalized.split(" where ", 1)[1].split(" = ", 1)[0]
            column_index = {
                "project_id": _PROJECT_ID_INDEX,
                "story_id": _STORY_ID_INDEX,
            }[column_name]
            scope_id = str(params[0])
            deleted_ids = [
                job_id
                for job_id, row in self.connection.jobs.items()
                if row[column_index] == scope_id
            ]
            for job_id in deleted_ids:
                del self.connection.jobs[job_id]
            self.rowcount = len(deleted_ids)
            return
        if "from background_jobs where job_id = %s" in normalized:
            self._fetchone = self.connection.jobs.get(str(params[0]))
            return
        if "from background_jobs order by queued_at, job_id" in normalized:
            self._fetchall = sorted(
                self.connection.jobs.values(),
                key=lambda row: (row[_QUEUED_AT_INDEX], row[0]),
            )
            return
        raise AssertionError(f"Unexpected SQL: {statement}")

    def fetchone(self) -> tuple[object, ...] | None:
        return self._fetchone

    def fetchall(self) -> list[tuple[object, ...]]:
        return self._fetchall


_STATUS_INDEX = 6
_QUEUED_AT_INDEX = 7
_PROJECT_ID_INDEX = 3
_STORY_ID_INDEX = 4
_MAX_ATTEMPTS_INDEX = 10

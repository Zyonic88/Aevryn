"""Tests for Aevryn V2 Phase 3 background worker foundations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from aevryn.persistence import (
    DuplicateRecordError,
    EngineRunRecord,
    ImportRecord,
    InMemoryProjectRepository,
    JsonProjectRepository,
    ProjectRecord,
    StoryRecord,
    UserRecord,
)
from aevryn.workers import (
    BackgroundJob,
    BackgroundJobHandler,
    BackgroundJobQueue,
    BackgroundJobService,
    BackgroundJobStatus,
    BackgroundWorker,
    BackgroundWorkerRunSummary,
    DuplicateJobError,
    InMemoryJobQueue,
    InvalidJobTransitionError,
    JobNotFoundError,
    JobQueueError,
)

NOW = "2026-06-27T00:00:00Z"
STARTED = "2026-06-27T00:01:00Z"
FINISHED = "2026-06-27T00:02:00Z"


def test_background_job_service_records_pending_run_and_enqueues_job() -> None:
    """Job submission should persist a pending run before worker execution."""
    repository = seeded_repository()
    queue = InMemoryJobQueue()
    service = BackgroundJobService(
        repository=repository,
        queue=queue,
        engine_version="0.1.0",
    )

    job = service.submit_import_processing_job(
        job_id="job_demo",
        run_id="run_demo",
        project_id="project_demo",
        story_id="story_demo",
        import_id="import_demo",
        queued_at=NOW,
    )

    assert job.status == "queued"
    assert queue.list_jobs() == (job,)
    run = repository.get_engine_run_for_worker("run_demo")
    assert run.status == "pending"
    assert run.job_ref == "queue://job_demo"


def test_background_queue_claims_jobs_in_fifo_order() -> None:
    """The in-memory queue should be deterministic."""
    queue = InMemoryJobQueue()
    first = background_job(job_id="job_first", run_id="run_first")
    second = background_job(job_id="job_second", run_id="run_second")

    queue.enqueue(first)
    queue.enqueue(second)

    claimed = queue.claim_next(claimed_at=STARTED)

    assert claimed is not None
    assert claimed.job_id == "job_first"
    assert claimed.status == "running"
    assert claimed.attempts == 1
    second_claimed = queue.claim_next(claimed_at=STARTED)
    assert second_claimed is not None
    assert second_claimed.job_id == "job_second"


def test_background_queue_snapshot_reports_status_counts() -> None:
    """Queue snapshots should support deterministic platform observability."""
    queue = InMemoryJobQueue()
    queue.enqueue(background_job(job_id="job_first", run_id="run_first"))
    queue.enqueue(background_job(job_id="job_second", run_id="run_second"))

    assert queue.snapshot().total_jobs == 2
    assert queue.snapshot().queued_jobs == 2
    assert queue.snapshot().next_job_id == "job_first"

    claimed = queue.claim_next(claimed_at=STARTED)
    assert claimed is not None
    queue.complete(claimed.job_id, completed_at=FINISHED)

    snapshot = queue.snapshot()
    assert snapshot.total_jobs == 2
    assert snapshot.queued_jobs == 1
    assert snapshot.running_jobs == 0
    assert snapshot.succeeded_jobs == 1
    assert snapshot.failed_jobs == 0
    assert snapshot.next_job_id == "job_second"


def test_background_job_model_rejects_invalid_lifecycle_values() -> None:
    """Job records should reject impossible lifecycle metadata."""
    with pytest.raises(ValueError, match="status_updated_at cannot be before"):
        background_job_with(status_updated_at="2026-06-26T23:59:59Z")

    with pytest.raises(ValueError, match="Queued background jobs cannot"):
        background_job_with(attempts=1)

    with pytest.raises(ValueError, match="Failed background jobs require"):
        background_job_with(status="failed", attempts=1)

    with pytest.raises(ValueError, match="Only failed background jobs"):
        background_job_with(error_summary="Not failed.")


def test_worker_public_exports_include_adapter_protocols_and_queue_errors() -> None:
    """The worker package should expose protocols and failures for API adapters."""
    queue_contract: BackgroundJobQueue = InMemoryJobQueue()
    handler_contract: BackgroundJobHandler = RecordingHandler()

    assert queue_contract.snapshot().total_jobs == 0
    handler_contract.process(background_job())
    assert issubclass(JobQueueError, Exception)
    assert issubclass(DuplicateJobError, JobQueueError)
    assert issubclass(InvalidJobTransitionError, JobQueueError)
    assert issubclass(JobNotFoundError, JobQueueError)


def test_background_queue_rejects_invalid_lifecycle_transitions() -> None:
    """Queue states should move forward only."""
    queue = InMemoryJobQueue()
    queue.enqueue(background_job())

    with pytest.raises(InvalidJobTransitionError, match="running jobs"):
        queue.complete("job_demo", completed_at=FINISHED)

    queue.claim_next(claimed_at=STARTED)
    queue.complete("job_demo", completed_at=FINISHED)

    with pytest.raises(InvalidJobTransitionError, match="running jobs"):
        queue.fail("job_demo", failed_at=FINISHED, error_summary="Already complete.")


def test_background_queue_rejects_non_monotonic_completion_timestamps() -> None:
    """Direct queue transitions should not move status timestamps backward."""
    queue = InMemoryJobQueue()
    queue.enqueue(background_job())
    queue.claim_next(claimed_at=FINISHED)

    with pytest.raises(InvalidJobTransitionError, match="completed_at cannot be before"):
        queue.complete("job_demo", completed_at=STARTED)

    assert queue.get("job_demo").status == "running"


def test_background_queue_rejects_non_monotonic_failure_timestamps() -> None:
    """Failed queue transitions should not move status timestamps backward."""
    queue = InMemoryJobQueue()
    queue.enqueue(background_job())
    queue.claim_next(claimed_at=FINISHED)

    with pytest.raises(InvalidJobTransitionError, match="failed_at cannot be before"):
        queue.fail("job_demo", failed_at=STARTED, error_summary="Too early.")

    assert queue.get("job_demo").status == "running"


def test_background_queue_rejects_duplicate_and_unknown_jobs() -> None:
    """Queue failures should be explicit."""
    queue = InMemoryJobQueue()
    queue.enqueue(background_job())

    with pytest.raises(DuplicateJobError, match="Duplicate background job"):
        queue.enqueue(background_job())

    with pytest.raises(JobNotFoundError, match="Unknown background job"):
        queue.get("job_missing")


def test_background_job_service_marks_run_failed_when_queue_enqueue_fails() -> None:
    """Queue adapter failures should not leave pending engine runs behind."""
    repository = seeded_repository()
    queue = FailingEnqueueQueue()

    with pytest.raises(RuntimeError, match="Queue unavailable."):
        BackgroundJobService(repository, queue, "0.1.0").submit_import_processing_job(
            job_id="job_demo",
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            queued_at=NOW,
        )

    run = repository.get_engine_run_for_worker("run_demo")
    assert run.status == "failed"
    assert run.finished_at == NOW
    assert run.error_summary == "Queue unavailable."


def test_background_job_service_rejects_duplicate_run_before_queue_write() -> None:
    """Duplicate run IDs should not enqueue orphaned jobs."""
    repository = seeded_repository()
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            status="pending",
            engine_version="0.1.0",
            started_at=NOW,
            status_updated_at=NOW,
            job_ref="queue://job_existing",
        )
    )
    queue = InMemoryJobQueue()

    with pytest.raises(DuplicateRecordError, match="Duplicate engine run"):
        BackgroundJobService(repository, queue, "0.1.0").submit_import_processing_job(
            job_id="job_demo",
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            queued_at=NOW,
        )

    assert queue.list_jobs() == ()


def test_background_job_service_rejects_duplicate_job_before_run_write() -> None:
    """Duplicate job IDs should not create orphaned pending engine runs."""
    repository = seeded_repository()
    queue = InMemoryJobQueue()
    queue.enqueue(background_job())
    service = BackgroundJobService(repository, queue, "0.1.0")

    with pytest.raises(DuplicateJobError, match="Duplicate background job"):
        service.submit_import_processing_job(
            job_id="job_demo",
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            queued_at=NOW,
        )

    assert repository.list_engine_runs_for_project("user_demo", "project_demo") == ()


def test_background_worker_rejects_job_scope_mismatch_before_handler_execution() -> None:
    """Workers should fail jobs that do not match their persisted engine run scope."""
    repository = seeded_repository()
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            status="pending",
            engine_version="0.1.0",
            started_at=NOW,
            status_updated_at=NOW,
            job_ref="queue://job_demo",
        )
    )
    queue = InMemoryJobQueue()
    queue.enqueue(
        BackgroundJob(
            job_id="job_demo",
            kind="process_import",
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_other",
            import_id="import_demo",
            status="queued",
            queued_at=NOW,
            status_updated_at=NOW,
        )
    )
    handler = RecordingHandler()

    final_job = BackgroundWorker(repository, queue, handler).process_next(
        started_at=STARTED,
        finished_at=FINISHED,
    )

    assert final_job is not None
    assert final_job.status == "failed"
    assert final_job.error_summary == (
        "Background job scope does not match engine run scope."
    )
    assert handler.processed_job_ids == ()
    run = repository.get_engine_run_for_worker("run_demo")
    assert run.status == "failed"
    assert run.error_summary == final_job.error_summary


def test_background_worker_rejects_missing_job_ref_before_handler_execution() -> None:
    """Workers should require engine runs to reference the claimed queue job."""
    repository = seeded_repository()
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            status="pending",
            engine_version="0.1.0",
            started_at=NOW,
            status_updated_at=NOW,
        )
    )
    queue = InMemoryJobQueue()
    queue.enqueue(background_job())
    handler = RecordingHandler()

    final_job = BackgroundWorker(repository, queue, handler).process_next(
        started_at=STARTED,
        finished_at=FINISHED,
    )

    assert final_job is not None
    assert final_job.status == "failed"
    assert final_job.error_summary == (
        "Background job reference does not match engine run job_ref."
    )
    assert handler.processed_job_ids == ()


def test_background_worker_rejects_job_ref_mismatch_before_handler_execution() -> None:
    """Workers should fail jobs whose run points to a different queue reference."""
    repository = seeded_repository()
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            status="pending",
            engine_version="0.1.0",
            started_at=NOW,
            status_updated_at=NOW,
            job_ref="queue://job_other",
        )
    )
    queue = InMemoryJobQueue()
    queue.enqueue(background_job())
    handler = RecordingHandler()

    final_job = BackgroundWorker(repository, queue, handler).process_next(
        started_at=STARTED,
        finished_at=FINISHED,
    )

    assert final_job is not None
    assert final_job.status == "failed"
    assert final_job.error_summary == (
        "Background job reference does not match engine run job_ref."
    )
    assert handler.processed_job_ids == ()
    assert repository.get_engine_run_for_worker("run_demo").status == "failed"


def test_background_worker_status_updates_persist_in_json_repository(
    tmp_path: Path,
) -> None:
    """Worker lifecycle updates should survive durable repository reloads."""
    database_path = tmp_path / "project_database.json"
    repository = JsonProjectRepository(database_path)
    seed_repository(repository)
    queue = InMemoryJobQueue()
    BackgroundJobService(repository, queue, "0.1.0").submit_import_processing_job(
        job_id="job_demo",
        run_id="run_demo",
        project_id="project_demo",
        story_id="story_demo",
        import_id="import_demo",
        queued_at=NOW,
    )

    BackgroundWorker(repository, queue, RecordingHandler()).process_next(
        started_at=STARTED,
        finished_at=FINISHED,
    )

    reloaded = JsonProjectRepository(database_path)
    run = reloaded.get_engine_run_for_worker("run_demo")
    assert run.status == "succeeded"
    assert run.status_updated_at == FINISHED
    assert run.finished_at == FINISHED


def test_background_worker_marks_run_succeeded_after_handler_completes() -> None:
    """Workers should synchronize queue status and persisted run status."""
    repository = seeded_repository()
    queue = InMemoryJobQueue()
    BackgroundJobService(repository, queue, "0.1.0").submit_import_processing_job(
        job_id="job_demo",
        run_id="run_demo",
        project_id="project_demo",
        story_id="story_demo",
        import_id="import_demo",
        queued_at=NOW,
    )
    handler = RecordingHandler()

    final_job = BackgroundWorker(repository, queue, handler).process_next(
        started_at=STARTED,
        finished_at=FINISHED,
    )

    assert final_job is not None
    assert final_job.status == "succeeded"
    assert handler.processed_job_ids == ("job_demo",)
    run = repository.get_engine_run_for_worker("run_demo")
    assert run.status == "succeeded"
    assert run.status_updated_at == FINISHED
    assert run.finished_at == FINISHED


def test_background_worker_marks_run_failed_after_handler_error() -> None:
    """Worker failures should be visible in queue and run records."""
    repository = seeded_repository()
    queue = InMemoryJobQueue()
    BackgroundJobService(repository, queue, "0.1.0").submit_import_processing_job(
        job_id="job_demo",
        run_id="run_demo",
        project_id="project_demo",
        story_id="story_demo",
        import_id="import_demo",
        queued_at=NOW,
    )

    final_job = BackgroundWorker(repository, queue, FailingHandler()).process_next(
        started_at=STARTED,
        finished_at=FINISHED,
    )

    assert final_job is not None
    assert final_job.status == "failed"
    assert final_job.error_summary == "Worker failure."
    run = repository.get_engine_run_for_worker("run_demo")
    assert run.status == "failed"
    assert run.error_summary == "Worker failure."
    assert run.finished_at == FINISHED


def test_background_worker_rejects_impossible_timestamp_order_before_claim() -> None:
    """Workers should reject bad caller timestamps before mutating queue state."""
    repository = seeded_repository()
    queue = InMemoryJobQueue()
    BackgroundJobService(repository, queue, "0.1.0").submit_import_processing_job(
        job_id="job_demo",
        run_id="run_demo",
        project_id="project_demo",
        story_id="story_demo",
        import_id="import_demo",
        queued_at=NOW,
    )

    with pytest.raises(ValueError, match="finished_at cannot be before started_at"):
        BackgroundWorker(repository, queue, RecordingHandler()).process_next(
            started_at=FINISHED,
            finished_at=STARTED,
        )

    assert queue.get("job_demo").status == "queued"
    assert repository.get_engine_run_for_worker("run_demo").status == "pending"


def test_background_worker_process_available_drains_until_idle() -> None:
    """Workers should process available jobs and return deterministic counts."""
    repository = seeded_repository()
    queue = InMemoryJobQueue()
    service = BackgroundJobService(repository, queue, "0.1.0")
    for suffix in ("one", "two"):
        service.submit_import_processing_job(
            job_id=f"job_{suffix}",
            run_id=f"run_{suffix}",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            queued_at=NOW,
        )

    summary = BackgroundWorker(repository, queue, RecordingHandler()).process_available(
        started_at=STARTED,
        finished_at=FINISHED,
        max_jobs=5,
    )

    assert summary == BackgroundWorkerRunSummary(
        claimed_jobs=2,
        succeeded_jobs=2,
        failed_jobs=0,
    )
    assert queue.snapshot().succeeded_jobs == 2


def test_background_worker_process_available_respects_max_jobs() -> None:
    """Worker drain loops should stop at the caller's explicit limit."""
    repository = seeded_repository()
    queue = InMemoryJobQueue()
    service = BackgroundJobService(repository, queue, "0.1.0")
    for suffix in ("one", "two"):
        service.submit_import_processing_job(
            job_id=f"job_{suffix}",
            run_id=f"run_{suffix}",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            queued_at=NOW,
        )

    summary = BackgroundWorker(repository, queue, RecordingHandler()).process_available(
        started_at=STARTED,
        finished_at=FINISHED,
        max_jobs=1,
    )

    assert summary.claimed_jobs == 1
    assert queue.snapshot().queued_jobs == 1
    assert queue.snapshot().next_job_id == "job_two"


def test_background_worker_process_available_rejects_invalid_max_jobs() -> None:
    """Worker drain limits should be explicit positive integers."""
    with pytest.raises(ValueError, match="max_jobs must be a positive integer"):
        BackgroundWorker(
            seeded_repository(),
            InMemoryJobQueue(),
            RecordingHandler(),
        ).process_available(
            started_at=STARTED,
            finished_at=FINISHED,
            max_jobs=0,
        )


def test_background_worker_summary_rejects_invalid_counts() -> None:
    """Worker summaries should not hide mismatched counts."""
    with pytest.raises(ValueError, match="counts do not match"):
        BackgroundWorkerRunSummary(
            claimed_jobs=2,
            succeeded_jobs=1,
            failed_jobs=0,
        )


def test_background_worker_returns_none_when_queue_is_empty() -> None:
    """Idle workers should not invent work."""
    repository = seeded_repository()
    worker = BackgroundWorker(repository, InMemoryJobQueue(), RecordingHandler())

    assert worker.process_next(started_at=STARTED, finished_at=FINISHED) is None


def test_background_worker_preserves_run_scope() -> None:
    """Worker execution should never move a run between projects or stories."""
    repository = seeded_repository()
    queue = InMemoryJobQueue()
    BackgroundJobService(repository, queue, "0.1.0").submit_import_processing_job(
        job_id="job_demo",
        run_id="run_demo",
        project_id="project_demo",
        story_id="story_demo",
        import_id="import_demo",
        queued_at=NOW,
    )

    BackgroundWorker(repository, queue, RecordingHandler()).process_next(
        started_at=STARTED,
        finished_at=FINISHED,
    )

    run = repository.get_engine_run_for_worker("run_demo")
    assert run.project_id == "project_demo"
    assert run.story_id == "story_demo"
    assert run.import_id == "import_demo"


@dataclass
class RecordingHandler:
    """Test handler that records processed jobs."""

    processed_job_ids: tuple[str, ...] = ()

    def process(self, job: BackgroundJob) -> None:
        """Record one processed job."""
        self.processed_job_ids = (*self.processed_job_ids, job.job_id)


class FailingHandler:
    """Test handler that raises a stable failure."""

    def process(self, _job: BackgroundJob) -> None:
        """Raise a deterministic worker failure."""
        raise RuntimeError("Worker failure.")


class FailingEnqueueQueue(InMemoryJobQueue):
    """Queue adapter that fails after duplicate preflight checks pass."""

    def enqueue(self, _job: BackgroundJob) -> None:
        """Raise a deterministic queue failure."""
        raise RuntimeError("Queue unavailable.")


def seeded_repository() -> InMemoryProjectRepository:
    """Return a repository with user, project, story, and import records."""
    repository = InMemoryProjectRepository()
    seed_repository(repository)
    return repository


def seed_repository(repository: InMemoryProjectRepository) -> None:
    """Seed a project repository with user, project, story, and import records."""
    repository.create_user(
        UserRecord(
            user_id="user_demo",
            email="demo@example.com",
            display_name="Demo User",
            created_at=NOW,
        )
    )
    repository.create_project(
        ProjectRecord(
            project_id="project_demo",
            owner_user_id="user_demo",
            name="Demo Project",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    repository.create_story(
        StoryRecord(
            story_id="story_demo",
            project_id="project_demo",
            title="Demo Story",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    repository.record_import(
        ImportRecord(
            import_id="import_demo",
            story_id="story_demo",
            source_id="source_demo",
            filename="chapter.txt",
            source_format="txt",
            storage_ref="storage://imports/source_demo/chapter.txt",
            chapter_count=1,
            scene_count=1,
            evidence_anchor_count=1,
            created_at=NOW,
        )
    )


def background_job(
    *,
    job_id: str = "job_demo",
    run_id: str = "run_demo",
) -> BackgroundJob:
    """Return a stable queued background job."""
    return BackgroundJob(
        job_id=job_id,
        kind="process_import",
        run_id=run_id,
        project_id="project_demo",
        story_id="story_demo",
        import_id="import_demo",
        status="queued",
        queued_at=NOW,
        status_updated_at=NOW,
    )


def background_job_with(
    *,
    status: BackgroundJobStatus = "queued",
    status_updated_at: str = NOW,
    attempts: int = 0,
    error_summary: str = "",
) -> BackgroundJob:
    """Return a background job with selected lifecycle overrides."""
    return BackgroundJob(
        job_id="job_demo",
        kind="process_import",
        run_id="run_demo",
        project_id="project_demo",
        story_id="story_demo",
        import_id="import_demo",
        status=status,
        queued_at=NOW,
        status_updated_at=status_updated_at,
        attempts=attempts,
        max_attempts=1,
        error_summary=error_summary,
    )

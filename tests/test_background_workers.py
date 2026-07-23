"""Tests for Aevryn V2 Phase 3 background worker foundations."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from aevryn.canon import CanonDatabase, CanonUpdateSummary
from aevryn.entity_resolution import ResolvedReference, SurfaceReference
from aevryn.extraction import (
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractedStateChange,
    ExtractionResult,
    SceneExtractionInput,
)
from aevryn.import_storage import ImportContentStore
from aevryn.importing import StoryImporter
from aevryn.persistence import (
    DuplicateRecordError,
    EngineRunRecord,
    ImportRecord,
    InMemoryProjectRepository,
    JsonProjectRepository,
    ProjectRecord,
    SnapshotRecord,
    StoryRecord,
    UserRecord,
)
from aevryn.projects import ProjectRunResult
from aevryn.translation import TranslatedUnit, TranslationIssue
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
    ProjectImportSnapshotHandler,
)
from aevryn.workers.service import _canon_snapshot_payload

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


def test_background_worker_logs_success_duration_without_payload(
    caplog: LogCaptureFixture,
) -> None:
    """Worker success timing logs should stay metadata-only."""
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

    with caplog.at_level(logging.INFO, logger="aevryn.workers.service"):
        final_job = BackgroundWorker(
            repository, queue, SnapshotReturningHandler()
        ).process_next(
            started_at=STARTED,
            finished_at=FINISHED,
        )

    assert final_job is not None
    assert final_job.status == "succeeded"
    worker_record = worker_log_record(caplog, "worker_processing", "succeeded")
    snapshot_record = worker_log_record(caplog, "snapshot_creation", "succeeded")
    assert_duration_log(worker_record)
    assert_duration_log(snapshot_record)
    assert getattr(worker_record, "job_id", "") == "job_demo"
    assert getattr(worker_record, "run_id", "") == "run_demo"
    assert getattr(worker_record, "snapshot_count", 0) == 1
    assert getattr(snapshot_record, "snapshot_id", "") == "snapshot_demo"
    assert getattr(snapshot_record, "snapshot_kind", "") == "canon"
    assert "Mark carried a rusty dagger" not in caplog_record_text(caplog)
    assert "serialized_output" not in caplog_record_text(caplog)


def test_background_worker_marks_run_failed_after_snapshot_store_error() -> None:
    """Snapshot persistence failures should not strand running queue jobs."""
    repository = SnapshotStoreFailingRepository()
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

    final_job = BackgroundWorker(
        repository,
        queue,
        SnapshotReturningHandler(),
    ).process_next(started_at=STARTED, finished_at=FINISHED)

    assert final_job is not None
    assert final_job.status == "failed"
    assert final_job.error_summary == "Snapshot write failed."
    run = repository.get_engine_run_for_worker("run_demo")
    assert run.status == "failed"
    assert run.error_summary == "Snapshot write failed."
    assert queue.snapshot().running_jobs == 0
    assert queue.snapshot().failed_jobs == 1


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


def test_background_worker_sanitizes_unknown_anchor_failures() -> None:
    """Worker failures should not expose internal evidence anchor IDs."""
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

    final_job = BackgroundWorker(
        repository,
        queue,
        UnknownAnchorFailingHandler(),
    ).process_next(started_at=STARTED, finished_at=FINISHED)

    assert final_job is not None
    assert final_job.status == "failed"
    assert "Unknown evidence anchor" not in final_job.error_summary
    assert "missing_anchor" not in final_job.error_summary
    assert "Import evidence could not be matched" in final_job.error_summary
    run = repository.get_engine_run_for_worker("run_demo")
    assert "Unknown evidence anchor" not in run.error_summary
    assert "missing_anchor" not in run.error_summary
    assert "split the import into smaller chapter batches" in run.error_summary


def test_background_worker_sanitizes_conflicting_fact_failures() -> None:
    """Worker failures should not expose internal fact IDs."""
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

    final_job = BackgroundWorker(
        repository,
        queue,
        ConflictingFactFailingHandler(),
    ).process_next(started_at=STARTED, finished_at=FINISHED)

    assert final_job is not None
    assert final_job.status == "failed"
    assert "Conflicting fact" not in final_job.error_summary
    assert "fact_1" not in final_job.error_summary
    assert "AI extraction produced conflicting canon facts" in final_job.error_summary
    run = repository.get_engine_run_for_worker("run_demo")
    assert "Conflicting fact" not in run.error_summary
    assert "fact_1" not in run.error_summary
    assert "review the import structure" in run.error_summary


def test_background_worker_sanitizes_duplicate_world_section_failures() -> None:
    """Worker failures should describe recoverable world-sheet presentation issues."""
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

    final_job = BackgroundWorker(
        repository,
        queue,
        DuplicateWorldSectionFailingHandler(),
    ).process_next(started_at=STARTED, finished_at=FINISHED)

    assert final_job is not None
    assert final_job.status == "failed"
    assert "World sheet section titles must be unique" not in final_job.error_summary
    assert "duplicate sections" in final_job.error_summary
    run = repository.get_engine_run_for_worker("run_demo")
    assert "World sheet section titles must be unique" not in run.error_summary
    assert "retry processing" in run.error_summary


def test_background_worker_sanitizes_provider_timeout_failures() -> None:
    """Worker failures should give actionable guidance for provider timeouts."""
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

    final_job = BackgroundWorker(
        repository,
        queue,
        ProviderTimeoutFailingHandler(),
    ).process_next(started_at=STARTED, finished_at=FINISHED)

    assert final_job is not None
    assert final_job.status == "failed"
    assert "read operation timed out" not in final_job.error_summary
    assert "AI extraction timed out" in final_job.error_summary
    run = repository.get_engine_run_for_worker("run_demo")
    assert "read operation timed out" not in run.error_summary
    assert "smaller chapter batch" in run.error_summary


def test_background_worker_logs_failure_duration_without_payload(
    caplog: LogCaptureFixture,
) -> None:
    """Worker failure timing logs should expose summaries without source payloads."""
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

    with caplog.at_level(logging.INFO, logger="aevryn.workers.service"):
        final_job = BackgroundWorker(repository, queue, FailingHandler()).process_next(
            started_at=STARTED,
            finished_at=FINISHED,
        )

    assert final_job is not None
    assert final_job.status == "failed"
    record = worker_log_record(caplog, "worker_processing", "failed")
    assert_duration_log(record)
    assert getattr(record, "error_summary", "") == "Worker failure."
    assert "Mark carried a rusty dagger" not in caplog_record_text(caplog)


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


def test_project_import_snapshot_handler_uses_injected_extractor() -> None:
    """Import processing should support the alpha AI extractor boundary."""
    repository = seeded_repository()
    extractor = RecordingSceneExtractor()
    import_content_store: ImportContentStore = StaticImportContentStore(
        b"Chapter 1\n\nLyra opened the sky gate."
    )
    handler = ProjectImportSnapshotHandler(
        repository=repository,
        import_content_store=import_content_store,
        extractor=extractor,
    )

    snapshots = handler.process(background_job())

    assert extractor.scene_ids == ("source_demo_chapter_001_scene_001",)
    assert len(snapshots) == 1
    snapshot_payload = json.loads(snapshots[0].serialized_output)
    assert snapshot_payload["accepted_entity_count"] == 1
    assert snapshot_payload["accepted_fact_count"] == 2
    assert snapshot_payload["presentation"]["scenes"][0]["title"] == "Scene 1"
    assert snapshot_payload["presentation"]["scenes"][0]["chapter_label"] == "Chapter 1"
    assert snapshot_payload["presentation"]["scenes"][0]["characters_present"]["items"] == [
        "Lyra"
    ]
    assert snapshot_payload["presentation"]["prompt_packs"][0]["scene"]["title"] == "Scene 1"
    assert snapshot_payload["presentation"]["continuity_report"]["source_id"] == "source_demo"
    assert snapshot_payload["presentation"]["export_options"][0]["export_kind"] == (
        "character_profile"
    )
    assert snapshot_payload["presentation"]["characters"][0]["display_name"] == "Lyra"
    assert snapshot_payload["timeline_changes"][0]["change_id"] == "state_fact_character_lyra_role"
    assert snapshot_payload["timeline_changes"][0] | {"change_id": ""} == {
        "attribute": "role",
        "change_id": "",
        "chapter_index": 1,
        "chapter_title": "Chapter 1",
        "entity_id": "character_lyra",
        "entity_name": "Lyra",
        "scene_index": 1,
        "scene_title": "Scene 1",
        "value": "Sky Gate Keeper",
    }
    assert "Lyra opened the sky gate" not in snapshots[0].serialized_output


def test_project_import_snapshot_humanizes_presentation_machine_ids() -> None:
    """Creator-facing snapshot presentation should not expose extraction IDs."""
    repository = seeded_repository()
    import_content_store: ImportContentStore = StaticImportContentStore(
        b"Chapter 1\n\nZhao Chen entered North Star Academy."
    )
    handler = ProjectImportSnapshotHandler(
        repository=repository,
        import_content_store=import_content_store,
        extractor=MachineIdSceneExtractor(),
    )

    snapshots = handler.process(background_job())

    snapshot_payload = json.loads(snapshots[0].serialized_output)
    presentation = snapshot_payload["presentation"]
    world_items = tuple(
        item
        for section in presentation["world"]["entity_sections"]
        for item in section["items"]
    )
    prompt_items = tuple(presentation["prompt_packs"][0]["image_prompt"]["items"])
    continuity_items = tuple(
        record["description"]
        for scene in presentation["continuity_report"]["scenes"]
        for bucket in ("new", "updated", "still_known", "invalidated")
        for record in scene[bucket]
    )

    assert "Zhao Chen is located in North Star Academy" in world_items
    assert "Character: Zhao Chen" in prompt_items
    assert all("(E1)" not in item for item in prompt_items)
    assert all("source_demo" not in item for item in prompt_items)
    assert all("_chapter_" not in item for item in prompt_items)
    assert all("Evidence anchor" not in item for item in prompt_items)
    assert all("Zhao Chen entered North Star Academy" not in item for item in prompt_items)
    assert all("Aevryn Import Bundle" not in item for item in continuity_items)
    assert all("State Valid From Event" not in item for item in continuity_items)
    assert "Zhao Chen current location: North Star Academy" in continuity_items


def test_canon_snapshot_payload_stores_stable_identity_review_reasons() -> None:
    """Phase 12 snapshot metadata should not persist resolver prose."""
    imported_source = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo Story",
        text="Chapter 1\n\nMark carried a rusty dagger.",
    )
    result = ProjectRunResult(
        imported_source=imported_source,
        database=CanonDatabase(),
        extraction_results=(
            ExtractionResult(scene_id="source_demo_chapter_001_scene_001"),
        ),
        update_summaries=(CanonUpdateSummary(),),
        identity_resolutions=(
            ResolvedReference(
                reference=SurfaceReference(
                    text="the dagger carrier",
                    evidence_anchor_id=(
                        "source_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
                    ),
                    chapter_id="source_demo_chapter_001",
                    scene_id="source_demo_chapter_001_scene_001",
                ),
                status="ambiguous",
                confidence=0.58,
                reason="Mark carried a rusty dagger in the original scene.",
            ),
        ),
    )

    snapshot_payload = _canon_snapshot_payload(result)

    parsed_payload = json.loads(snapshot_payload)
    assert parsed_payload["entity_resolution"]["decisions"] == [
        {
            "candidate_count": 0,
            "chapter_id": "source_demo_chapter_001",
            "confidence": 0.58,
            "entity_id": None,
            "evidence_anchor_id": (
                "source_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
            ),
            "reason": "Identity has multiple possible matches and needs review.",
            "reference_kind": "description",
            "reference_label": "Description reference",
            "scene_id": "source_demo_chapter_001_scene_001",
            "status": "ambiguous",
        }
    ]
    assert "Mark carried a rusty dagger" not in snapshot_payload
    assert "the dagger carrier" not in snapshot_payload


def test_canon_snapshot_payload_classifies_identity_reference_metadata_safely() -> None:
    """Identity review metadata should classify references without persisting source text."""
    imported_source = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo Story",
        text="Chapter 1\n\nGeneral Charlotte arrived. She, waited.",
    )
    result = ProjectRunResult(
        imported_source=imported_source,
        database=CanonDatabase(),
        extraction_results=(
            ExtractionResult(scene_id="source_demo_chapter_001_scene_001"),
        ),
        update_summaries=(CanonUpdateSummary(),),
        identity_resolutions=(
            ResolvedReference(
                reference=SurfaceReference(
                    text="General Charlotte",
                    evidence_anchor_id=(
                        "source_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
                    ),
                    chapter_id="source_demo_chapter_001",
                    scene_id="source_demo_chapter_001_scene_001",
                ),
                status="ambiguous",
                confidence=0.95,
            ),
            ResolvedReference(
                reference=SurfaceReference(
                    text="She,",
                    evidence_anchor_id=(
                        "source_demo_chapter_001_scene_001_paragraph_001_sentence_002_anchor"
                    ),
                    chapter_id="source_demo_chapter_001",
                    scene_id="source_demo_chapter_001_scene_001",
                ),
                status="unresolved",
                confidence=0.87,
            ),
        ),
    )

    parsed_payload = json.loads(_canon_snapshot_payload(result))
    decisions = parsed_payload["entity_resolution"]["decisions"]

    assert decisions[0]["reference_kind"] == "title"
    assert decisions[0]["reference_label"] == "Title reference"
    assert decisions[1]["reference_kind"] == "pronoun"
    assert decisions[1]["reference_label"] == "Pronoun reference"
    assert "General Charlotte" not in json.dumps(parsed_payload)
    assert "She," not in json.dumps(parsed_payload)


def test_canon_snapshot_payload_reports_quarantined_extraction_candidates() -> None:
    """Snapshot metadata should expose ungrounded AI candidate quarantine counts."""
    imported_source = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo Story",
        text="Chapter 1\n\nMark carried a rusty dagger.",
    )
    result = ProjectRunResult(
        imported_source=imported_source,
        database=CanonDatabase(),
        extraction_results=(
            ExtractionResult(
                scene_id="source_demo_chapter_001_scene_001",
                rejected_candidate_count=3,
            ),
        ),
        update_summaries=(CanonUpdateSummary(),),
    )

    parsed_payload = json.loads(_canon_snapshot_payload(result))

    assert parsed_payload["ungrounded_extraction_candidate_count"] == 3


def test_canon_snapshot_payload_stores_translation_metadata_without_text() -> None:
    """Phase 12 translation snapshots should persist metadata, not text."""
    imported_source = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo Story",
        text="Chapter 1\n\nMark carried a rusty dagger.",
    )
    result = ProjectRunResult(
        imported_source=imported_source,
        database=CanonDatabase(),
        extraction_results=(
            ExtractionResult(scene_id="source_demo_chapter_001_scene_001"),
        ),
        update_summaries=(CanonUpdateSummary(),),
        translation_units=(
            TranslatedUnit(
                unit_id="translation_source_demo_chapter_001_scene_001",
                source_language="zh",
                target_language="en",
                mode="clean_english",
                normalized_text="The translated private sentence should stay out.",
                source_evidence_anchor_ids=(
                    "source_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
                ),
                issues=(
                    TranslationIssue(
                        issue_code="uncertain_term",
                        source_term="private_source_term",
                        message="This issue message should stay out of snapshots.",
                        evidence_anchor_ids=(
                            "source_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
                        ),
                        term_kind="power_system",
                        possible_meaning_count=2,
                    ),
                ),
                source_chapter_id="source_demo_chapter_001",
                source_scene_id="source_demo_chapter_001_scene_001",
            ),
        ),
    )

    snapshot_payload = _canon_snapshot_payload(result)

    parsed_payload = json.loads(snapshot_payload)
    assert parsed_payload["translation"] == {
        "issue_count": 1,
        "unit_count": 1,
        "units": [
            {
                "issue_count": 1,
                "mode": "clean_english",
                "source_chapter_id": "source_demo_chapter_001",
                "source_evidence_anchor_ids": [
                    "source_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
                ],
                "source_language": "zh",
                "source_scene_id": "source_demo_chapter_001_scene_001",
                "target_language": "en",
                "unit_id": "translation_source_demo_chapter_001_scene_001",
                "issues": [
                    {
                        "evidence_anchor_count": 1,
                        "issue_code": "translation_review_required",
                        "issue_label": "Multiple meanings need review",
                        "possible_meaning_count": 2,
                        "term_kind": "power_system",
                    }
                ],
            }
        ],
    }
    assert "Mark carried a rusty dagger" not in snapshot_payload
    assert "The translated private sentence should stay out" not in snapshot_payload
    assert "private_source_term" not in snapshot_payload
    assert "This issue message should stay out" not in snapshot_payload


def test_project_import_snapshot_handler_persists_scene_prompts_without_characters() -> None:
    """Scene and prompt panels should not disappear when extraction finds no Canon facts."""
    repository = seeded_repository()
    import_content_store: ImportContentStore = StaticImportContentStore(
        b"Chapter 1\n\nA quiet room waited under pale light."
    )
    handler = ProjectImportSnapshotHandler(
        repository=repository,
        import_content_store=import_content_store,
    )

    snapshots = handler.process(background_job())

    snapshot_payload = json.loads(snapshots[0].serialized_output)
    presentation = snapshot_payload["presentation"]
    assert snapshot_payload["accepted_entity_count"] == 0
    assert presentation["scenes"][0]["title"] == "Scene 1"
    assert presentation["scenes"][0]["characters_present"]["items"] == []
    assert presentation["prompt_packs"][0]["scene"]["title"] == "Scene 1"
    assert presentation["prompt_packs"][0]["image_prompt"]["items"][0].startswith(
        "Generate this image"
    )


def test_project_import_snapshot_handler_filters_unknown_provider_anchors() -> None:
    """Provider anchor drift should not fail the whole import processing run."""
    repository = seeded_repository()
    import_content_store: ImportContentStore = StaticImportContentStore(
        b"Chapter 1\n\nLyra opened the sky gate."
    )
    handler = ProjectImportSnapshotHandler(
        repository=repository,
        import_content_store=import_content_store,
        extractor=MixedAnchorSceneExtractor(),
    )

    snapshots = handler.process(background_job())

    assert len(snapshots) == 1
    snapshot_payload = json.loads(snapshots[0].serialized_output)
    assert snapshot_payload["accepted_entity_count"] == 1
    assert snapshot_payload["accepted_fact_count"] == 2
    assert "character_ghost" not in snapshots[0].serialized_output
    assert "missing_anchor" not in snapshots[0].serialized_output


@dataclass
class RecordingHandler:
    """Test handler that records processed jobs."""

    processed_job_ids: tuple[str, ...] = ()

    def process(self, job: BackgroundJob) -> None:
        """Record one processed job."""
        self.processed_job_ids = (*self.processed_job_ids, job.job_id)


class SnapshotReturningHandler:
    """Test handler that returns one metadata-rich snapshot."""

    def process(self, job: BackgroundJob) -> tuple[SnapshotRecord, ...]:
        """Return one snapshot with content that must stay out of logs."""
        return (
            SnapshotRecord(
                snapshot_id="snapshot_demo",
                project_id=job.project_id,
                story_id=job.story_id,
                run_id=job.run_id,
                snapshot_kind="canon",
                content_type="application/json",
                serialized_output='{"source_text":"Mark carried a rusty dagger."}',
                created_at=FINISHED,
            ),
        )


class SnapshotStoreFailingRepository(InMemoryProjectRepository):
    """Repository test double that fails only when storing snapshots."""

    def store_snapshot(self, _snapshot: SnapshotRecord) -> None:
        """Raise a deterministic snapshot write failure."""
        raise RuntimeError("Snapshot write failed.")


class FailingHandler:
    """Test handler that raises a stable failure."""

    def process(self, _job: BackgroundJob) -> None:
        """Raise a deterministic worker failure."""
        raise RuntimeError("Worker failure.")


class UnknownAnchorFailingHandler:
    """Test handler that raises an internal anchor mismatch."""

    def process(self, _job: BackgroundJob) -> None:
        """Raise a deterministic unknown-anchor failure."""
        raise ValueError("Unknown evidence anchor: missing_anchor")


class ConflictingFactFailingHandler:
    """Test handler that raises an internal canon conflict."""

    def process(self, _job: BackgroundJob) -> None:
        """Raise a deterministic conflicting-fact failure."""
        raise ValueError("Conflicting fact: fact_1")


class DuplicateWorldSectionFailingHandler:
    """Test handler that raises an internal presentation duplicate."""

    def process(self, _job: BackgroundJob) -> None:
        """Raise a deterministic duplicate world-section failure."""
        raise ValueError("World sheet section titles must be unique.")


class ProviderTimeoutFailingHandler:
    """Test handler that raises a normalized provider timeout."""

    def process(self, _job: BackgroundJob) -> None:
        """Raise a deterministic provider timeout failure."""
        raise ValueError("OpenAI extraction request timed out.")


class FailingEnqueueQueue(InMemoryJobQueue):
    """Queue adapter that fails after duplicate preflight checks pass."""

    def enqueue(self, _job: BackgroundJob) -> None:
        """Raise a deterministic queue failure."""
        raise RuntimeError("Queue unavailable.")


class StaticImportContentStore:
    """Test import content store that returns one in-memory source body."""

    def __init__(self, content: bytes) -> None:
        """Create a static import content store."""
        self._content = content

    def store_import_content(self, _storage_ref: str, _content: bytes) -> None:
        """Reject writes because this store is read-only for worker tests."""
        raise NotImplementedError("Static test import store is read-only.")

    def read_import_content(self, _storage_ref: str) -> bytes:
        """Return the configured test source body."""
        return self._content

    def delete_import_content(self, _storage_ref: str) -> None:
        """Ignore deletes because this store is read-only for worker tests."""


class RecordingSceneExtractor:
    """Test extractor that proves worker processing can use injected extraction."""

    def __init__(self) -> None:
        """Create a recording extractor."""
        self.scene_ids: tuple[str, ...] = ()

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return one evidence-backed character proposal."""
        self.scene_ids = (*self.scene_ids, scene.scene_id)
        anchor_id = scene.evidence_anchor_ids[0]
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="character_lyra",
                    entity_type="character",
                    display_name="Lyra",
                    evidence_anchor_id=anchor_id,
                    confidence=0.95,
                ),
            ),
            facts=(
                ExtractedFact(
                    fact_id="fact_character_lyra_role",
                    entity_id="character_lyra",
                    attribute="role",
                    value="Sky Gate Keeper",
                    evidence_anchor_id=anchor_id,
                    confidence=0.91,
                ),
            ),
            state_changes=(
                ExtractedStateChange(
                    entity_id="character_lyra",
                    attribute="role",
                    value="Sky Gate Keeper",
                    valid_from_anchor_id=anchor_id,
                    confidence=0.91,
                ),
            ),
        )


class MachineIdSceneExtractor:
    """Test extractor that emits short provider-style entity IDs."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return accepted canon candidates with short entity IDs."""
        anchor_id = scene.evidence_anchor_ids[0]
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="E1",
                    entity_type="character",
                    display_name="Zhao Chen",
                    evidence_anchor_id=anchor_id,
                    confidence=0.95,
                ),
                ExtractedEntity(
                    entity_id="E5",
                    entity_type="location",
                    display_name="North Star Academy",
                    evidence_anchor_id=anchor_id,
                    confidence=0.95,
                ),
            ),
            facts=(
                ExtractedFact(
                    fact_id="fact_e1_current_location",
                    entity_id="E1",
                    attribute="current_location",
                    value="North Star Academy",
                    evidence_anchor_id=anchor_id,
                    confidence=0.91,
                ),
            ),
            relationships=(
                ExtractedRelationship(
                    source_entity_id="E1",
                    relationship_type="located_in",
                    target_entity_id="E5",
                    evidence_anchor_id=anchor_id,
                    confidence=0.9,
                ),
            ),
            state_changes=(
                ExtractedStateChange(
                    entity_id="E1",
                    attribute="current_location",
                    value="North Star Academy",
                    valid_from_anchor_id=anchor_id,
                    confidence=0.91,
                ),
            ),
        )


class MixedAnchorSceneExtractor:
    """Test extractor that emits one grounded and one ungrounded candidate."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return provider-like candidates with one anchor mismatch."""
        anchor_id = scene.evidence_anchor_ids[0]
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="character_lyra",
                    entity_type="character",
                    display_name="Lyra",
                    evidence_anchor_id=anchor_id,
                    confidence=0.95,
                ),
                ExtractedEntity(
                    entity_id="character_ghost",
                    entity_type="character",
                    display_name="Ghost",
                    evidence_anchor_id="missing_anchor",
                    confidence=0.95,
                ),
            ),
            facts=(
                ExtractedFact(
                    fact_id="fact_character_lyra_role",
                    entity_id="character_lyra",
                    attribute="role",
                    value="Sky Gate Keeper",
                    evidence_anchor_id=anchor_id,
                    confidence=0.91,
                ),
                ExtractedFact(
                    fact_id="fact_character_ghost_role",
                    entity_id="character_ghost",
                    attribute="role",
                    value="Unseen Passenger",
                    evidence_anchor_id="missing_anchor",
                    confidence=0.91,
                ),
            ),
        )


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


def worker_log_record(
    caplog: LogCaptureFixture,
    workflow_kind: str,
    workflow_status: str,
) -> logging.LogRecord:
    """Return one captured worker workflow log record."""
    for record in caplog.records:
        if (
            getattr(record, "workflow_kind", "") == workflow_kind
            and getattr(record, "workflow_status", "") == workflow_status
        ):
            return record
    raise AssertionError(f"Missing worker log: {workflow_kind}/{workflow_status}")


def assert_duration_log(record: logging.LogRecord) -> None:
    """Assert a worker log record has metadata-only duration."""
    duration_ms = getattr(record, "duration_ms", None)
    assert isinstance(duration_ms, float)
    assert duration_ms >= 0.0


def caplog_record_text(caplog: LogCaptureFixture) -> str:
    """Return captured worker log metadata as searchable text."""
    return "\n".join(str(record.__dict__) for record in caplog.records)

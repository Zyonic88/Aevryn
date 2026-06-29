"""Tests for storage-backed generated exports."""

from __future__ import annotations

from pathlib import Path

import pytest

from aevryn.export_storage import ExportStorageService, ExportWriteRequest
from aevryn.persistence import (
    EngineRunRecord,
    ExportRecord,
    ImportRecord,
    InMemoryProjectRepository,
    ProjectRecord,
    SnapshotRecord,
    StoryRecord,
    UserRecord,
)
from aevryn.storage import LocalFilesystemStorage, StorageObjectNotFoundError

NOW = "2026-06-29T00:00:00Z"


def test_export_storage_service_writes_bytes_and_database_metadata(tmp_path: Path) -> None:
    """Generated exports should store bytes in Storage and metadata in the database."""
    repository = _repository_with_snapshot()
    storage = LocalFilesystemStorage(tmp_path / "storage")
    service = ExportStorageService(repository=repository, storage=storage)

    export = service.write_export(
        ExportWriteRequest(
            export_id="export_alpha",
            project_id="project_alpha",
            snapshot_id="snapshot_alpha",
            export_kind="canon",
            export_format="markdown",
            filename="canon.md",
            content_type="text/markdown; charset=utf-8",
            content=b"# Canon\n",
            created_at=NOW,
        )
    )

    recorded = repository.get_export("user_alpha", "export_alpha")
    assert recorded == export
    assert recorded.storage_ref == (
        "storage://projects/project_alpha/exports/export_alpha/canon.md"
    )
    assert recorded.size == len(b"# Canon\n")
    assert recorded.checksum.startswith("sha256:")
    assert service.read_export(user_id="user_alpha", export_id="export_alpha") == b"# Canon\n"


def test_export_storage_service_deletes_bytes_when_database_record_fails(
    tmp_path: Path,
) -> None:
    """Export byte writes should be compensated when metadata persistence fails."""
    repository = FailingExportRepository()
    storage = LocalFilesystemStorage(tmp_path / "storage")
    service = ExportStorageService(repository=repository, storage=storage)

    with pytest.raises(RuntimeError, match="database unavailable"):
        service.write_export(
            ExportWriteRequest(
                export_id="export_alpha",
                project_id="project_alpha",
                snapshot_id="snapshot_alpha",
                export_kind="canon",
                export_format="markdown",
                filename="canon.md",
                content_type="text/markdown; charset=utf-8",
                content=b"# Canon\n",
                created_at=NOW,
            )
        )

    with pytest.raises(StorageObjectNotFoundError):
        storage.read_object("storage://projects/project_alpha/exports/export_alpha/canon.md")


def test_export_storage_service_rejects_path_filenames(tmp_path: Path) -> None:
    """Export filenames should not be allowed to shape storage paths."""
    service = ExportStorageService(
        repository=_repository_with_snapshot(),
        storage=LocalFilesystemStorage(tmp_path / "storage"),
    )

    with pytest.raises(ValueError, match="filename"):
        service.write_export(
            ExportWriteRequest(
                export_id="export_alpha",
                project_id="project_alpha",
                snapshot_id="snapshot_alpha",
                export_kind="canon",
                export_format="markdown",
                filename="../canon.md",
                content_type="text/markdown; charset=utf-8",
                content=b"# Canon\n",
                created_at=NOW,
            )
        )


class FailingExportRepository(InMemoryProjectRepository):
    """Repository double that fails during export metadata persistence."""

    def record_export(self, export: ExportRecord) -> None:
        """Simulate a database outage."""
        raise RuntimeError("database unavailable")


def _repository_with_snapshot() -> InMemoryProjectRepository:
    """Return a repository with one succeeded run and canon snapshot."""
    repository = InMemoryProjectRepository()
    repository.create_user(
        UserRecord(
            user_id="user_alpha",
            email="alpha@example.com",
            display_name="Alpha",
            created_at=NOW,
        )
    )
    repository.create_project(
        ProjectRecord(
            project_id="project_alpha",
            owner_user_id="user_alpha",
            name="Alpha Project",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    repository.create_story(
        StoryRecord(
            story_id="story_alpha",
            project_id="project_alpha",
            title="Alpha Story",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    repository.record_import(
        import_record=ImportRecord(
            import_id="import_alpha",
            story_id="story_alpha",
            source_id="source_alpha",
            filename="chapter.txt",
            source_format="txt",
            storage_ref="storage://projects/project_alpha/imports/import_alpha/source.txt",
            chapter_count=1,
            scene_count=1,
            evidence_anchor_count=1,
            created_at=NOW,
        )
    )
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_alpha",
            project_id="project_alpha",
            story_id="story_alpha",
            import_id="import_alpha",
            status="succeeded",
            engine_version="aevryn_v1",
            started_at=NOW,
            status_updated_at=NOW,
            finished_at=NOW,
        )
    )
    repository.store_snapshot(
        SnapshotRecord(
            snapshot_id="snapshot_alpha",
            project_id="project_alpha",
            story_id="story_alpha",
            run_id="run_alpha",
            snapshot_kind="canon",
            content_type="application/json",
            serialized_output="{}",
            created_at=NOW,
        )
    )
    return repository

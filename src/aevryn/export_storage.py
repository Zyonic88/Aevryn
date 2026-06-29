"""Storage-backed generated export persistence."""

from __future__ import annotations

from dataclasses import dataclass

from aevryn.persistence import ExportRecord, ProjectRepository
from aevryn.storage import StorageService


@dataclass(frozen=True, slots=True)
class ExportWriteRequest:
    """Request to persist generated export bytes."""

    export_id: str
    project_id: str
    snapshot_id: str
    export_kind: str
    export_format: str
    filename: str
    content_type: str
    content: bytes
    created_at: str


class ExportStorageService:
    """Persist generated export bytes in Storage and metadata in the database."""

    def __init__(self, *, repository: ProjectRepository, storage: StorageService) -> None:
        """Create a storage-backed export service."""
        self._repository = repository
        self._storage = storage

    def write_export(self, request: ExportWriteRequest) -> ExportRecord:
        """Write export bytes, then record database metadata."""
        storage_ref = _export_storage_ref(
            project_id=request.project_id,
            export_id=request.export_id,
            filename=request.filename,
        )
        stored = self._storage.save_object(
            storage_ref=storage_ref,
            content=request.content,
            content_type=request.content_type,
            metadata={
                "aevryn_storage_kind": "generated_export",
                "filename": request.filename,
                "export_kind": request.export_kind,
                "export_format": request.export_format,
            },
        )
        export = ExportRecord(
            export_id=request.export_id,
            project_id=request.project_id,
            snapshot_id=request.snapshot_id,
            export_kind=request.export_kind,
            export_format=request.export_format,
            filename=stored.filename,
            content_type=stored.content_type,
            storage_ref=stored.storage_ref,
            created_at=request.created_at,
            size=stored.size,
            checksum=stored.checksum,
        )
        try:
            self._repository.record_export(export)
        except Exception:
            self._storage.delete_object(storage_ref)
            raise
        return export

    def read_export(self, *, user_id: str, export_id: str) -> bytes:
        """Read generated export bytes after repository ownership checks."""
        export = self._repository.get_export(user_id=user_id, export_id=export_id)
        return self._storage.read_object(export.storage_ref)

    def delete_export_bytes(self, export: ExportRecord) -> None:
        """Delete generated export bytes for an already scoped export record."""
        self._storage.delete_object(export.storage_ref)


def _export_storage_ref(*, project_id: str, export_id: str, filename: str) -> str:
    """Return the canonical storage reference for one generated export."""
    if any(character in filename for character in {"/", "\\"}) or filename in {"", ".", ".."}:
        raise ValueError("Export filename cannot be a path.")
    return f"storage://projects/{project_id}/exports/{export_id}/{filename}"

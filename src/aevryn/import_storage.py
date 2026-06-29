"""Storage boundary for imported source bytes."""

from __future__ import annotations

import base64
import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from aevryn.storage import StorageObjectNotFoundError, StorageService


class ImportContentNotFoundError(Exception):
    """Raised when imported source bytes are missing from storage."""


class ImportContentStore(Protocol):
    """Storage adapter for source bytes referenced by import metadata."""

    def store_import_content(self, storage_ref: str, content: bytes) -> None:
        """Store source bytes under a stable storage reference."""

    def read_import_content(self, storage_ref: str) -> bytes:
        """Read source bytes for a stable storage reference."""

    def delete_import_content(self, storage_ref: str) -> None:
        """Delete source bytes for a stable storage reference if present."""


class ObjectStorageClient(Protocol):
    """Minimal private object-storage client used by import content adapters."""

    def put_object(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str,
        metadata: Mapping[str, str],
    ) -> None:
        """Write one private object."""

    def get_object(self, *, bucket: str, key: str) -> bytes:
        """Read one private object."""

    def delete_object(self, *, bucket: str, key: str) -> None:
        """Delete one private object if present."""


class InMemoryImportContentStore:
    """Deterministic in-memory import content store for API and worker tests."""

    def __init__(self) -> None:
        """Create an empty import content store."""
        self._content_by_ref: dict[str, bytes] = {}

    def store_import_content(self, storage_ref: str, content: bytes) -> None:
        """Store source bytes under a stable storage reference."""
        _require_storage_ref(storage_ref)
        if not isinstance(content, bytes) or not content:
            raise ValueError("Import content cannot be empty.")
        self._content_by_ref[storage_ref] = content

    def read_import_content(self, storage_ref: str) -> bytes:
        """Read source bytes for a stable storage reference."""
        _require_storage_ref(storage_ref)
        try:
            return self._content_by_ref[storage_ref]
        except KeyError as error:
            raise ImportContentNotFoundError(
                f"Missing import content: {storage_ref}"
            ) from error

    def delete_import_content(self, storage_ref: str) -> None:
        """Delete source bytes for a stable storage reference if present."""
        _require_storage_ref(storage_ref)
        self._content_by_ref.pop(storage_ref, None)


class FileSystemImportContentStore:
    """Local filesystem import content store for environment-backed development."""

    def __init__(self, root: Path) -> None:
        """Create a local import content store rooted at one directory."""
        self._root = root

    def store_import_content(self, storage_ref: str, content: bytes) -> None:
        """Store source bytes under a stable storage reference."""
        _require_storage_ref(storage_ref)
        if not isinstance(content, bytes) or not content:
            raise ValueError("Import content cannot be empty.")
        path = self._path_for_ref(storage_ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def read_import_content(self, storage_ref: str) -> bytes:
        """Read source bytes for a stable storage reference."""
        _require_storage_ref(storage_ref)
        path = self._path_for_ref(storage_ref)
        try:
            content = path.read_bytes()
        except FileNotFoundError as error:
            raise ImportContentNotFoundError(
                f"Missing import content: {storage_ref}"
            ) from error
        if not content:
            raise ImportContentNotFoundError(f"Missing import content: {storage_ref}")
        return content

    def delete_import_content(self, storage_ref: str) -> None:
        """Delete source bytes for a stable storage reference if present."""
        _require_storage_ref(storage_ref)
        self._path_for_ref(storage_ref).unlink(missing_ok=True)

    def _path_for_ref(self, storage_ref: str) -> Path:
        """Return the deterministic local path for a storage reference."""
        encoded = base64.urlsafe_b64encode(storage_ref.encode("utf-8")).decode("ascii")
        return self._root / f"{encoded.rstrip('=')}.bin"


class ObjectStorageImportContentStore:
    """Private object-storage adapter for imported source bytes."""

    def __init__(self, *, client: ObjectStorageClient, bucket: str, prefix: str) -> None:
        """Create an object-storage import content store."""
        self._client = client
        self._bucket = _require_object_storage_token(bucket, "Object storage bucket")
        self._prefix = _normalize_object_prefix(prefix)

    def store_import_content(self, storage_ref: str, content: bytes) -> None:
        """Store source bytes under a stable private object key."""
        _require_storage_ref(storage_ref)
        if not isinstance(content, bytes) or not content:
            raise ValueError("Import content cannot be empty.")
        self._client.put_object(
            bucket=self._bucket,
            key=self._key_for_ref(storage_ref),
            body=content,
            content_type="application/octet-stream",
            metadata={"aevryn_storage_kind": "source_import"},
        )

    def read_import_content(self, storage_ref: str) -> bytes:
        """Read source bytes from private object storage."""
        _require_storage_ref(storage_ref)
        try:
            content = self._client.get_object(
                bucket=self._bucket,
                key=self._key_for_ref(storage_ref),
            )
        except (FileNotFoundError, KeyError) as error:
            raise ImportContentNotFoundError(
                f"Missing import content: {storage_ref}"
            ) from error
        if not content:
            raise ImportContentNotFoundError(f"Missing import content: {storage_ref}")
        return content

    def delete_import_content(self, storage_ref: str) -> None:
        """Delete source bytes from private object storage if present."""
        _require_storage_ref(storage_ref)
        self._client.delete_object(
            bucket=self._bucket,
            key=self._key_for_ref(storage_ref),
        )

    def _key_for_ref(self, storage_ref: str) -> str:
        """Return a stable object key that does not expose source prose."""
        digest = hashlib.sha256(storage_ref.encode("utf-8")).hexdigest()
        return f"{self._prefix}/{digest}.bin"


class StorageServiceImportContentStore:
    """Import content store backed by the general Aevryn storage service."""

    def __init__(self, storage: StorageService) -> None:
        """Create a storage-service-backed import content store."""
        self._storage = storage

    def store_import_content(self, storage_ref: str, content: bytes) -> None:
        """Store source bytes through the shared storage boundary."""
        _require_storage_ref(storage_ref)
        if not isinstance(content, bytes) or not content:
            raise ValueError("Import content cannot be empty.")
        self._storage.save_object(
            storage_ref=_object_storage_ref_for_import_ref(storage_ref),
            content=content,
            content_type="application/octet-stream",
            metadata={"aevryn_storage_kind": "source_import", "filename": "source.bin"},
        )

    def read_import_content(self, storage_ref: str) -> bytes:
        """Read source bytes through the shared storage boundary."""
        _require_storage_ref(storage_ref)
        try:
            return self._storage.read_object(_object_storage_ref_for_import_ref(storage_ref))
        except StorageObjectNotFoundError as error:
            raise ImportContentNotFoundError(
                f"Missing import content: {storage_ref}"
            ) from error

    def delete_import_content(self, storage_ref: str) -> None:
        """Delete source bytes through the shared storage boundary."""
        _require_storage_ref(storage_ref)
        self._storage.delete_object(_object_storage_ref_for_import_ref(storage_ref))


def _require_storage_ref(storage_ref: str) -> None:
    """Require an Aevryn API import storage reference."""
    if not isinstance(storage_ref, str) or not storage_ref.startswith("api_import://"):
        raise ValueError("Import content storage_ref is invalid.")
    if any(character.isspace() for character in storage_ref):
        raise ValueError("Import content storage_ref cannot contain whitespace.")


def _require_object_storage_token(value: str, label: str) -> str:
    """Require a nonblank object-storage identifier without whitespace."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")
    normalized = value.strip()
    if any(character.isspace() for character in normalized):
        raise ValueError(f"{label} cannot contain whitespace.")
    return normalized


def _normalize_object_prefix(prefix: str) -> str:
    """Return a stable object-storage prefix for source imports."""
    normalized = _require_object_storage_token(prefix, "Object storage prefix").strip("/")
    if not normalized:
        raise ValueError("Object storage prefix is required.")
    if ".." in normalized.split("/"):
        raise ValueError("Object storage prefix cannot contain traversal segments.")
    return normalized


def _object_storage_ref_for_import_ref(storage_ref: str) -> str:
    """Return the storage-service reference for one API import reference."""
    _require_storage_ref(storage_ref)
    without_scheme = storage_ref.removeprefix("api_import://")
    if "/" not in without_scheme:
        raise ValueError("Import content storage_ref is missing an import ID.")
    story_id, import_id = without_scheme.split("/", maxsplit=1)
    return f"storage://projects/{story_id}/imports/{import_id}/source.bin"

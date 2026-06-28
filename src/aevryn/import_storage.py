"""Storage boundary for imported source bytes."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Protocol


class ImportContentNotFoundError(Exception):
    """Raised when imported source bytes are missing from storage."""


class ImportContentStore(Protocol):
    """Storage adapter for source bytes referenced by import metadata."""

    def store_import_content(self, storage_ref: str, content: bytes) -> None:
        """Store source bytes under a stable storage reference."""

    def read_import_content(self, storage_ref: str) -> bytes:
        """Read source bytes for a stable storage reference."""


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

    def _path_for_ref(self, storage_ref: str) -> Path:
        """Return the deterministic local path for a storage reference."""
        encoded = base64.urlsafe_b64encode(storage_ref.encode("utf-8")).decode("ascii")
        return self._root / f"{encoded.rstrip('=')}.bin"


def _require_storage_ref(storage_ref: str) -> None:
    """Require an Aevryn API import storage reference."""
    if not isinstance(storage_ref, str) or not storage_ref.startswith("api_import://"):
        raise ValueError("Import content storage_ref is invalid.")
    if any(character.isspace() for character in storage_ref):
        raise ValueError("Import content storage_ref cannot contain whitespace.")

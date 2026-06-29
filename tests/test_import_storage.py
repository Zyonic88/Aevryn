"""Tests for import source-byte storage adapters."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from aevryn.import_storage import (
    ImportContentNotFoundError,
    ObjectStorageImportContentStore,
    StorageServiceImportContentStore,
)
from aevryn.storage import LocalFilesystemStorage


def test_object_storage_import_content_store_round_trips_private_bytes() -> None:
    """Object storage should store and read import bytes without exposing source refs in keys."""
    client = FakeObjectStorageClient()
    store = ObjectStorageImportContentStore(
        client=client,
        bucket="aevryn-private-source",
        prefix="imports/source",
    )

    store.store_import_content(
        "api_import://story_alpha/import_alpha",
        b"Chapter 1\nMira opened the brass gate.",
    )

    assert store.read_import_content("api_import://story_alpha/import_alpha") == (
        b"Chapter 1\nMira opened the brass gate."
    )
    [(bucket, key)] = client.objects
    assert bucket == "aevryn-private-source"
    assert key.startswith("imports/source/")
    assert key.endswith(".bin")
    assert "story_alpha" not in key
    assert "import_alpha" not in key
    assert client.metadata[(bucket, key)] == {"aevryn_storage_kind": "source_import"}


def test_object_storage_import_content_store_deletes_private_bytes() -> None:
    """Object storage deletes should make future reads behave like missing content."""
    client = FakeObjectStorageClient()
    store = ObjectStorageImportContentStore(
        client=client,
        bucket="aevryn-private-source",
        prefix="imports/source",
    )

    store.store_import_content("api_import://story_alpha/import_alpha", b"source")
    store.delete_import_content("api_import://story_alpha/import_alpha")

    with pytest.raises(ImportContentNotFoundError):
        store.read_import_content("api_import://story_alpha/import_alpha")


def test_object_storage_import_content_store_validates_configuration() -> None:
    """Object storage configuration should fail closed for ambiguous identifiers."""
    client = FakeObjectStorageClient()

    with pytest.raises(ValueError, match="bucket"):
        ObjectStorageImportContentStore(client=client, bucket="", prefix="imports")

    with pytest.raises(ValueError, match="prefix"):
        ObjectStorageImportContentStore(
            client=client,
            bucket="aevryn-private-source",
            prefix="../imports",
        )


def test_storage_service_import_content_store_uses_project_import_path(
    tmp_path: Path,
) -> None:
    """Import content should be movable onto the shared storage service boundary."""
    storage = LocalFilesystemStorage(tmp_path / "storage")
    store = StorageServiceImportContentStore(storage)

    store.store_import_content(
        "api_import://story_alpha/import_alpha",
        b"Chapter 1\nMira opened the brass gate.",
    )

    assert store.read_import_content("api_import://story_alpha/import_alpha") == (
        b"Chapter 1\nMira opened the brass gate."
    )
    assert storage.read_object(
        "storage://projects/story_alpha/imports/import_alpha/source.bin"
    ) == b"Chapter 1\nMira opened the brass gate."


def test_storage_service_import_content_store_uses_project_scoped_import_refs(
    tmp_path: Path,
) -> None:
    """New import refs should map to the approved project-scoped storage path."""
    storage = LocalFilesystemStorage(tmp_path / "storage")
    store = StorageServiceImportContentStore(storage)

    store.store_import_content(
        "api_import://projects/project_alpha/stories/story_alpha/imports/import_alpha",
        b"Chapter 1\nMira opened the brass gate.",
    )

    assert storage.read_object(
        "storage://projects/project_alpha/imports/import_alpha/source.bin"
    ) == b"Chapter 1\nMira opened the brass gate."


def test_storage_service_import_content_store_rejects_malformed_project_refs(
    tmp_path: Path,
) -> None:
    """Malformed project-scoped refs should fail before object storage is touched."""
    storage = LocalFilesystemStorage(tmp_path / "storage")
    store = StorageServiceImportContentStore(storage)

    with pytest.raises(ValueError, match="Import content storage_ref"):
        store.store_import_content(
            "api_import://projects/project_alpha/story/story_alpha/imports/import_alpha",
            b"source",
        )

    with pytest.raises(ValueError, match="Project ID"):
        store.store_import_content(
            "api_import://projects/../stories/story_alpha/imports/import_alpha",
            b"source",
        )


class FakeObjectStorageClient:
    """Deterministic object storage client for adapter tests."""

    def __init__(self) -> None:
        """Create an empty fake object store."""
        self.objects: dict[tuple[str, str], bytes] = {}
        self.metadata: dict[tuple[str, str], Mapping[str, str]] = {}

    def put_object(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str,
        metadata: Mapping[str, str],
    ) -> None:
        """Store one object."""
        assert content_type == "application/octet-stream"
        self.objects[(bucket, key)] = body
        self.metadata[(bucket, key)] = dict(metadata)

    def get_object(self, *, bucket: str, key: str) -> bytes:
        """Read one object."""
        try:
            return self.objects[(bucket, key)]
        except KeyError as error:
            raise FileNotFoundError(key) from error

    def delete_object(self, *, bucket: str, key: str) -> None:
        """Delete one object."""
        self.objects.pop((bucket, key), None)
        self.metadata.pop((bucket, key), None)

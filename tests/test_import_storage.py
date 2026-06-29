"""Tests for import source-byte storage adapters."""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from aevryn.import_storage import (
    ImportContentNotFoundError,
    ObjectStorageImportContentStore,
)


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

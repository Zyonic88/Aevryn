"""Tests for Aevryn private storage services."""

from __future__ import annotations

import io
import sys
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType

import pytest

from aevryn.storage import LocalFilesystemStorage, R2Storage, StorageObjectNotFoundError


def test_local_filesystem_storage_saves_reads_and_deletes_private_bytes(
    tmp_path: Path,
) -> None:
    """Local storage should round-trip bytes and return database-owned metadata."""
    root = tmp_path / "storage"
    storage = LocalFilesystemStorage(root)

    metadata = storage.save_object(
        storage_ref="storage://projects/project_alpha/imports/import_alpha/source.epub",
        content=b"epub bytes",
        content_type="application/epub+zip",
        metadata={"filename": "source.epub"},
    )

    assert storage.read_object(
        "storage://projects/project_alpha/imports/import_alpha/source.epub"
    ) == b"epub bytes"
    assert metadata.storage_ref == (
        "storage://projects/project_alpha/imports/import_alpha/source.epub"
    )
    assert metadata.filename == "source.epub"
    assert metadata.content_type == "application/epub+zip"
    assert metadata.size == len(b"epub bytes")
    assert metadata.checksum.startswith("sha256:")

    storage.delete_object("storage://projects/project_alpha/imports/import_alpha/source.epub")

    with pytest.raises(StorageObjectNotFoundError):
        storage.read_object("storage://projects/project_alpha/imports/import_alpha/source.epub")


def test_local_filesystem_storage_rejects_path_traversal(
    tmp_path: Path,
) -> None:
    """Storage references should not escape the configured local storage root."""
    storage = LocalFilesystemStorage(tmp_path / "storage")

    unsafe_refs = (
        "storage://projects/project_alpha/../source.epub",
        "storage://projects/project_alpha/imports\\source.epub",
        "storage://projects//source.epub",
    )

    for storage_ref in unsafe_refs:
        with pytest.raises(ValueError):
            storage.save_object(
                storage_ref=storage_ref,
                content=b"bytes",
                content_type="application/octet-stream",
                metadata={},
            )


def test_r2_storage_maps_operations_to_s3_compatible_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R2 storage should write private objects through the S3-compatible client."""
    fake_module = FakeBoto3Module("boto3")
    monkeypatch.setitem(sys.modules, "boto3", fake_module)

    storage = R2Storage(
        bucket="aevryn-dev",
        prefix="objects",
        endpoint_url="https://example.r2.cloudflarestorage.com",
        access_key_id="access-key",
        secret_access_key="secret-key",
    )

    metadata = storage.save_object(
        storage_ref="storage://projects/project_alpha/exports/export_alpha/character.md",
        content=b"# Character",
        content_type="text/markdown; charset=utf-8",
        metadata={"filename": "character.md", "storage_kind": "export"},
    )

    assert storage.read_object(
        "storage://projects/project_alpha/exports/export_alpha/character.md"
    ) == b"# Character"
    storage.delete_object("storage://projects/project_alpha/exports/export_alpha/character.md")

    with pytest.raises(StorageObjectNotFoundError):
        storage.read_object("storage://projects/project_alpha/exports/export_alpha/character.md")

    assert metadata.filename == "character.md"
    assert fake_module.client_calls == [
        {
            "service_name": "s3",
            "endpoint_url": "https://example.r2.cloudflarestorage.com",
            "aws_access_key_id": "access-key",
            "aws_secret_access_key": "secret-key",
            "region_name": "auto",
        }
    ]


class FakeBoto3Module(ModuleType):
    """Small fake boto3 module for R2 adapter tests."""

    def __init__(self, name: str) -> None:
        """Create a fake boto3 module."""
        super().__init__(name)
        self.client_calls: list[dict[str, str]] = []
        self.s3_client = FakeS3Client()

    def client(
        self,
        service_name: str,
        *,
        endpoint_url: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
    ) -> FakeS3Client:
        """Return a fake S3 client and capture connection settings."""
        self.client_calls.append(
            {
                "service_name": service_name,
                "endpoint_url": endpoint_url,
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
                "region_name": region_name,
            }
        )
        return self.s3_client


class FakeS3Client:
    """Small fake S3-compatible client."""

    def __init__(self) -> None:
        """Create an empty fake object store."""
        self.objects: dict[tuple[str, str], tuple[bytes, str, Mapping[str, str]]] = {}

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str,
        Metadata: Mapping[str, str],
    ) -> None:
        """Store one fake object."""
        self.objects[(Bucket, Key)] = (Body, ContentType, dict(Metadata))

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, io.BytesIO]:
        """Read one fake object."""
        try:
            body = self.objects[(Bucket, Key)][0]
        except KeyError as error:
            not_found = RuntimeError("not found")
            not_found.response = {"Error": {"Code": "NoSuchKey"}}  # type: ignore[attr-defined]
            raise not_found from error
        return {"Body": io.BytesIO(body)}

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        """Delete one fake object."""
        self.objects.pop((Bucket, Key), None)

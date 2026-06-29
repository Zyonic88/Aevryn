"""Storage service boundary for private file-like bytes."""

from __future__ import annotations

import hashlib
import importlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class StorageObjectNotFoundError(Exception):
    """Raised when private storage cannot find an object."""


class StorageService(Protocol):
    """Private object storage boundary for source files, exports, and snapshots."""

    def save_object(
        self,
        *,
        storage_ref: str,
        content: bytes,
        content_type: str,
        metadata: Mapping[str, str],
    ) -> StoredObjectMetadata:
        """Save private bytes and return metadata for database records."""

    def read_object(self, storage_ref: str) -> bytes:
        """Read private bytes by stable storage reference."""

    def delete_object(self, storage_ref: str) -> None:
        """Delete private bytes by stable storage reference if present."""


@dataclass(frozen=True)
class StoredObjectMetadata:
    """Database-owned metadata for one private storage object."""

    storage_ref: str
    filename: str
    content_type: str
    size: int
    checksum: str


class LocalFilesystemStorage:
    """Development storage service rooted at one local directory."""

    def __init__(self, root: Path) -> None:
        """Create a local storage service rooted at one directory."""
        self._root = root.resolve()

    def save_object(
        self,
        *,
        storage_ref: str,
        content: bytes,
        content_type: str,
        metadata: Mapping[str, str],
    ) -> StoredObjectMetadata:
        """Save private bytes and return metadata for database records."""
        _require_storage_ref(storage_ref)
        if not isinstance(content, bytes) or not content:
            raise ValueError("Storage content cannot be empty.")
        path = self._path_for_ref(storage_ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return _stored_metadata(
            storage_ref=storage_ref,
            content=content,
            content_type=content_type,
            filename=_filename_from_metadata_or_ref(metadata, storage_ref),
        )

    def read_object(self, storage_ref: str) -> bytes:
        """Read private bytes by stable storage reference."""
        _require_storage_ref(storage_ref)
        try:
            content = self._path_for_ref(storage_ref).read_bytes()
        except FileNotFoundError as error:
            raise StorageObjectNotFoundError(storage_ref) from error
        if not content:
            raise StorageObjectNotFoundError(storage_ref)
        return content

    def delete_object(self, storage_ref: str) -> None:
        """Delete private bytes by stable storage reference if present."""
        _require_storage_ref(storage_ref)
        self._path_for_ref(storage_ref).unlink(missing_ok=True)

    def _path_for_ref(self, storage_ref: str) -> Path:
        """Return a traversal-safe local path for one storage reference."""
        key = _normalize_storage_key(storage_ref)
        path = (self._root / key).resolve()
        if not path.is_relative_to(self._root):
            raise ValueError("Storage reference escapes the configured storage root.")
        return path


class R2Storage:
    """Cloudflare R2 storage service using its S3-compatible API."""

    def __init__(
        self,
        *,
        bucket: str,
        prefix: str,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        region_name: str = "auto",
    ) -> None:
        """Create a private Cloudflare R2 storage service."""
        self._bucket = _require_token(bucket, "R2 bucket")
        self._prefix = _normalize_prefix(prefix)
        self._client = _boto3_client(
            endpoint_url=_require_endpoint(endpoint_url),
            access_key_id=_require_secret(access_key_id, "R2 access key ID"),
            secret_access_key=_require_secret(secret_access_key, "R2 secret access key"),
            region_name=region_name.strip() or "auto",
        )

    def save_object(
        self,
        *,
        storage_ref: str,
        content: bytes,
        content_type: str,
        metadata: Mapping[str, str],
    ) -> StoredObjectMetadata:
        """Save private bytes and return metadata for database records."""
        _require_storage_ref(storage_ref)
        if not isinstance(content, bytes) or not content:
            raise ValueError("Storage content cannot be empty.")
        key = self._key_for_ref(storage_ref)
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=content,
            ContentType=_require_content_type(content_type),
            Metadata=dict(metadata),
        )
        return _stored_metadata(
            storage_ref=storage_ref,
            content=content,
            content_type=content_type,
            filename=_filename_from_metadata_or_ref(metadata, storage_ref),
        )

    def read_object(self, storage_ref: str) -> bytes:
        """Read private bytes by stable storage reference."""
        _require_storage_ref(storage_ref)
        key = self._key_for_ref(storage_ref)
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except Exception as error:
            if _is_object_not_found(error):
                raise StorageObjectNotFoundError(storage_ref) from error
            raise
        body = response["Body"].read()
        if not isinstance(body, bytes) or not body:
            raise StorageObjectNotFoundError(storage_ref)
        return body

    def delete_object(self, storage_ref: str) -> None:
        """Delete private bytes by stable storage reference if present."""
        _require_storage_ref(storage_ref)
        self._client.delete_object(Bucket=self._bucket, Key=self._key_for_ref(storage_ref))

    def _key_for_ref(self, storage_ref: str) -> str:
        """Return the provider object key for one storage reference."""
        return f"{self._prefix}/{_normalize_storage_key(storage_ref)}"


def _boto3_client(
    *,
    endpoint_url: str,
    access_key_id: str,
    secret_access_key: str,
    region_name: str,
) -> Any:
    """Return a boto3 S3 client without importing boto3 unless R2 is configured."""
    try:
        boto3 = importlib.import_module("boto3")
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Cloudflare R2 storage requires the optional object-storage dependency."
        ) from error
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region_name,
    )


def _stored_metadata(
    *,
    storage_ref: str,
    content: bytes,
    content_type: str,
    filename: str,
) -> StoredObjectMetadata:
    """Return database-owned metadata for saved storage bytes."""
    return StoredObjectMetadata(
        storage_ref=storage_ref,
        filename=filename,
        content_type=_require_content_type(content_type),
        size=len(content),
        checksum=f"sha256:{hashlib.sha256(content).hexdigest()}",
    )


def _normalize_storage_key(storage_ref: str) -> str:
    """Return a safe provider key from an Aevryn storage reference."""
    _require_storage_ref(storage_ref)
    key = storage_ref.removeprefix("storage://")
    segments = key.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError("Storage reference contains an unsafe path segment.")
    if any("\\" in segment for segment in segments):
        raise ValueError("Storage reference cannot contain backslashes.")
    return key


def _require_storage_ref(storage_ref: str) -> None:
    """Require a stable Aevryn storage reference."""
    if not isinstance(storage_ref, str) or not storage_ref.startswith("storage://"):
        raise ValueError("Storage reference is invalid.")
    if any(character.isspace() for character in storage_ref):
        raise ValueError("Storage reference cannot contain whitespace.")


def _normalize_prefix(prefix: str) -> str:
    """Return a stable object-storage prefix."""
    normalized = _require_token(prefix, "Storage prefix").strip("/")
    if any(segment in {"", ".", ".."} for segment in normalized.split("/")):
        raise ValueError("Storage prefix contains an unsafe path segment.")
    return normalized


def _require_token(value: str, label: str) -> str:
    """Require a nonblank storage identifier without whitespace."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")
    normalized = value.strip()
    if any(character.isspace() for character in normalized):
        raise ValueError(f"{label} cannot contain whitespace.")
    return normalized


def _require_secret(value: str, label: str) -> str:
    """Require a nonblank secret value without logging it."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")
    return value.strip()


def _require_endpoint(value: str) -> str:
    """Require an HTTPS storage endpoint."""
    normalized = _require_secret(value, "R2 endpoint URL")
    if not normalized.startswith("https://"):
        raise ValueError("R2 endpoint URL must use https://.")
    return normalized


def _require_content_type(content_type: str) -> str:
    """Require a content type suitable for metadata records."""
    if not isinstance(content_type, str) or not content_type.strip():
        raise ValueError("Storage content type is required.")
    return content_type.strip()


def _filename_from_metadata_or_ref(
    metadata: Mapping[str, str],
    storage_ref: str,
) -> str:
    """Return a display filename from metadata or storage reference."""
    filename = metadata.get("filename", "").strip()
    if filename:
        return filename
    return _normalize_storage_key(storage_ref).rsplit("/", maxsplit=1)[-1]


def _is_object_not_found(error: Exception) -> bool:
    """Return whether a provider exception represents a missing object."""
    response = getattr(error, "response", None)
    if not isinstance(response, dict):
        return False
    error_payload = response.get("Error")
    if not isinstance(error_payload, dict):
        return False
    return str(error_payload.get("Code", "")) in {"404", "NoSuchKey", "NotFound"}

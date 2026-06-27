"""Persistence models for Aevryn platform projects."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

_MACHINE_TOKEN_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

EngineRunStatus = Literal["pending", "running", "succeeded", "failed"]
SnapshotKind = Literal[
    "canon",
    "timeline",
    "character_profile",
    "world_state",
    "scene_sheet",
    "prompt_pack",
    "continuity_report",
]


@dataclass(frozen=True, slots=True)
class UserRecord:
    """Persisted platform user identity placeholder.

    Full registration, login, password recovery, and session policy belong to
    Version 2 Phase 4. Phase 2 only needs a stable ownership record.
    """

    user_id: str
    email: str
    display_name: str
    created_at: str

    def __post_init__(self) -> None:
        """Validate user identity fields."""
        _require_machine_token(self.user_id, "User ID")
        _require_email_like(self.email, "User email")
        _require_text(self.display_name, "User display name")
        _require_timestamp(self.created_at, "User created_at")


@dataclass(frozen=True, slots=True)
class ProjectRecord:
    """Persisted creator workspace."""

    project_id: str
    owner_user_id: str
    name: str
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        """Validate project identity and ownership fields."""
        _require_machine_token(self.project_id, "Project ID")
        _require_machine_token(self.owner_user_id, "Project owner user ID")
        _require_text(self.name, "Project name")
        _require_timestamp(self.created_at, "Project created_at")
        _require_timestamp(self.updated_at, "Project updated_at")


@dataclass(frozen=True, slots=True)
class StoryRecord:
    """Persisted story metadata inside a project."""

    story_id: str
    project_id: str
    title: str
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        """Validate story metadata fields."""
        _require_machine_token(self.story_id, "Story ID")
        _require_machine_token(self.project_id, "Story project ID")
        _require_text(self.title, "Story title")
        _require_timestamp(self.created_at, "Story created_at")
        _require_timestamp(self.updated_at, "Story updated_at")


@dataclass(frozen=True, slots=True)
class ImportRecord:
    """Persisted source import metadata.

    The database stores metadata and storage references, not uploaded file bytes.
    """

    import_id: str
    story_id: str
    source_id: str
    filename: str
    source_format: str
    storage_ref: str
    chapter_count: int
    scene_count: int
    evidence_anchor_count: int
    created_at: str

    def __post_init__(self) -> None:
        """Validate import metadata and counts."""
        _require_machine_token(self.import_id, "Import ID")
        _require_machine_token(self.story_id, "Import story ID")
        _require_machine_token(self.source_id, "Import source ID")
        _require_filename(self.filename, "Import filename")
        _require_machine_token(self.source_format, "Import source format")
        _require_storage_ref(self.storage_ref, "Import storage reference")
        _require_non_negative(self.chapter_count, "Import chapter count")
        _require_non_negative(self.scene_count, "Import scene count")
        _require_non_negative(self.evidence_anchor_count, "Import evidence anchor count")
        _require_timestamp(self.created_at, "Import created_at")


@dataclass(frozen=True, slots=True)
class EngineRunRecord:
    """Persisted engine processing attempt metadata."""

    run_id: str
    project_id: str
    story_id: str
    import_id: str
    status: EngineRunStatus
    engine_version: str
    started_at: str
    status_updated_at: str | None = None
    finished_at: str | None = None
    error_summary: str = ""
    job_ref: str = ""

    def __post_init__(self) -> None:
        """Validate engine run metadata."""
        _require_machine_token(self.run_id, "Engine run ID")
        _require_machine_token(self.project_id, "Engine run project ID")
        _require_machine_token(self.story_id, "Engine run story ID")
        _require_machine_token(self.import_id, "Engine run import ID")
        if self.status not in {"pending", "running", "succeeded", "failed"}:
            raise ValueError("Engine run status is invalid.")
        _require_text(self.engine_version, "Engine run version")
        _require_timestamp(self.started_at, "Engine run started_at")
        started_at = _require_timestamp(self.started_at, "Engine run started_at")
        status_updated_at = None
        if self.status_updated_at is not None:
            status_updated_at = _require_timestamp(
                self.status_updated_at,
                "Engine run status_updated_at",
            )
        finished_at = None
        if self.finished_at is not None:
            finished_at = _require_timestamp(self.finished_at, "Engine run finished_at")
        if status_updated_at is not None and status_updated_at < started_at:
            raise ValueError("Engine run status_updated_at cannot be before started_at.")
        if finished_at is not None and finished_at < started_at:
            raise ValueError("Engine run finished_at cannot be before started_at.")
        if self.status in {"pending", "running"} and self.finished_at is not None:
            raise ValueError("Active engine runs cannot have a finished_at timestamp.")
        if self.status in {"succeeded", "failed"} and self.finished_at is None:
            raise ValueError("Completed engine runs require a finished_at timestamp.")
        if self.error_summary:
            _require_text(self.error_summary, "Engine run error summary")
        if self.status == "failed" and not self.error_summary:
            raise ValueError("Failed engine runs require an error summary.")
        if self.status != "failed" and self.error_summary:
            raise ValueError("Only failed engine runs can store an error summary.")
        if self.job_ref:
            _require_storage_ref(self.job_ref, "Engine run job reference")


@dataclass(frozen=True, slots=True)
class SnapshotRecord:
    """Immutable persisted engine output snapshot."""

    snapshot_id: str
    project_id: str
    story_id: str
    run_id: str
    snapshot_kind: SnapshotKind
    content_type: str
    serialized_output: str
    created_at: str

    def __post_init__(self) -> None:
        """Validate snapshot identity and payload."""
        _require_machine_token(self.snapshot_id, "Snapshot ID")
        _require_machine_token(self.project_id, "Snapshot project ID")
        _require_machine_token(self.story_id, "Snapshot story ID")
        _require_machine_token(self.run_id, "Snapshot run ID")
        if self.snapshot_kind not in {
            "canon",
            "timeline",
            "character_profile",
            "world_state",
            "scene_sheet",
            "prompt_pack",
            "continuity_report",
        }:
            raise ValueError("Snapshot kind is invalid.")
        _require_text(self.content_type, "Snapshot content type")
        _require_text(self.serialized_output, "Snapshot serialized output")
        _require_serialized_payload(self.serialized_output, self.content_type)
        _require_timestamp(self.created_at, "Snapshot created_at")


@dataclass(frozen=True, slots=True)
class ExportRecord:
    """Persisted export metadata.

    Export bytes live in Storage. The database stores the storage reference.
    """

    export_id: str
    project_id: str
    snapshot_id: str
    export_kind: str
    export_format: str
    filename: str
    content_type: str
    storage_ref: str
    created_at: str

    def __post_init__(self) -> None:
        """Validate export metadata."""
        _require_machine_token(self.export_id, "Export ID")
        _require_machine_token(self.project_id, "Export project ID")
        _require_machine_token(self.snapshot_id, "Export snapshot ID")
        _require_machine_token(self.export_kind, "Export kind")
        _require_machine_token(self.export_format, "Export format")
        _require_filename(self.filename, "Export filename")
        _require_text(self.content_type, "Export content type")
        _require_storage_ref(self.storage_ref, "Export storage reference")
        _require_timestamp(self.created_at, "Export created_at")


@dataclass(frozen=True, slots=True)
class ProjectSettingsRecord:
    """Persisted project settings that do not override engine rules."""

    project_id: str
    default_export_format: str = "markdown"
    locale: str = "en-US"

    def __post_init__(self) -> None:
        """Validate project settings."""
        _require_machine_token(self.project_id, "Settings project ID")
        _require_machine_token(self.default_export_format, "Default export format")
        _require_text(self.locale, "Settings locale")


def _require_machine_token(value: str, label: str) -> None:
    """Require a stable machine-readable token."""
    if not isinstance(value, str) or not _MACHINE_TOKEN_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a machine-readable token.")


def _require_text(value: str, label: str) -> None:
    """Require nonblank human-readable text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} cannot be blank.")


def _require_email_like(value: str, label: str) -> None:
    """Require a minimal email-like value without owning auth policy."""
    _require_text(value, label)
    if any(character.isspace() for character in value):
        raise ValueError(f"{label} cannot contain whitespace.")
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValueError(f"{label} must be email-like.")


def _require_filename(value: str, label: str) -> None:
    """Require a filename metadata value, not a filesystem path."""
    _require_text(value, label)
    if "/" in value or "\\" in value:
        raise ValueError(f"{label} cannot contain path separators.")
    if value in {".", ".."}:
        raise ValueError(f"{label} cannot be a relative path segment.")


def _require_storage_ref(value: str, label: str) -> None:
    """Require a nonblank storage or job reference."""
    _require_text(value, label)
    if any(character.isspace() for character in value):
        raise ValueError(f"{label} cannot contain whitespace.")
    scheme, separator, path = value.partition("://")
    if not separator or not scheme or not path:
        raise ValueError(f"{label} must use scheme://path notation.")
    _require_machine_token(scheme, f"{label} scheme")
    if ".." in path.split("/"):
        raise ValueError(f"{label} cannot contain parent-directory traversal.")


def _require_non_negative(value: int, label: str) -> None:
    """Require a non-negative integer count."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer.")


def _require_serialized_payload(value: str, content_type: str) -> None:
    """Require serialized output to match known structured content types."""
    if content_type == "application/json":
        try:
            json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError("Snapshot serialized output must be valid JSON.") from error


def _require_timestamp(value: str, label: str) -> datetime:
    """Require and return a valid UTC timestamp string ending in Z."""
    _require_text(value, label)
    if "T" not in value or not value.endswith("Z"):
        raise ValueError(f"{label} must be an ISO UTC timestamp ending in Z.")
    try:
        return datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO UTC timestamp ending in Z.") from error

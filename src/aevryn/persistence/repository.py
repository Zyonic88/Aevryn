"""Repository contract for Aevryn platform persistence."""

from __future__ import annotations

from typing import Protocol

from aevryn.persistence.models import (
    EngineRunRecord,
    ExportRecord,
    ImportRecord,
    ProjectRecord,
    ProjectSettingsRecord,
    SnapshotKind,
    SnapshotRecord,
    StoryRecord,
    UserRecord,
)


class PersistenceError(Exception):
    """Base error for platform persistence failures."""


class DuplicateRecordError(PersistenceError):
    """Raised when a record would violate unique identity."""


class RecordNotFoundError(PersistenceError):
    """Raised when a required persisted record does not exist."""


class AccessDeniedError(PersistenceError):
    """Raised when a record exists outside the requested ownership boundary."""


class ProjectRepository(Protocol):
    """Persistence boundary for platform project records."""

    def create_user(self, user: UserRecord) -> None:
        """Persist a user identity record."""

    def get_user(self, user_id: str) -> UserRecord:
        """Return a persisted user or raise if missing."""

    def delete_user_for_auth_rollback(self, user_id: str) -> None:
        """Delete a user created by a failed authentication registration."""

    def create_project(self, project: ProjectRecord) -> None:
        """Persist a project owned by an existing user."""

    def get_project(self, user_id: str, project_id: str) -> ProjectRecord:
        """Return a project inside a user's ownership boundary."""

    def list_projects_for_user(self, user_id: str) -> tuple[ProjectRecord, ...]:
        """Return projects owned by a user in deterministic order."""

    def create_story(self, story: StoryRecord) -> None:
        """Persist a story inside an existing project."""

    def get_story(self, user_id: str, story_id: str) -> StoryRecord:
        """Return a story accessible to a user."""

    def list_stories_for_project(
        self,
        user_id: str,
        project_id: str,
    ) -> tuple[StoryRecord, ...]:
        """Return stories inside a project in deterministic order."""

    def record_import(self, import_record: ImportRecord) -> None:
        """Persist source import metadata."""

    def list_imports_for_story(
        self,
        user_id: str,
        story_id: str,
    ) -> tuple[ImportRecord, ...]:
        """Return import metadata for an accessible story."""

    def get_import(self, user_id: str, import_id: str) -> ImportRecord:
        """Return import metadata accessible to a user."""

    def get_import_for_worker(self, import_id: str) -> ImportRecord:
        """Return import metadata for trusted background worker execution."""

    def record_engine_run(self, run: EngineRunRecord) -> None:
        """Persist an engine run record."""

    def get_engine_run(self, user_id: str, run_id: str) -> EngineRunRecord:
        """Return an engine run accessible to a user."""

    def get_engine_run_for_worker(self, run_id: str) -> EngineRunRecord:
        """Return an engine run for trusted background worker execution."""

    def list_engine_runs_for_project(
        self,
        user_id: str,
        project_id: str,
    ) -> tuple[EngineRunRecord, ...]:
        """Return engine runs for an accessible project in deterministic order."""

    def update_engine_run(self, run: EngineRunRecord) -> None:
        """Update an existing engine run without changing its scope."""

    def store_snapshot(self, snapshot: SnapshotRecord) -> None:
        """Persist an immutable engine output snapshot."""

    def list_snapshots_for_project(
        self,
        user_id: str,
        project_id: str,
    ) -> tuple[SnapshotRecord, ...]:
        """Return snapshots for an accessible project in deterministic order."""

    def list_snapshots_for_story(
        self,
        user_id: str,
        story_id: str,
        snapshot_kind: SnapshotKind | None = None,
    ) -> tuple[SnapshotRecord, ...]:
        """Return story snapshots, optionally filtered by kind."""

    def get_snapshot(self, user_id: str, snapshot_id: str) -> SnapshotRecord:
        """Return a snapshot accessible to a user."""

    def record_export(self, export: ExportRecord) -> None:
        """Persist export metadata."""

    def list_exports_for_project(
        self,
        user_id: str,
        project_id: str,
    ) -> tuple[ExportRecord, ...]:
        """Return exports for an accessible project in deterministic order."""

    def get_export(self, user_id: str, export_id: str) -> ExportRecord:
        """Return export metadata accessible to a user."""

    def save_project_settings(self, settings: ProjectSettingsRecord) -> None:
        """Persist project settings for an existing project."""

    def get_project_settings(
        self,
        user_id: str,
        project_id: str,
    ) -> ProjectSettingsRecord:
        """Return settings for an accessible project."""

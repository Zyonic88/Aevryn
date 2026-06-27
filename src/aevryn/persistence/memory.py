"""Deterministic in-memory repository for Project Database tests."""

from __future__ import annotations

import logging
from typing import TypeVar

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
from aevryn.persistence.repository import (
    AccessDeniedError,
    DuplicateRecordError,
    RecordNotFoundError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class InMemoryProjectRepository:
    """Store platform project records in memory for deterministic tests.

    This repository proves the Phase 2 persistence contract without choosing a
    production database adapter. It is not durable and must not be used as the
    production Project Database.
    """

    def __init__(self) -> None:
        """Create an empty in-memory repository."""
        self._users: dict[str, UserRecord] = {}
        self._projects: dict[str, ProjectRecord] = {}
        self._stories: dict[str, StoryRecord] = {}
        self._imports: dict[str, ImportRecord] = {}
        self._runs: dict[str, EngineRunRecord] = {}
        self._snapshots: dict[str, SnapshotRecord] = {}
        self._exports: dict[str, ExportRecord] = {}
        self._settings: dict[str, ProjectSettingsRecord] = {}

    def create_user(self, user: UserRecord) -> None:
        """Persist a user identity record."""
        if any(
            existing.email.casefold() == user.email.casefold()
            for existing in self._users.values()
        ):
            raise DuplicateRecordError(f"Duplicate user email: {user.email}")
        self._store_unique(self._users, user.user_id, user, "user")
        logger.debug("user_record_created", extra={"user_id": user.user_id})

    def get_user(self, user_id: str) -> UserRecord:
        """Return a persisted user or raise if missing."""
        return self._get_required(self._users, user_id, "user")

    def create_project(self, project: ProjectRecord) -> None:
        """Persist a project owned by an existing user."""
        self.get_user(project.owner_user_id)
        self._store_unique(self._projects, project.project_id, project, "project")
        logger.debug(
            "project_record_created",
            extra={"project_id": project.project_id, "user_id": project.owner_user_id},
        )

    def get_project(self, user_id: str, project_id: str) -> ProjectRecord:
        """Return a project inside a user's ownership boundary."""
        project = self._get_required(self._projects, project_id, "project")
        if project.owner_user_id != user_id:
            raise AccessDeniedError(f"Project is not owned by user: {project_id}")
        return project

    def list_projects_for_user(self, user_id: str) -> tuple[ProjectRecord, ...]:
        """Return projects owned by a user in deterministic order."""
        self.get_user(user_id)
        return tuple(
            sorted(
                (
                    project
                    for project in self._projects.values()
                    if project.owner_user_id == user_id
                ),
                key=lambda project: project.project_id,
            )
        )

    def create_story(self, story: StoryRecord) -> None:
        """Persist a story inside an existing project."""
        self._get_required(self._projects, story.project_id, "project")
        self._store_unique(self._stories, story.story_id, story, "story")
        logger.debug(
            "story_record_created",
            extra={"story_id": story.story_id, "project_id": story.project_id},
        )

    def get_story(self, user_id: str, story_id: str) -> StoryRecord:
        """Return a story accessible to a user."""
        story = self._get_required(self._stories, story_id, "story")
        self.get_project(user_id=user_id, project_id=story.project_id)
        return story

    def list_stories_for_project(
        self,
        user_id: str,
        project_id: str,
    ) -> tuple[StoryRecord, ...]:
        """Return stories inside a project in deterministic order."""
        self.get_project(user_id=user_id, project_id=project_id)
        return tuple(
            sorted(
                (
                    story
                    for story in self._stories.values()
                    if story.project_id == project_id
                ),
                key=lambda story: story.story_id,
            )
        )

    def record_import(self, import_record: ImportRecord) -> None:
        """Persist source import metadata."""
        self._get_required(self._stories, import_record.story_id, "story")
        self._store_unique(
            self._imports,
            import_record.import_id,
            import_record,
            "import",
        )
        logger.debug(
            "import_record_created",
            extra={
                "import_id": import_record.import_id,
                "story_id": import_record.story_id,
            },
        )

    def list_imports_for_story(
        self,
        user_id: str,
        story_id: str,
    ) -> tuple[ImportRecord, ...]:
        """Return import metadata for an accessible story."""
        self.get_story(user_id=user_id, story_id=story_id)
        return tuple(
            sorted(
                (
                    import_record
                    for import_record in self._imports.values()
                    if import_record.story_id == story_id
                ),
                key=lambda import_record: import_record.import_id,
            )
        )

    def get_import(self, user_id: str, import_id: str) -> ImportRecord:
        """Return import metadata accessible to a user."""
        import_record = self._get_required(self._imports, import_id, "import")
        self.get_story(user_id=user_id, story_id=import_record.story_id)
        return import_record

    def record_engine_run(self, run: EngineRunRecord) -> None:
        """Persist an engine run record."""
        self._require_story_in_project(story_id=run.story_id, project_id=run.project_id)
        import_record = self._get_required(self._imports, run.import_id, "import")
        if import_record.story_id != run.story_id:
            raise ValueError("Engine run import must belong to the same story.")
        self._store_unique(self._runs, run.run_id, run, "engine run")
        logger.debug("engine_run_record_created", extra={"run_id": run.run_id})

    def get_engine_run(self, user_id: str, run_id: str) -> EngineRunRecord:
        """Return an engine run accessible to a user."""
        run = self._get_required(self._runs, run_id, "engine run")
        self.get_project(user_id=user_id, project_id=run.project_id)
        return run

    def get_engine_run_for_worker(self, run_id: str) -> EngineRunRecord:
        """Return an engine run for trusted background worker execution."""
        return self._get_required(self._runs, run_id, "engine run")

    def list_engine_runs_for_project(
        self,
        user_id: str,
        project_id: str,
    ) -> tuple[EngineRunRecord, ...]:
        """Return engine runs for an accessible project in deterministic order."""
        self.get_project(user_id=user_id, project_id=project_id)
        return tuple(
            sorted(
                (run for run in self._runs.values() if run.project_id == project_id),
                key=lambda run: run.run_id,
            )
        )

    def update_engine_run(self, run: EngineRunRecord) -> None:
        """Update an existing engine run without changing its scope."""
        existing = self._get_required(self._runs, run.run_id, "engine run")
        if (
            existing.project_id != run.project_id
            or existing.story_id != run.story_id
            or existing.import_id != run.import_id
        ):
            raise ValueError("Engine run updates cannot change run scope.")
        allowed_transitions = {
            "pending": {"running", "succeeded", "failed"},
            "running": {"succeeded", "failed"},
            "succeeded": set(),
            "failed": set(),
        }
        if run.status != existing.status and run.status not in allowed_transitions[existing.status]:
            raise ValueError("Engine run status transition is invalid.")
        self._runs[run.run_id] = run
        logger.debug("engine_run_record_updated", extra={"run_id": run.run_id})

    def store_snapshot(self, snapshot: SnapshotRecord) -> None:
        """Persist an immutable engine output snapshot."""
        self._require_story_in_project(
            story_id=snapshot.story_id,
            project_id=snapshot.project_id,
        )
        run = self._get_required(self._runs, snapshot.run_id, "engine run")
        if run.project_id != snapshot.project_id or run.story_id != snapshot.story_id:
            raise ValueError("Snapshot run must belong to the same project and story.")
        if run.status != "succeeded":
            raise ValueError("Snapshots can only be stored for succeeded engine runs.")
        self._store_unique(
            self._snapshots,
            snapshot.snapshot_id,
            snapshot,
            "snapshot",
        )
        logger.debug(
            "snapshot_record_created",
            extra={
                "snapshot_id": snapshot.snapshot_id,
                "snapshot_kind": snapshot.snapshot_kind,
            },
        )

    def list_snapshots_for_project(
        self,
        user_id: str,
        project_id: str,
    ) -> tuple[SnapshotRecord, ...]:
        """Return snapshots for an accessible project in deterministic order."""
        self.get_project(user_id=user_id, project_id=project_id)
        return tuple(
            sorted(
                (
                    snapshot
                    for snapshot in self._snapshots.values()
                    if snapshot.project_id == project_id
                ),
                key=lambda snapshot: snapshot.snapshot_id,
            )
        )

    def list_snapshots_for_story(
        self,
        user_id: str,
        story_id: str,
        snapshot_kind: SnapshotKind | None = None,
    ) -> tuple[SnapshotRecord, ...]:
        """Return story snapshots, optionally filtered by kind."""
        self.get_story(user_id=user_id, story_id=story_id)
        return tuple(
            sorted(
                (
                    snapshot
                    for snapshot in self._snapshots.values()
                    if snapshot.story_id == story_id
                    and (snapshot_kind is None or snapshot.snapshot_kind == snapshot_kind)
                ),
                key=lambda snapshot: snapshot.snapshot_id,
            )
        )

    def get_snapshot(self, user_id: str, snapshot_id: str) -> SnapshotRecord:
        """Return a snapshot accessible to a user."""
        snapshot = self._get_required(self._snapshots, snapshot_id, "snapshot")
        self.get_project(user_id=user_id, project_id=snapshot.project_id)
        return snapshot

    def record_export(self, export: ExportRecord) -> None:
        """Persist export metadata."""
        snapshot = self._get_required(self._snapshots, export.snapshot_id, "snapshot")
        if snapshot.project_id != export.project_id:
            raise ValueError("Export snapshot must belong to the export project.")
        if snapshot.snapshot_kind != export.export_kind:
            raise ValueError("Export kind must match snapshot kind.")
        self._store_unique(self._exports, export.export_id, export, "export")
        logger.debug("export_record_created", extra={"export_id": export.export_id})

    def list_exports_for_project(
        self,
        user_id: str,
        project_id: str,
    ) -> tuple[ExportRecord, ...]:
        """Return exports for an accessible project in deterministic order."""
        self.get_project(user_id=user_id, project_id=project_id)
        return tuple(
            sorted(
                (
                    export
                    for export in self._exports.values()
                    if export.project_id == project_id
                ),
                key=lambda export: export.export_id,
            )
        )

    def get_export(self, user_id: str, export_id: str) -> ExportRecord:
        """Return export metadata accessible to a user."""
        export = self._get_required(self._exports, export_id, "export")
        self.get_project(user_id=user_id, project_id=export.project_id)
        return export

    def save_project_settings(self, settings: ProjectSettingsRecord) -> None:
        """Persist project settings for an existing project."""
        self._get_required(self._projects, settings.project_id, "project")
        self._settings[settings.project_id] = settings
        logger.debug(
            "project_settings_saved",
            extra={"project_id": settings.project_id},
        )

    def get_project_settings(
        self,
        user_id: str,
        project_id: str,
    ) -> ProjectSettingsRecord:
        """Return settings for an accessible project."""
        self.get_project(user_id=user_id, project_id=project_id)
        settings = self._settings.get(project_id)
        if settings is None:
            return ProjectSettingsRecord(project_id=project_id)
        return settings

    def _require_story_in_project(self, story_id: str, project_id: str) -> StoryRecord:
        """Return a story or raise if it does not belong to the project."""
        story = self._get_required(self._stories, story_id, "story")
        if story.project_id != project_id:
            raise ValueError("Story does not belong to project.")
        return story

    @staticmethod
    def _store_unique(
        records: dict[str, T],
        record_id: str,
        record: T,
        label: str,
    ) -> None:
        """Store a record or raise on duplicate identity."""
        if record_id in records:
            raise DuplicateRecordError(f"Duplicate {label}: {record_id}")
        records[record_id] = record

    @staticmethod
    def _get_required(
        records: dict[str, T],
        record_id: str,
        label: str,
    ) -> T:
        """Return a record or raise a typed missing-record error."""
        record = records.get(record_id)
        if record is None:
            raise RecordNotFoundError(f"Unknown {label}: {record_id}")
        return record

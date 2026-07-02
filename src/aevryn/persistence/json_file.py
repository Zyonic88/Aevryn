"""Deterministic JSON repository for local Project Database persistence."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any, TypeVar

from aevryn.persistence.memory import InMemoryProjectRepository
from aevryn.persistence.models import (
    EngineRunRecord,
    ExportRecord,
    ImportRecord,
    ProjectRecord,
    ProjectSettingsRecord,
    SnapshotRecord,
    StoryRecord,
    UserRecord,
)
from aevryn.persistence.repository import (
    PersistenceError,
    ProjectDeletionResult,
    RecordNotFoundError,
)
from aevryn.persistence.schema import PROJECT_DATABASE_SCHEMA

logger = logging.getLogger(__name__)

T = TypeVar("T")


class JsonProjectRepository(InMemoryProjectRepository):
    """Persist project records to deterministic JSON for local platform runs.

    This adapter is intentionally simple. It proves durable repository behavior
    without becoming the production PostgreSQL adapter.
    """

    def __init__(self, database_path: Path) -> None:
        """Open a local JSON repository file, creating it on first write."""
        super().__init__()
        self._database_path = database_path
        self._load()

    def create_user(self, user: UserRecord) -> None:
        """Persist a user identity record and flush the local store."""
        self._commit(lambda: super(JsonProjectRepository, self).create_user(user))

    def create_project(self, project: ProjectRecord) -> None:
        """Persist a project record and flush the local store."""
        self._commit(lambda: super(JsonProjectRepository, self).create_project(project))

    def delete_project(self, user_id: str, project_id: str) -> ProjectDeletionResult:
        """Hard-delete a project and flush the local store."""
        result = ProjectDeletionResult(deleted_imports=(), deleted_exports=())

        def delete() -> None:
            nonlocal result
            result = super(JsonProjectRepository, self).delete_project(
                user_id=user_id,
                project_id=project_id,
            )

        self._commit(delete)
        return result

    def create_story(self, story: StoryRecord) -> None:
        """Persist a story record and flush the local store."""
        self._commit(lambda: super(JsonProjectRepository, self).create_story(story))

    def delete_story(self, user_id: str, story_id: str) -> tuple[ImportRecord, ...]:
        """Hard-delete a story and flush the local store."""
        deleted_imports: tuple[ImportRecord, ...] = ()

        def delete() -> None:
            nonlocal deleted_imports
            deleted_imports = super(JsonProjectRepository, self).delete_story(
                user_id=user_id,
                story_id=story_id,
            )

        self._commit(delete)
        return deleted_imports

    def record_import(self, import_record: ImportRecord) -> None:
        """Persist import metadata and flush the local store."""
        self._commit(lambda: super(JsonProjectRepository, self).record_import(import_record))

    def record_engine_run(self, run: EngineRunRecord) -> None:
        """Persist an engine run record and flush the local store."""
        self._commit(lambda: super(JsonProjectRepository, self).record_engine_run(run))

    def update_engine_run(self, run: EngineRunRecord) -> None:
        """Update an engine run record and flush the local store."""
        self._commit(lambda: super(JsonProjectRepository, self).update_engine_run(run))

    def store_snapshot(self, snapshot: SnapshotRecord) -> None:
        """Persist a snapshot record and flush the local store."""
        self._commit(lambda: super(JsonProjectRepository, self).store_snapshot(snapshot))

    def record_export(self, export: ExportRecord) -> None:
        """Persist export metadata and flush the local store."""
        self._commit(lambda: super(JsonProjectRepository, self).record_export(export))

    def save_project_settings(self, settings: ProjectSettingsRecord) -> None:
        """Persist project settings and flush the local store."""
        self._commit(lambda: super(JsonProjectRepository, self).save_project_settings(settings))

    def _commit(self, mutation: Callable[[], None]) -> None:
        """Apply a mutation and rollback memory state if disk persistence fails."""
        state = self._snapshot_state()
        try:
            mutation()
            self._save()
        except Exception:
            self._restore_state(state)
            raise

    def _snapshot_state(self) -> tuple[dict[str, Any], ...]:
        """Return a shallow copy of all in-memory record dictionaries."""
        return (
            self._users.copy(),
            self._projects.copy(),
            self._stories.copy(),
            self._imports.copy(),
            self._runs.copy(),
            self._snapshots.copy(),
            self._exports.copy(),
            self._settings.copy(),
        )

    def _restore_state(self, state: tuple[dict[str, Any], ...]) -> None:
        """Restore in-memory record dictionaries after a failed commit."""
        (
            self._users,
            self._projects,
            self._stories,
            self._imports,
            self._runs,
            self._snapshots,
            self._exports,
            self._settings,
        ) = state

    def _load(self) -> None:
        """Load existing JSON records into memory."""
        if not self._database_path.exists():
            return
        try:
            payload = json.loads(self._database_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise PersistenceError("Project database JSON is malformed.") from error
        if not isinstance(payload, dict):
            raise PersistenceError("Project database JSON root must be an object.")
        if payload.get("schema_version") != PROJECT_DATABASE_SCHEMA.schema_version:
            raise PersistenceError("Project database schema version is unsupported.")
        _require_payload_sections(payload)

        self._users = _load_records(payload, "users", UserRecord, "user_id")
        self._projects = _load_records(payload, "projects", ProjectRecord, "project_id")
        self._stories = _load_records(payload, "stories", StoryRecord, "story_id")
        self._imports = _load_records(payload, "imports", ImportRecord, "import_id")
        self._runs = _load_records(payload, "engine_runs", EngineRunRecord, "run_id")
        self._snapshots = _load_records(payload, "snapshots", SnapshotRecord, "snapshot_id")
        self._exports = _load_records(payload, "exports", ExportRecord, "export_id")
        self._settings = _load_records(
            payload,
            "project_settings",
            ProjectSettingsRecord,
            "project_id",
        )
        self._validate_loaded_uniqueness()
        self._validate_loaded_relationships()
        logger.debug("json_project_repository_loaded", extra={"adapter": "local_json"})

    def _validate_loaded_uniqueness(self) -> None:
        """Reject persisted records that violate repository uniqueness rules."""
        emails: set[str] = set()
        for user in self._users.values():
            email = user.email.casefold()
            if email in emails:
                raise PersistenceError("Project database contains duplicate user email.")
            emails.add(email)

    def _validate_loaded_relationships(self) -> None:
        """Reject persisted records with broken ownership relationships."""
        try:
            for project in self._projects.values():
                self.get_user(project.owner_user_id)
            for story in self._stories.values():
                self._get_required(self._projects, story.project_id, "project")
            for import_record in self._imports.values():
                self._get_required(self._stories, import_record.story_id, "story")
            for run in self._runs.values():
                self._require_story_in_project(
                    story_id=run.story_id,
                    project_id=run.project_id,
                )
                import_record = self._get_required(self._imports, run.import_id, "import")
                if import_record.story_id != run.story_id:
                    raise ValueError("Engine run import must belong to the same story.")
            for snapshot in self._snapshots.values():
                self._require_story_in_project(
                    story_id=snapshot.story_id,
                    project_id=snapshot.project_id,
                )
                run = self._get_required(self._runs, snapshot.run_id, "engine run")
                if run.project_id != snapshot.project_id or run.story_id != snapshot.story_id:
                    raise ValueError("Snapshot run must belong to the same project and story.")
                if run.status != "succeeded":
                    raise ValueError("Snapshots can only be stored for succeeded engine runs.")
            for export in self._exports.values():
                snapshot = self._get_required(self._snapshots, export.snapshot_id, "snapshot")
                if snapshot.project_id != export.project_id:
                    raise ValueError("Export snapshot must belong to the export project.")
                if snapshot.snapshot_kind != export.export_kind:
                    raise ValueError("Export kind must match snapshot kind.")
            for settings in self._settings.values():
                self._get_required(self._projects, settings.project_id, "project")
        except (RecordNotFoundError, ValueError) as error:
            raise PersistenceError("Project database relationships are invalid.") from error


    def _save(self) -> None:
        """Write the current repository state as deterministic JSON."""
        payload = {
            "schema_version": PROJECT_DATABASE_SCHEMA.schema_version,
            "users": _dump_records(self._users),
            "projects": _dump_records(self._projects),
            "stories": _dump_records(self._stories),
            "imports": _dump_records(self._imports),
            "engine_runs": _dump_records(self._runs),
            "snapshots": _dump_records(self._snapshots),
            "exports": _dump_records(self._exports),
            "project_settings": _dump_records(self._settings),
        }
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._database_path.with_suffix(f"{self._database_path.suffix}.tmp")
        temporary_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(self._database_path)
        logger.debug("json_project_repository_saved", extra={"adapter": "local_json"})


def _require_payload_sections(payload: dict[str, Any]) -> None:
    """Require every known repository section in persisted JSON."""
    required_sections = {
        "schema_version",
        "users",
        "projects",
        "stories",
        "imports",
        "engine_runs",
        "snapshots",
        "exports",
        "project_settings",
    }
    missing_sections = sorted(required_sections.difference(payload))
    if missing_sections:
        raise PersistenceError(
            "Project database JSON is missing required sections: "
            + ", ".join(missing_sections)
        )
    unknown_sections = sorted(set(payload).difference(required_sections))
    if unknown_sections:
        raise PersistenceError(
            "Project database JSON contains unknown sections: "
            + ", ".join(unknown_sections)
        )


def _dump_records(records: dict[str, Any]) -> list[dict[str, Any]]:
    """Return records as sorted JSON-compatible dictionaries."""
    return [asdict(records[record_id]) for record_id in sorted(records)]


def _load_records(
    payload: dict[str, Any],
    key: str,
    record_type: type[T],
    id_field: str,
) -> dict[str, T]:
    """Load and validate records from one JSON payload section."""
    raw_records = payload.get(key, [])
    if not isinstance(raw_records, list):
        raise PersistenceError(f"Project database section is invalid: {key}")
    records: dict[str, T] = {}
    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            raise PersistenceError(f"Project database record is invalid: {key}")
        record = record_type(**raw_record)
        record_id = getattr(record, id_field)
        if record_id in records:
            raise PersistenceError(f"Project database contains duplicate record: {record_id}")
        records[record_id] = record
    return records

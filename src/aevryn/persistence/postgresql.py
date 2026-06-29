"""PostgreSQL Project Database adapter."""

from __future__ import annotations

import importlib
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, cast

from aevryn.persistence.json_file import _dump_records, _load_records
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
from aevryn.persistence.repository import PersistenceError, RecordNotFoundError
from aevryn.persistence.schema import (
    PROJECT_DATABASE_SCHEMA,
    ColumnDefinition,
    postgresql_create_index_statements,
    postgresql_create_table_statements,
)

logger = logging.getLogger(__name__)

ConnectFactory = Callable[[str], Any]


class PostgresqlProjectRepository(InMemoryProjectRepository):
    """Persist project records to PostgreSQL through the Project Repository contract.

    This first production adapter keeps the existing repository semantics and
    uses PostgreSQL as the durable store. It intentionally reuses the logical
    Project Database schema instead of creating a parallel production schema.
    """

    def __init__(
        self,
        database_url: str,
        *,
        connect_factory: ConnectFactory | None = None,
        bootstrap_schema: bool = True,
    ) -> None:
        """Open a PostgreSQL repository and load existing records."""
        super().__init__()
        self._database_url = _required_database_url(database_url)
        self._connect_factory = connect_factory or _default_connect_factory()
        if bootstrap_schema:
            self.bootstrap_schema()
        self._load()

    def bootstrap_schema(self) -> None:
        """Create missing PostgreSQL tables and indexes for the current schema."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                for statement in _create_table_if_not_exists_statements():
                    cursor.execute(statement)
                for statement in _add_missing_column_statements():
                    cursor.execute(statement)
                for statement in _create_constraint_if_missing_statements():
                    cursor.execute(statement)
                for statement in _create_index_if_not_exists_statements():
                    cursor.execute(statement)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS aevryn_schema_versions (
                        schema_version text PRIMARY KEY,
                        applied_at timestamptz NOT NULL DEFAULT now()
                    );
                    """
                )
                cursor.execute(
                    """
                    INSERT INTO aevryn_schema_versions (schema_version)
                    VALUES (%s)
                    ON CONFLICT (schema_version) DO NOTHING;
                    """,
                    (PROJECT_DATABASE_SCHEMA.schema_version,),
                )
            connection.commit()

    def create_user(self, user: UserRecord) -> None:
        """Persist a user identity record and flush the PostgreSQL store."""
        self._commit(lambda: super(PostgresqlProjectRepository, self).create_user(user))

    def create_project(self, project: ProjectRecord) -> None:
        """Persist a project record and flush the PostgreSQL store."""
        self._commit(lambda: super(PostgresqlProjectRepository, self).create_project(project))

    def create_story(self, story: StoryRecord) -> None:
        """Persist a story record and flush the PostgreSQL store."""
        self._commit(lambda: super(PostgresqlProjectRepository, self).create_story(story))

    def delete_story(self, user_id: str, story_id: str) -> tuple[ImportRecord, ...]:
        """Hard-delete a story and flush the PostgreSQL store."""
        deleted_imports: tuple[ImportRecord, ...] = ()

        def delete() -> None:
            nonlocal deleted_imports
            deleted_imports = super(PostgresqlProjectRepository, self).delete_story(
                user_id=user_id,
                story_id=story_id,
            )

        self._commit(delete)
        return deleted_imports

    def record_import(self, import_record: ImportRecord) -> None:
        """Persist import metadata and flush the PostgreSQL store."""
        self._commit(lambda: super(PostgresqlProjectRepository, self).record_import(import_record))

    def record_engine_run(self, run: EngineRunRecord) -> None:
        """Persist an engine run record and flush the PostgreSQL store."""
        self._commit(lambda: super(PostgresqlProjectRepository, self).record_engine_run(run))

    def update_engine_run(self, run: EngineRunRecord) -> None:
        """Update an engine run record and flush the PostgreSQL store."""
        self._commit(lambda: super(PostgresqlProjectRepository, self).update_engine_run(run))

    def store_snapshot(self, snapshot: SnapshotRecord) -> None:
        """Persist a snapshot record and flush the PostgreSQL store."""
        self._commit(lambda: super(PostgresqlProjectRepository, self).store_snapshot(snapshot))

    def record_export(self, export: ExportRecord) -> None:
        """Persist export metadata and flush the PostgreSQL store."""
        self._commit(lambda: super(PostgresqlProjectRepository, self).record_export(export))

    def save_project_settings(self, settings: ProjectSettingsRecord) -> None:
        """Persist project settings and flush the PostgreSQL store."""
        self._commit(
            lambda: super(PostgresqlProjectRepository, self).save_project_settings(settings)
        )

    def _connect(self) -> Any:
        """Return a new PostgreSQL connection."""
        return self._connect_factory(self._database_url)

    def _commit(self, mutation: Callable[[], None]) -> None:
        """Apply a mutation and rollback memory state if PostgreSQL persistence fails."""
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
        """Load PostgreSQL records into memory."""
        payload: dict[str, Any] = {"schema_version": PROJECT_DATABASE_SCHEMA.schema_version}
        with self._connect() as connection:
            with connection.cursor() as cursor:
                payload["users"] = _fetch_records(cursor, "users")
                payload["projects"] = _fetch_records(cursor, "projects")
                payload["stories"] = _fetch_records(cursor, "stories")
                payload["imports"] = _fetch_records(cursor, "imports")
                payload["engine_runs"] = _fetch_records(cursor, "engine_runs")
                payload["snapshots"] = _fetch_records(cursor, "snapshots")
                payload["exports"] = _fetch_records(cursor, "exports")
                payload["project_settings"] = _fetch_records(cursor, "project_settings")

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
        logger.debug("postgresql_project_repository_loaded")

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
        """Write the current repository state to PostgreSQL in one transaction."""
        with self._connect() as connection:
            try:
                with connection.cursor() as cursor:
                    for table_name in (
                        "project_settings",
                        "exports",
                        "snapshots",
                        "engine_runs",
                        "imports",
                        "stories",
                        "projects",
                        "users",
                    ):
                        cursor.execute(f"DELETE FROM {table_name};")  # nosec B608
                    _insert_records(cursor, "users", _dump_records(self._users))
                    _insert_records(cursor, "projects", _dump_records(self._projects))
                    _insert_records(cursor, "stories", _dump_records(self._stories))
                    _insert_records(cursor, "imports", _dump_records(self._imports))
                    _insert_records(cursor, "engine_runs", _dump_records(self._runs))
                    _insert_records(cursor, "snapshots", _dump_records(self._snapshots))
                    _insert_records(cursor, "exports", _dump_records(self._exports))
                    _insert_records(
                        cursor,
                        "project_settings",
                        _dump_records(self._settings),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        logger.debug("postgresql_project_repository_saved")


def _required_database_url(database_url: str) -> str:
    """Return a nonblank PostgreSQL database URL."""
    if not isinstance(database_url, str) or not database_url.strip():
        raise ValueError("PostgreSQL database URL cannot be blank.")
    if not database_url.startswith(("postgresql://", "postgres://")):
        raise ValueError("PostgreSQL database URL must use postgresql:// or postgres://.")
    return database_url.strip()


def _default_connect_factory() -> ConnectFactory:
    """Return psycopg's connect function, or raise with install guidance."""
    try:
        psycopg = importlib.import_module("psycopg")
    except ModuleNotFoundError as error:
        raise PersistenceError(
            "psycopg is required for the PostgreSQL Project Database adapter. "
            "Install the Aevryn postgresql optional dependencies."
        ) from error
    return cast(ConnectFactory, psycopg.connect)


def _create_table_if_not_exists_statements() -> tuple[str, ...]:
    """Return idempotent table creation statements."""
    return tuple(
        statement.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ", 1)
        for statement in postgresql_create_table_statements()
    )


def _create_constraint_if_missing_statements() -> tuple[str, ...]:
    """Return idempotent check-constraint creation statements."""
    return tuple(
        "\n".join(
            (
                "DO $$",
                "BEGIN",
                f"    {statement}",
                "EXCEPTION WHEN duplicate_object THEN",
                "    NULL;",
                "END $$;",
            )
        )
        for statement in _constraint_statements()
    )


def _add_missing_column_statements() -> tuple[str, ...]:
    """Return idempotent column migration statements for existing dev databases."""
    statements: list[str] = []
    for table in PROJECT_DATABASE_SCHEMA.tables:
        for column in table.columns:
            statements.append(
                f"ALTER TABLE {table.name} ADD COLUMN IF NOT EXISTS "
                f"{_postgresql_column_without_primary_key(column)};"  # nosec B608
            )
    return tuple(statements)


def _postgresql_column_without_primary_key(column: ColumnDefinition) -> str:
    """Render a column definition suitable for ADD COLUMN IF NOT EXISTS."""
    parts = [column.name, column.data_type]
    if not column.nullable and not column.primary_key:
        parts.append("NOT NULL")
        parts.append(f"DEFAULT {_default_value_for_column(column)}")
    return " ".join(parts)


def _default_value_for_column(column: ColumnDefinition) -> str:
    """Return a conservative default for adding non-null columns to existing tables."""
    if column.data_type == "integer":
        return "0"
    if column.data_type == "jsonb":
        return "'{}'::jsonb"
    if column.data_type == "timestamptz":
        return "'1970-01-01T00:00:00Z'"
    return "''"


def _constraint_statements() -> tuple[str, ...]:
    """Return plain PostgreSQL check-constraint creation statements."""
    from aevryn.persistence.schema import postgresql_create_constraint_statements

    return postgresql_create_constraint_statements()


def _create_index_if_not_exists_statements() -> tuple[str, ...]:
    """Return idempotent index creation statements."""
    statements = []
    for statement in postgresql_create_index_statements():
        if statement.startswith("CREATE UNIQUE INDEX "):
            statements.append(
                statement.replace("CREATE UNIQUE INDEX ", "CREATE UNIQUE INDEX IF NOT EXISTS ", 1)
            )
        else:
            statements.append(
                statement.replace("CREATE INDEX ", "CREATE INDEX IF NOT EXISTS ", 1)
            )
    return tuple(statements)


def _fetch_records(cursor: Any, table_name: str) -> list[dict[str, Any]]:
    """Fetch all records from a table as JSON-compatible dictionaries."""
    columns = _table_columns(table_name)
    cursor.execute(
        f"SELECT {', '.join(columns)} FROM {table_name} "
        f"ORDER BY {_primary_key(table_name)};"  # nosec B608
    )
    rows = cursor.fetchall()
    return [
        {
            column_name: _json_compatible_value(column_name, value)
            for column_name, value in zip(columns, row, strict=True)
        }
        for row in rows
    ]


def _insert_records(cursor: Any, table_name: str, records: list[dict[str, Any]]) -> None:
    """Insert records into one PostgreSQL table."""
    if not records:
        return
    columns = _table_columns(table_name)
    placeholders = ", ".join(["%s"] * len(columns))
    statement = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders});"  # nosec B608
    for record in records:
        cursor.execute(statement, tuple(_db_value(column, record[column]) for column in columns))


def _table_columns(table_name: str) -> tuple[str, ...]:
    """Return schema columns for a table."""
    for table in PROJECT_DATABASE_SCHEMA.tables:
        if table.name == table_name:
            return tuple(column.name for column in table.columns)
    raise ValueError(f"Unknown Project Database table: {table_name}")


def _primary_key(table_name: str) -> str:
    """Return the primary-key column for a table."""
    for table in PROJECT_DATABASE_SCHEMA.tables:
        if table.name == table_name:
            for column in table.columns:
                if column.primary_key:
                    return column.name
    raise ValueError(f"Unknown Project Database table: {table_name}")


def _json_compatible_value(column_name: str, value: Any) -> Any:
    """Return a record value compatible with persistence dataclasses."""
    if value is None:
        return None
    if isinstance(value, datetime):
        normalized = value.astimezone(UTC)
        return normalized.isoformat().replace("+00:00", "Z")
    if column_name == "serialized_output" and not isinstance(value, str):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def _db_value(column_name: str, value: Any) -> Any:
    """Return a value suitable for PostgreSQL parameters."""
    if column_name == "serialized_output" and isinstance(value, str):
        return _postgresql_jsonb(json.loads(value))
    return value


def _postgresql_jsonb(value: Any) -> Any:
    """Return a psycopg JSONB wrapper when available."""
    try:
        json_module = importlib.import_module("psycopg.types.json")
    except ModuleNotFoundError:
        return value
    jsonb_type = getattr(json_module, "Jsonb", None)
    if jsonb_type is None:
        return value
    return jsonb_type(value)

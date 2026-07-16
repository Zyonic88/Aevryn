"""Schema manifest for the Aevryn Project Database."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ColumnDefinition:
    """One logical database column definition."""

    name: str
    data_type: str
    nullable: bool = False
    primary_key: bool = False
    unique: bool = False
    references: str = ""

    def __post_init__(self) -> None:
        """Validate column metadata."""
        _require_token(self.name, "Column name")
        _require_text(self.data_type, "Column data type")
        if self.references:
            _require_reference(self.references, "Column reference")


@dataclass(frozen=True, slots=True)
class CheckConstraintDefinition:
    """One logical database check constraint definition."""

    name: str
    table_name: str
    expression: str

    def __post_init__(self) -> None:
        """Validate check constraint metadata."""
        _require_token(self.name, "Check constraint name")
        _require_token(self.table_name, "Check constraint table name")
        _require_text(self.expression, "Check constraint expression")


@dataclass(frozen=True, slots=True)
class IndexDefinition:
    """One logical database index definition."""

    name: str
    table_name: str
    column_names: tuple[str, ...]
    unique: bool = False

    def __post_init__(self) -> None:
        """Validate index metadata."""
        _require_token(self.name, "Index name")
        _require_token(self.table_name, "Index table name")
        if not self.column_names:
            raise ValueError("Index must define at least one column.")
        for column_name in self.column_names:
            _require_token(column_name, "Index column name")


@dataclass(frozen=True, slots=True)
class TableDefinition:
    """One logical database table definition."""

    name: str
    columns: tuple[ColumnDefinition, ...]

    def __post_init__(self) -> None:
        """Validate table metadata."""
        _require_token(self.name, "Table name")
        if not self.columns:
            raise ValueError("Table must define at least one column.")
        names = [column.name for column in self.columns]
        if len(names) != len(set(names)):
            raise ValueError(f"Table has duplicate columns: {self.name}")
        primary_keys = [column for column in self.columns if column.primary_key]
        if len(primary_keys) != 1:
            raise ValueError(f"Table must define exactly one primary key: {self.name}")


@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    """Logical Project Database schema manifest."""

    schema_version: str
    tables: tuple[TableDefinition, ...]
    constraints: tuple[CheckConstraintDefinition, ...] = ()
    indexes: tuple[IndexDefinition, ...] = ()

    def __post_init__(self) -> None:
        """Validate schema metadata."""
        _require_text(self.schema_version, "Schema version")
        if not self.tables:
            raise ValueError("Schema must define at least one table.")
        names = [table.name for table in self.tables]
        if len(names) != len(set(names)):
            raise ValueError("Schema cannot contain duplicate tables.")
        constraint_names = [constraint.name for constraint in self.constraints]
        if len(constraint_names) != len(set(constraint_names)):
            raise ValueError("Schema cannot contain duplicate constraints.")
        index_names = [index.name for index in self.indexes]
        if len(index_names) != len(set(index_names)):
            raise ValueError("Schema cannot contain duplicate indexes.")
        self._validate_references()
        self._validate_reference_order()
        self._validate_constraints()
        self._validate_indexes()

    def table_names(self) -> tuple[str, ...]:
        """Return table names in deterministic creation order."""
        return tuple(table.name for table in self.tables)

    def reference_targets(self) -> tuple[str, ...]:
        """Return foreign-key references in deterministic table order."""
        return tuple(
            column.references
            for table in self.tables
            for column in table.columns
            if column.references
        )

    def constraint_names(self) -> tuple[str, ...]:
        """Return check constraint names in deterministic creation order."""
        return tuple(constraint.name for constraint in self.constraints)

    def index_names(self) -> tuple[str, ...]:
        """Return index names in deterministic creation order."""
        return tuple(index.name for index in self.indexes)

    def _columns_by_table(self) -> dict[str, set[str]]:
        """Return schema columns keyed by table name."""
        return {
            table.name: {column.name for column in table.columns}
            for table in self.tables
        }

    def _validate_references(self) -> None:
        """Validate that every reference points to an existing table column."""
        columns_by_table = self._columns_by_table()
        for reference in self.reference_targets():
            table_name, column_name = reference.split(".")
            if table_name not in columns_by_table:
                raise ValueError(f"Schema reference points to unknown table: {reference}")
            if column_name not in columns_by_table[table_name]:
                raise ValueError(f"Schema reference points to unknown column: {reference}")

    def _validate_reference_order(self) -> None:
        """Validate table order for inline PostgreSQL foreign keys."""
        seen_tables: set[str] = set()
        for table in self.tables:
            for column in table.columns:
                if not column.references:
                    continue
                referenced_table, _ = column.references.split(".")
                if referenced_table != table.name and referenced_table not in seen_tables:
                    raise ValueError(
                        "Schema table order creates a forward reference: "
                        f"{table.name}.{column.name}"
                    )
            seen_tables.add(table.name)

    def _validate_constraints(self) -> None:
        """Validate that every check constraint points to an existing table."""
        table_names = set(self.table_names())
        for constraint in self.constraints:
            if constraint.table_name not in table_names:
                raise ValueError(
                    f"Schema constraint points to unknown table: {constraint.name}"
                )

    def _validate_indexes(self) -> None:
        """Validate that every index points to existing table columns."""
        columns_by_table = self._columns_by_table()
        for index in self.indexes:
            if index.table_name not in columns_by_table:
                raise ValueError(f"Schema index points to unknown table: {index.name}")
            for column_name in index.column_names:
                if column_name not in columns_by_table[index.table_name]:
                    raise ValueError(f"Schema index points to unknown column: {index.name}")


def _require_token(value: str, label: str) -> None:
    """Require lowercase SQL-safe identifier text."""
    if not isinstance(value, str) or not value.replace("_", "").isalnum() or value != value.lower():
        raise ValueError(f"{label} must be a lowercase SQL identifier.")


def _require_text(value: str, label: str) -> None:
    """Require nonblank text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} cannot be blank.")


def _require_reference(value: str, label: str) -> None:
    """Require table.column reference notation."""
    parts = value.split(".")
    if len(parts) != 2:
        raise ValueError(f"{label} must use table.column notation.")
    for part in parts:
        _require_token(part, label)



PROJECT_DATABASE_SCHEMA = SchemaDefinition(
    schema_version="v2_phase_2_001",
    tables=(
        TableDefinition(
            name="users",
            columns=(
                ColumnDefinition("user_id", "text", primary_key=True),
                ColumnDefinition("email", "text", unique=True),
                ColumnDefinition("display_name", "text"),
                ColumnDefinition("created_at", "timestamptz"),
            ),
        ),
        TableDefinition(
            name="projects",
            columns=(
                ColumnDefinition("project_id", "text", primary_key=True),
                ColumnDefinition("owner_user_id", "text", references="users.user_id"),
                ColumnDefinition("name", "text"),
                ColumnDefinition("created_at", "timestamptz"),
                ColumnDefinition("updated_at", "timestamptz"),
            ),
        ),
        TableDefinition(
            name="stories",
            columns=(
                ColumnDefinition("story_id", "text", primary_key=True),
                ColumnDefinition("project_id", "text", references="projects.project_id"),
                ColumnDefinition("title", "text"),
                ColumnDefinition("created_at", "timestamptz"),
                ColumnDefinition("updated_at", "timestamptz"),
            ),
        ),
        TableDefinition(
            name="imports",
            columns=(
                ColumnDefinition("import_id", "text", primary_key=True),
                ColumnDefinition("story_id", "text", references="stories.story_id"),
                ColumnDefinition("source_id", "text"),
                ColumnDefinition("filename", "text"),
                ColumnDefinition("source_format", "text"),
                ColumnDefinition("storage_ref", "text"),
                ColumnDefinition("chapter_count", "integer"),
                ColumnDefinition("scene_count", "integer"),
                ColumnDefinition("evidence_anchor_count", "integer"),
                ColumnDefinition("created_at", "timestamptz"),
            ),
        ),
        TableDefinition(
            name="engine_runs",
            columns=(
                ColumnDefinition("run_id", "text", primary_key=True),
                ColumnDefinition("project_id", "text", references="projects.project_id"),
                ColumnDefinition("story_id", "text", references="stories.story_id"),
                ColumnDefinition("import_id", "text", references="imports.import_id"),
                ColumnDefinition("status", "text"),
                ColumnDefinition("status_updated_at", "timestamptz", nullable=True),
                ColumnDefinition("engine_version", "text"),
                ColumnDefinition("started_at", "timestamptz"),
                ColumnDefinition("finished_at", "timestamptz", nullable=True),
                ColumnDefinition("error_summary", "text", nullable=True),
                ColumnDefinition("job_ref", "text", nullable=True),
            ),
        ),
        TableDefinition(
            name="background_jobs",
            columns=(
                ColumnDefinition("job_id", "text", primary_key=True),
                ColumnDefinition("kind", "text"),
                ColumnDefinition("run_id", "text"),
                ColumnDefinition("project_id", "text"),
                ColumnDefinition("story_id", "text"),
                ColumnDefinition("import_id", "text"),
                ColumnDefinition("status", "text"),
                ColumnDefinition("queued_at", "timestamptz"),
                ColumnDefinition("status_updated_at", "timestamptz"),
                ColumnDefinition("attempts", "integer"),
                ColumnDefinition("max_attempts", "integer"),
                ColumnDefinition("error_summary", "text"),
            ),
        ),
        TableDefinition(
            name="snapshots",
            columns=(
                ColumnDefinition("snapshot_id", "text", primary_key=True),
                ColumnDefinition("project_id", "text", references="projects.project_id"),
                ColumnDefinition("story_id", "text", references="stories.story_id"),
                ColumnDefinition("run_id", "text", references="engine_runs.run_id"),
                ColumnDefinition("snapshot_kind", "text"),
                ColumnDefinition("content_type", "text"),
                ColumnDefinition("serialized_output", "jsonb"),
                ColumnDefinition("created_at", "timestamptz"),
            ),
        ),
        TableDefinition(
            name="exports",
            columns=(
                ColumnDefinition("export_id", "text", primary_key=True),
                ColumnDefinition("project_id", "text", references="projects.project_id"),
                ColumnDefinition("snapshot_id", "text", references="snapshots.snapshot_id"),
                ColumnDefinition("export_kind", "text"),
                ColumnDefinition("export_format", "text"),
                ColumnDefinition("filename", "text"),
                ColumnDefinition("content_type", "text"),
                ColumnDefinition("storage_ref", "text"),
                ColumnDefinition("created_at", "timestamptz"),
                ColumnDefinition("size", "integer"),
                ColumnDefinition("checksum", "text"),
            ),
        ),
        TableDefinition(
            name="project_settings",
            columns=(
                ColumnDefinition(
                    "project_id",
                    "text",
                    primary_key=True,
                    references="projects.project_id",
                ),
                ColumnDefinition("default_export_format", "text"),
                ColumnDefinition("locale", "text"),
            ),
        ),
    ),
    constraints=(
        CheckConstraintDefinition(
            "chk_imports_chapter_count_non_negative",
            "imports",
            "chapter_count >= 0",
        ),
        CheckConstraintDefinition(
            "chk_imports_scene_count_non_negative",
            "imports",
            "scene_count >= 0",
        ),
        CheckConstraintDefinition(
            "chk_imports_evidence_anchor_count_non_negative",
            "imports",
            "evidence_anchor_count >= 0",
        ),
        CheckConstraintDefinition(
            "chk_engine_runs_status",
            "engine_runs",
            "status IN ('pending', 'running', 'succeeded', 'failed')",
        ),
        CheckConstraintDefinition(
            "chk_engine_runs_finished_at_by_status",
            "engine_runs",
            "((status IN ('pending', 'running') AND finished_at IS NULL) OR "
            "(status IN ('succeeded', 'failed') AND finished_at IS NOT NULL))",
        ),
        CheckConstraintDefinition(
            "chk_background_jobs_kind",
            "background_jobs",
            "kind IN ('process_import')",
        ),
        CheckConstraintDefinition(
            "chk_background_jobs_status",
            "background_jobs",
            "status IN ('queued', 'running', 'succeeded', 'failed')",
        ),
        CheckConstraintDefinition(
            "chk_background_jobs_attempts_non_negative",
            "background_jobs",
            "attempts >= 0",
        ),
        CheckConstraintDefinition(
            "chk_background_jobs_max_attempts_positive",
            "background_jobs",
            "max_attempts >= 1",
        ),
        CheckConstraintDefinition(
            "chk_background_jobs_error_summary_by_status",
            "background_jobs",
            "((status = 'failed' AND error_summary <> '') OR "
            "(status <> 'failed' AND error_summary = ''))",
        ),
        CheckConstraintDefinition(
            "chk_snapshots_snapshot_kind",
            "snapshots",
            "snapshot_kind IN ('canon', 'timeline', 'character_profile', "
            "'world_state', 'scene_sheet', 'prompt_pack', 'continuity_report')",
        ),
        CheckConstraintDefinition(
            "chk_exports_size_non_negative",
            "exports",
            "size >= 0",
        ),
    ),
    indexes=(
        IndexDefinition("idx_projects_owner_user_id", "projects", ("owner_user_id",)),
        IndexDefinition("idx_stories_project_id", "stories", ("project_id",)),
        IndexDefinition("idx_imports_story_id", "imports", ("story_id",)),
        IndexDefinition("idx_engine_runs_project_id", "engine_runs", ("project_id",)),
        IndexDefinition("idx_engine_runs_story_id", "engine_runs", ("story_id",)),
        IndexDefinition("idx_background_jobs_status", "background_jobs", ("status",)),
        IndexDefinition(
            "idx_background_jobs_project_id",
            "background_jobs",
            ("project_id",),
        ),
        IndexDefinition(
            "idx_background_jobs_queued_order",
            "background_jobs",
            ("queued_at", "job_id"),
        ),
        IndexDefinition("idx_snapshots_project_id", "snapshots", ("project_id",)),
        IndexDefinition(
            "idx_snapshots_story_kind",
            "snapshots",
            ("story_id", "snapshot_kind"),
        ),
        IndexDefinition("idx_exports_project_id", "exports", ("project_id",)),
    ),
)


def postgresql_create_table_statements(
    schema: SchemaDefinition = PROJECT_DATABASE_SCHEMA,
) -> tuple[str, ...]:
    """Render deterministic PostgreSQL CREATE TABLE statements.

    The renderer is a schema contract aid, not a migration runner. Real
    migrations must still be reviewed and applied deliberately.
    """
    return tuple(_postgresql_create_table(table) for table in schema.tables)


def postgresql_create_constraint_statements(
    schema: SchemaDefinition = PROJECT_DATABASE_SCHEMA,
) -> tuple[str, ...]:
    """Render deterministic PostgreSQL CHECK constraint statements."""
    return tuple(_postgresql_create_constraint(constraint) for constraint in schema.constraints)


def postgresql_create_index_statements(
    schema: SchemaDefinition = PROJECT_DATABASE_SCHEMA,
) -> tuple[str, ...]:
    """Render deterministic PostgreSQL CREATE INDEX statements."""
    return tuple(_postgresql_create_index(index) for index in schema.indexes)


def postgresql_schema_statements(
    schema: SchemaDefinition = PROJECT_DATABASE_SCHEMA,
) -> tuple[str, ...]:
    """Render deterministic PostgreSQL schema statements."""
    return (
        postgresql_create_table_statements(schema)
        + postgresql_create_constraint_statements(schema)
        + postgresql_create_index_statements(schema)
    )


def project_database_schema_digest(
    schema: SchemaDefinition = PROJECT_DATABASE_SCHEMA,
) -> str:
    """Return a deterministic digest for the logical schema contract."""
    payload = "\n\n".join(postgresql_schema_statements(schema)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _postgresql_create_table(table: TableDefinition) -> str:
    """Render one CREATE TABLE statement from a table definition."""
    column_lines = [
        f"    {_postgresql_column_definition(column)}"
        for column in table.columns
    ]
    return "\n".join(
        (
            f"CREATE TABLE {table.name} (",
            ",\n".join(column_lines),
            ");",
        )
    )


def _postgresql_create_constraint(constraint: CheckConstraintDefinition) -> str:
    """Render one PostgreSQL check constraint definition."""
    return (
        f"ALTER TABLE {constraint.table_name} ADD CONSTRAINT {constraint.name} "
        f"CHECK ({constraint.expression});"
    )



def _postgresql_create_index(index: IndexDefinition) -> str:
    """Render one PostgreSQL index definition."""
    unique = "UNIQUE " if index.unique else ""
    columns = ", ".join(index.column_names)
    return f"CREATE {unique}INDEX {index.name} ON {index.table_name} ({columns});"



def _postgresql_column_definition(column: ColumnDefinition) -> str:
    """Render one PostgreSQL column definition."""
    parts = [column.name, column.data_type]
    if column.primary_key:
        parts.append("PRIMARY KEY")
    if not column.nullable and not column.primary_key:
        parts.append("NOT NULL")
    if column.unique:
        parts.append("UNIQUE")
    if column.references:
        table_name, column_name = column.references.split(".")
        parts.append(f"REFERENCES {table_name}({column_name})")
    return " ".join(parts)

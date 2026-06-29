"""Aevryn platform persistence boundary."""

from aevryn.persistence.json_file import JsonProjectRepository
from aevryn.persistence.memory import InMemoryProjectRepository
from aevryn.persistence.models import (
    EngineRunRecord,
    EngineRunStatus,
    ExportRecord,
    ImportRecord,
    ProjectRecord,
    ProjectSettingsRecord,
    SnapshotKind,
    SnapshotRecord,
    StoryRecord,
    UserRecord,
)
from aevryn.persistence.postgresql import PostgresqlProjectRepository
from aevryn.persistence.repository import (
    AccessDeniedError,
    DuplicateRecordError,
    PersistenceError,
    ProjectRepository,
    RecordNotFoundError,
)
from aevryn.persistence.schema import (
    PROJECT_DATABASE_SCHEMA,
    CheckConstraintDefinition,
    ColumnDefinition,
    IndexDefinition,
    SchemaDefinition,
    TableDefinition,
    postgresql_create_constraint_statements,
    postgresql_create_index_statements,
    postgresql_create_table_statements,
    postgresql_schema_statements,
    project_database_schema_digest,
)

__all__ = [
    "AccessDeniedError",
    "CheckConstraintDefinition",
    "ColumnDefinition",
    "DuplicateRecordError",
    "EngineRunRecord",
    "EngineRunStatus",
    "ExportRecord",
    "ImportRecord",
    "InMemoryProjectRepository",
    "IndexDefinition",
    "JsonProjectRepository",
    "PersistenceError",
    "PROJECT_DATABASE_SCHEMA",
    "PostgresqlProjectRepository",
    "ProjectRecord",
    "ProjectRepository",
    "ProjectSettingsRecord",
    "postgresql_create_constraint_statements",
    "postgresql_create_index_statements",
    "postgresql_create_table_statements",
    "postgresql_schema_statements",
    "project_database_schema_digest",
    "RecordNotFoundError",
    "SchemaDefinition",
    "SnapshotKind",
    "SnapshotRecord",
    "StoryRecord",
    "TableDefinition",
    "UserRecord",
]

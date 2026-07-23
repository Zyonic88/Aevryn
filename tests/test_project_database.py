"""Tests for Aevryn V2 Phase 2 persistence foundation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import aevryn.persistence.postgresql as postgresql
from aevryn.persistence import (
    PROJECT_DATABASE_SCHEMA,
    AccessDeniedError,
    CheckConstraintDefinition,
    ColumnDefinition,
    DuplicateRecordError,
    EngineRunRecord,
    ExportRecord,
    ImportRecord,
    IndexDefinition,
    InMemoryProjectRepository,
    JsonProjectRepository,
    PersistenceError,
    PostgresqlProjectRepository,
    ProjectRecord,
    ProjectRepository,
    ProjectSettingsRecord,
    RecordNotFoundError,
    SnapshotKind,
    SnapshotRecord,
    StoryRecord,
    TableDefinition,
    UserRecord,
    postgresql_create_constraint_statements,
    postgresql_create_index_statements,
    postgresql_create_table_statements,
    postgresql_schema_statements,
    project_database_schema_digest,
)

NOW = "2026-06-27T00:00:00Z"



def test_project_database_schema_manifest_defines_phase_2_tables() -> None:
    """Schema manifest should define the Phase 2 persistence target."""
    assert PROJECT_DATABASE_SCHEMA.schema_version == "v2_phase_2_001"
    assert PROJECT_DATABASE_SCHEMA.table_names() == (
        "users",
        "projects",
        "stories",
        "imports",
        "engine_runs",
        "background_jobs",
        "snapshots",
        "exports",
        "project_settings",
    )


def test_project_database_schema_manifest_preserves_relationships() -> None:
    """Schema manifest should encode ownership and snapshot relationships."""
    tables = {table.name: table for table in PROJECT_DATABASE_SCHEMA.tables}
    project_columns = {column.name: column for column in tables["projects"].columns}
    snapshot_columns = {column.name: column for column in tables["snapshots"].columns}
    export_columns = {column.name: column for column in tables["exports"].columns}

    assert project_columns["owner_user_id"].references == "users.user_id"
    assert snapshot_columns["run_id"].references == "engine_runs.run_id"
    assert snapshot_columns["serialized_output"].data_type == "jsonb"
    assert export_columns["snapshot_id"].references == "snapshots.snapshot_id"


def test_project_database_schema_renders_postgresql_contract() -> None:
    """Schema renderer should produce deterministic PostgreSQL DDL."""
    statements = postgresql_create_table_statements()

    assert statements[0].startswith("CREATE TABLE users")
    assert "user_id text PRIMARY KEY" in statements[0]
    assert "email text NOT NULL UNIQUE" in statements[0]
    assert "owner_user_id text NOT NULL REFERENCES users(user_id)" in statements[1]
    assert "run_id text NOT NULL" in statements[5]
    assert "serialized_output jsonb NOT NULL" in statements[6]
    assert statements[-1].endswith(");")


def test_project_database_schema_manifest_defines_check_constraints() -> None:
    """Schema manifest should define database-level data integrity constraints."""
    assert PROJECT_DATABASE_SCHEMA.constraint_names() == (
        "chk_imports_chapter_count_non_negative",
        "chk_imports_scene_count_non_negative",
        "chk_imports_evidence_anchor_count_non_negative",
        "chk_engine_runs_status",
        "chk_engine_runs_finished_at_by_status",
        "chk_background_jobs_kind",
        "chk_background_jobs_status",
        "chk_background_jobs_attempts_non_negative",
        "chk_background_jobs_max_attempts_positive",
        "chk_background_jobs_error_summary_by_status",
        "chk_snapshots_snapshot_kind",
        "chk_exports_size_non_negative",
    )


def test_project_database_schema_renders_postgresql_constraints() -> None:
    """Constraint renderer should produce deterministic PostgreSQL CHECK DDL."""
    statements = postgresql_create_constraint_statements()

    assert statements[0] == (
        "ALTER TABLE imports ADD CONSTRAINT "
        "chk_imports_chapter_count_non_negative CHECK (chapter_count >= 0);"
    )
    assert any("chk_engine_runs_status" in statement for statement in statements)
    assert any("chk_background_jobs_status" in statement for statement in statements)
    assert any("chk_snapshots_snapshot_kind" in statement for statement in statements)


def test_project_database_schema_rejects_forward_references() -> None:
    """Schema table order should be valid for inline foreign keys."""
    with pytest.raises(ValueError, match="forward reference"):
        type(PROJECT_DATABASE_SCHEMA)(
            schema_version="test_schema",
            tables=(
                TableDefinition(
                    name="children",
                    columns=(
                        ColumnDefinition("child_id", "text", primary_key=True),
                        ColumnDefinition("parent_id", "text", references="parents.parent_id"),
                    ),
                ),
                TableDefinition(
                    name="parents",
                    columns=(ColumnDefinition("parent_id", "text", primary_key=True),),
                ),
            ),
        )


def test_project_database_schema_rejects_invalid_constraint_targets() -> None:
    """Schema constraints should only reference existing tables."""
    with pytest.raises(ValueError, match="unknown table"):
        type(PROJECT_DATABASE_SCHEMA)(
            schema_version="test_schema",
            tables=(
                TableDefinition(
                    name="demo",
                    columns=(ColumnDefinition("demo_id", "text", primary_key=True),),
                ),
            ),
            constraints=(
                CheckConstraintDefinition(
                    "chk_missing",
                    "missing",
                    "demo_id IS NOT NULL",
                ),
            ),
        )


def test_project_database_schema_manifest_defines_indexes() -> None:
    """Schema manifest should define indexes for repository read paths."""
    assert PROJECT_DATABASE_SCHEMA.index_names() == (
        "idx_projects_owner_user_id",
        "idx_stories_project_id",
        "idx_imports_story_id",
        "idx_engine_runs_project_id",
        "idx_engine_runs_story_id",
        "idx_background_jobs_status",
        "idx_background_jobs_project_id",
        "idx_background_jobs_queued_order",
        "idx_snapshots_project_id",
        "idx_snapshots_story_kind",
        "idx_exports_project_id",
    )


def test_project_database_schema_digest_matches_rendered_contract() -> None:
    """Schema digest should describe the rendered PostgreSQL contract."""
    payload = "\n\n".join(postgresql_schema_statements()).encode("utf-8")

    assert project_database_schema_digest() == hashlib.sha256(payload).hexdigest()
    assert len(project_database_schema_digest()) == 64


def test_project_database_schema_renders_postgresql_indexes() -> None:
    """Index renderer should produce deterministic PostgreSQL index DDL."""
    statements = postgresql_create_index_statements()

    assert statements[0] == (
        "CREATE INDEX idx_projects_owner_user_id ON projects (owner_user_id);"
    )
    assert (
        "CREATE INDEX idx_snapshots_story_kind ON snapshots "
        "(story_id, snapshot_kind);"
    ) in statements
    assert postgresql_schema_statements() == (
        postgresql_create_table_statements()
        + postgresql_create_constraint_statements()
        + statements
    )


def test_project_database_schema_rejects_invalid_index_targets() -> None:
    """Schema indexes should only reference existing table columns."""
    with pytest.raises(ValueError, match="unknown column"):
        type(PROJECT_DATABASE_SCHEMA)(
            schema_version="test_schema",
            tables=(
                TableDefinition(
                    name="demo",
                    columns=(ColumnDefinition("demo_id", "text", primary_key=True),),
                ),
            ),
            indexes=(IndexDefinition("idx_demo_missing", "demo", ("missing_id",)),),
        )


def test_repository_satisfies_project_repository_protocol() -> None:
    """The in-memory adapter should satisfy the repository contract."""
    repository: ProjectRepository = InMemoryProjectRepository()

    repository.create_user(user_record())

    assert repository.get_user("user_demo").email == "demo@example.com"


def test_project_database_records_full_project_flow() -> None:
    """Repository stores project persistence records without engine logic."""
    repository = seeded_repository()
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())
    repository.store_snapshot(snapshot_record())
    repository.record_export(export_record())
    repository.save_project_settings(
        ProjectSettingsRecord(
            project_id="project_demo",
            default_export_format="json",
            locale="en-US",
        )
    )

    assert repository.list_projects_for_user("user_demo") == (project_record(),)
    assert repository.list_stories_for_project("user_demo", "project_demo") == (
        story_record(),
    )
    assert repository.list_imports_for_story("user_demo", "story_demo") == (
        import_record(),
    )
    assert repository.get_import("user_demo", "import_demo") == import_record()
    assert repository.get_engine_run("user_demo", "run_demo") == engine_run_record()
    assert repository.list_engine_runs_for_project("user_demo", "project_demo") == (
        engine_run_record(),
    )
    assert repository.list_snapshots_for_project("user_demo", "project_demo") == (
        snapshot_record(),
    )
    assert repository.get_snapshot("user_demo", "snapshot_demo") == snapshot_record()
    assert repository.list_exports_for_project("user_demo", "project_demo") == (
        export_record(),
    )
    assert repository.get_export("user_demo", "export_demo") == export_record()
    assert repository.get_project_settings("user_demo", "project_demo").default_export_format == (
        "json"
    )


def test_repository_hard_deletes_story_scoped_records() -> None:
    """Story deletion should remove imports, runs, snapshots, and exports."""
    repository = seeded_repository()
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())
    repository.store_snapshot(snapshot_record())
    repository.record_export(export_record())

    deleted_imports = repository.delete_story("user_demo", "story_demo")

    assert tuple(import_record.import_id for import_record in deleted_imports) == ("import_demo",)
    with pytest.raises(RecordNotFoundError):
        repository.get_story("user_demo", "story_demo")
    with pytest.raises(RecordNotFoundError):
        repository.get_import("user_demo", "import_demo")
    with pytest.raises(RecordNotFoundError):
        repository.get_engine_run("user_demo", "run_demo")
    with pytest.raises(RecordNotFoundError):
        repository.get_snapshot("user_demo", "snapshot_demo")
    with pytest.raises(RecordNotFoundError):
        repository.get_export("user_demo", "export_demo")


def test_repository_hard_deletes_project_scoped_records() -> None:
    """Project deletion should remove stories, runs, snapshots, exports, and settings."""
    repository = seeded_repository()
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())
    repository.store_snapshot(snapshot_record())
    repository.record_export(export_record())
    repository.save_project_settings(
        ProjectSettingsRecord(
            project_id="project_demo",
            default_export_format="json",
            locale="en-US",
        )
    )

    deleted = repository.delete_project("user_demo", "project_demo")

    assert tuple(import_record.import_id for import_record in deleted.deleted_imports) == (
        "import_demo",
    )
    assert tuple(export_record.export_id for export_record in deleted.deleted_exports) == (
        "export_demo",
    )
    assert repository.list_projects_for_user("user_demo") == ()
    with pytest.raises(RecordNotFoundError):
        repository.get_project("user_demo", "project_demo")
    with pytest.raises(RecordNotFoundError):
        repository.get_story("user_demo", "story_demo")
    with pytest.raises(RecordNotFoundError):
        repository.get_import("user_demo", "import_demo")
    with pytest.raises(RecordNotFoundError):
        repository.get_engine_run("user_demo", "run_demo")
    with pytest.raises(RecordNotFoundError):
        repository.get_snapshot("user_demo", "snapshot_demo")
    with pytest.raises(RecordNotFoundError):
        repository.get_export("user_demo", "export_demo")
    with pytest.raises(RecordNotFoundError):
        repository.get_project_settings("user_demo", "project_demo")


def test_json_project_repository_persists_records_across_instances(
    tmp_path: Path,
) -> None:
    """Local JSON persistence should reload records through the same contract."""
    database_path = tmp_path / "project_database.json"
    repository = JsonProjectRepository(database_path)
    repository.create_user(user_record())
    repository.create_project(project_record())
    repository.create_story(story_record())
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())
    repository.store_snapshot(snapshot_record())
    repository.record_export(export_record())
    repository.save_project_settings(
        ProjectSettingsRecord(
            project_id="project_demo",
            default_export_format="json",
            locale="en-US",
        )
    )

    reloaded = JsonProjectRepository(database_path)

    assert reloaded.get_user("user_demo") == user_record()
    assert reloaded.list_projects_for_user("user_demo") == (project_record(),)
    assert reloaded.list_imports_for_story("user_demo", "story_demo") == (import_record(),)
    assert reloaded.get_snapshot("user_demo", "snapshot_demo") == snapshot_record()
    assert reloaded.get_export("user_demo", "export_demo") == export_record()
    assert reloaded.get_project_settings("user_demo", "project_demo").default_export_format == (
        "json"
    )
    assert '"schema_version": "v2_phase_2_001"' in database_path.read_text(
        encoding="utf-8"
    )


def test_postgresql_project_repository_rejects_blank_database_url() -> None:
    """PostgreSQL adapter should fail before attempting a connection with bad config."""
    with pytest.raises(ValueError, match="database URL cannot be blank"):
        PostgresqlProjectRepository("", connect_factory=lambda _: None)


def test_postgresql_project_repository_rejects_non_postgresql_database_url() -> None:
    """PostgreSQL adapter should require an explicit PostgreSQL URL."""
    with pytest.raises(ValueError, match="must use postgresql:// or postgres://"):
        PostgresqlProjectRepository("sqlite:///aevryn.db", connect_factory=lambda _: None)


def test_postgresql_project_repository_normalizes_pasted_database_url() -> None:
    """Production database URLs should survive common copy/paste wrapping."""
    assert postgresql._required_database_url(
        "  'postgres://example.invalid/aevryn'  "
    ) == "postgres://example.invalid/aevryn"


def test_postgresql_project_repository_requires_psycopg_when_no_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PostgreSQL adapter should explain the optional production dependency."""

    def missing_psycopg(module_name: str) -> object:
        if module_name == "psycopg":
            raise ModuleNotFoundError(module_name)
        raise AssertionError(f"Unexpected import: {module_name}")

    monkeypatch.setattr("aevryn.persistence.postgresql.importlib.import_module", missing_psycopg)

    with pytest.raises(PersistenceError, match="psycopg is required"):
        PostgresqlProjectRepository("postgresql://example.invalid/aevryn")


def test_postgresql_default_connection_disables_prepared_statements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production poolers should not receive psycopg prepared statement names."""
    observed: dict[str, object] = {}

    class FakePsycopg:
        """Minimal module exposing connect."""

        @staticmethod
        def connect(database_url: str, **kwargs: object) -> object:
            observed["database_url"] = database_url
            observed.update(kwargs)
            return object()

    def fake_import_module(module_name: str) -> object:
        if module_name == "psycopg":
            return FakePsycopg
        raise AssertionError(f"Unexpected import: {module_name}")

    monkeypatch.setattr("aevryn.persistence.postgresql.importlib.import_module", fake_import_module)

    connect = postgresql._default_connect_factory()
    connect("postgresql://example.invalid/aevryn")

    assert observed == {
        "database_url": "postgresql://example.invalid/aevryn",
        "prepare_threshold": None,
    }


def test_postgresql_jsonb_values_are_wrapped_for_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PostgreSQL JSONB values should be adapted before parameter binding."""

    class FakeJsonb:
        """Minimal stand-in for psycopg.types.json.Jsonb."""

        def __init__(self, value: object) -> None:
            self.value = value

    class FakeJsonModule:
        """Minimal module exposing Jsonb."""

        Jsonb = FakeJsonb

    def fake_import_module(module_name: str) -> object:
        if module_name == "psycopg.types.json":
            return FakeJsonModule
        raise AssertionError(f"Unexpected import: {module_name}")

    monkeypatch.setattr(
        "aevryn.persistence.postgresql.importlib.import_module",
        fake_import_module,
    )

    adapted = postgresql._db_value("serialized_output", '{"accepted_fact_count":2}')

    assert isinstance(adapted, FakeJsonb)
    assert adapted.value == {"accepted_fact_count": 2}


def test_json_project_repository_rolls_back_failed_writes(tmp_path: Path) -> None:
    """Local JSON persistence should not retain memory changes after write failure."""
    blocked_parent = tmp_path / "blocked"
    blocked_parent.write_text("not a directory", encoding="utf-8")
    repository = JsonProjectRepository(blocked_parent / "project_database.json")

    with pytest.raises(OSError):
        repository.create_user(user_record())

    with pytest.raises(RecordNotFoundError, match="Unknown user"):
        repository.get_user("user_demo")


def test_json_project_repository_rejects_malformed_store(tmp_path: Path) -> None:
    """Local JSON persistence should fail clearly on corrupt database files."""
    database_path = tmp_path / "project_database.json"
    database_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(PersistenceError, match="malformed"):
        JsonProjectRepository(database_path)


def test_json_project_repository_rejects_unsupported_schema_version(
    tmp_path: Path,
) -> None:
    """Local JSON persistence should reject unsupported schema versions."""
    database_path = tmp_path / "project_database.json"
    database_path.write_text(
        json.dumps({"schema_version": "old_schema", "users": []}),
        encoding="utf-8",
    )

    with pytest.raises(PersistenceError, match="schema version is unsupported"):
        JsonProjectRepository(database_path)


def test_json_project_repository_rejects_non_object_payload(tmp_path: Path) -> None:
    """Local JSON persistence should require an object root."""
    database_path = tmp_path / "project_database.json"
    database_path.write_text("[]", encoding="utf-8")

    with pytest.raises(PersistenceError, match="root must be an object"):
        JsonProjectRepository(database_path)


def test_json_project_repository_rejects_missing_sections(tmp_path: Path) -> None:
    """Local JSON persistence should reject partial database files."""
    database_path = tmp_path / "project_database.json"
    database_path.write_text(
        json.dumps({"schema_version": "v2_phase_2_001", "users": []}),
        encoding="utf-8",
    )

    with pytest.raises(PersistenceError, match="missing required sections"):
        JsonProjectRepository(database_path)


def test_json_project_repository_rejects_unknown_sections(tmp_path: Path) -> None:
    """Local JSON persistence should reject unexpected top-level sections."""
    database_path = tmp_path / "project_database.json"
    repository = JsonProjectRepository(database_path)
    repository.create_user(user_record())
    payload = json.loads(database_path.read_text(encoding="utf-8"))
    payload["surprise"] = []
    database_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PersistenceError, match="unknown sections"):
        JsonProjectRepository(database_path)


def test_json_project_repository_rejects_invalid_sections(tmp_path: Path) -> None:
    """Local JSON persistence should reject malformed record sections."""
    database_path = tmp_path / "project_database.json"
    database_path.write_text(
        json.dumps(
            {
                "schema_version": "v2_phase_2_001",
                "users": {},
                "projects": [],
                "stories": [],
                "imports": [],
                "engine_runs": [],
                "snapshots": [],
                "exports": [],
                "project_settings": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(PersistenceError, match="section is invalid"):
        JsonProjectRepository(database_path)


def test_json_project_repository_writes_deterministic_payloads(tmp_path: Path) -> None:
    """Local JSON persistence should produce byte-stable equivalent payloads."""
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    for database_path in (first_path, second_path):
        repository = JsonProjectRepository(database_path)
        repository.create_user(user_record())
        repository.create_project(project_record())
        repository.create_story(story_record())
        repository.record_import(import_record())
        repository.record_engine_run(engine_run_record())
        repository.store_snapshot(snapshot_record())

    assert first_path.read_bytes() == second_path.read_bytes()


def test_json_project_repository_rejects_duplicate_loaded_emails(tmp_path: Path) -> None:
    """Local JSON persistence should reject duplicate emails on reload."""
    database_path = tmp_path / "project_database.json"
    repository = JsonProjectRepository(database_path)
    repository.create_user(user_record())

    payload = json.loads(database_path.read_text(encoding="utf-8"))
    payload["users"].append(
        {
            "user_id": "user_other",
            "email": "DEMO@example.com",
            "display_name": "Other User",
            "created_at": NOW,
        }
    )
    database_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PersistenceError, match="duplicate user email"):
        JsonProjectRepository(database_path)


def test_json_project_repository_rejects_broken_relationships(tmp_path: Path) -> None:
    """Local JSON persistence should reject corrupted ownership graphs."""
    database_path = tmp_path / "project_database.json"
    repository = JsonProjectRepository(database_path)
    repository.create_user(user_record())
    repository.create_project(project_record())
    repository.create_story(story_record())
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())

    payload = json.loads(database_path.read_text(encoding="utf-8"))
    payload["imports"][0]["story_id"] = "story_missing"
    database_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PersistenceError, match="relationships are invalid"):
        JsonProjectRepository(database_path)


def test_project_database_rejects_duplicate_records() -> None:
    """Repository should fail clearly on duplicate identities."""
    repository = InMemoryProjectRepository()
    repository.create_user(user_record())

    with pytest.raises(DuplicateRecordError, match="Duplicate user"):
        repository.create_user(user_record())


def test_project_database_models_reject_email_whitespace() -> None:
    """User emails should be stable values without hidden whitespace."""
    with pytest.raises(ValueError, match="cannot contain whitespace"):
        UserRecord(
            user_id="user_demo",
            email="demo @example.com",
            display_name="Demo User",
            created_at=NOW,
        )


def test_project_database_rejects_case_insensitive_duplicate_user_email() -> None:
    """User email uniqueness should not depend on letter casing."""
    repository = InMemoryProjectRepository()
    repository.create_user(user_record())

    with pytest.raises(DuplicateRecordError, match="Duplicate user email"):
        repository.create_user(
            UserRecord(
                user_id="user_other",
                email="DEMO@example.com",
                display_name="Other User",
                created_at=NOW,
            )
        )


def test_project_database_rejects_duplicate_user_email() -> None:
    """Repository should enforce the schema's unique user email contract."""
    repository = InMemoryProjectRepository()
    repository.create_user(user_record())

    with pytest.raises(DuplicateRecordError, match="Duplicate user email"):
        repository.create_user(
            UserRecord(
                user_id="user_other",
                email="demo@example.com",
                display_name="Other User",
                created_at=NOW,
            )
        )


def test_project_database_rejects_missing_parent_records() -> None:
    """Repository should not create child records without required parents."""
    repository = InMemoryProjectRepository()

    with pytest.raises(RecordNotFoundError, match="Unknown user"):
        repository.create_project(project_record())


def test_project_database_enforces_project_ownership() -> None:
    """Repository should not return projects across user boundaries."""
    repository = seeded_repository()
    repository.create_user(
        UserRecord(
            user_id="user_other",
            email="other@example.com",
            display_name="Other User",
            created_at=NOW,
        )
    )

    with pytest.raises(AccessDeniedError, match="not owned"):
        repository.get_project("user_other", "project_demo")

    with pytest.raises(AccessDeniedError, match="not owned"):
        repository.get_story("user_other", "story_demo")


def test_project_database_rejects_cross_user_import_and_run_lists() -> None:
    """Import and run reads should stay inside project ownership."""
    repository = seeded_repository()
    repository.create_user(
        UserRecord(
            user_id="user_other",
            email="other@example.com",
            display_name="Other User",
            created_at=NOW,
        )
    )
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())

    with pytest.raises(AccessDeniedError, match="not owned"):
        repository.get_import("user_other", "import_demo")

    with pytest.raises(AccessDeniedError, match="not owned"):
        repository.list_engine_runs_for_project("user_other", "project_demo")


def test_project_database_updates_engine_run_status_without_changing_scope() -> None:
    """Repository should update run status while preserving run ownership."""
    repository = seeded_repository()
    repository.record_import(import_record())
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            status="pending",
            engine_version="0.1.0",
            started_at=NOW,
        )
    )

    repository.update_engine_run(engine_run_record())

    assert repository.get_engine_run("user_demo", "run_demo").status == "succeeded"


def test_project_database_rejects_engine_run_import_from_other_story() -> None:
    """Engine runs should only process imports from the same story."""
    repository = seeded_repository()
    repository.create_story(
        StoryRecord(
            story_id="story_other",
            project_id="project_demo",
            title="Other Story",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    repository.record_import(import_record(import_id="import_other", story_id="story_other"))

    with pytest.raises(ValueError, match="same story"):
        repository.record_engine_run(
            EngineRunRecord(
                run_id="run_demo",
                project_id="project_demo",
                story_id="story_demo",
                import_id="import_other",
                status="succeeded",
                engine_version="0.1.0",
                started_at=NOW,
                finished_at=NOW,
            )
        )


def test_project_database_rejects_invalid_engine_run_status_transition() -> None:
    """Engine run status updates should move forward only."""
    repository = seeded_repository()
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())

    with pytest.raises(ValueError, match="status transition is invalid"):
        repository.update_engine_run(
            EngineRunRecord(
                run_id="run_demo",
                project_id="project_demo",
                story_id="story_demo",
                import_id="import_demo",
                status="running",
                engine_version="0.1.0",
                started_at=NOW,
                status_updated_at=NOW,
            )
        )


def test_project_database_rejects_engine_run_scope_changes() -> None:
    """Engine run updates should not move runs between stories or projects."""
    repository = seeded_repository()
    repository.record_import(import_record())
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            status="pending",
            engine_version="0.1.0",
            started_at=NOW,
        )
    )

    with pytest.raises(ValueError, match="cannot change run scope"):
        repository.update_engine_run(
            EngineRunRecord(
                run_id="run_demo",
                project_id="project_other",
                story_id="story_demo",
                import_id="import_demo",
                status="failed",
                engine_version="0.1.0",
                started_at=NOW,
                finished_at=NOW,
                error_summary="Project mismatch.",
            )
        )


def test_project_database_rejects_impossible_engine_run_timestamp_order() -> None:
    """Engine run timestamps should not move backward."""
    with pytest.raises(ValueError, match="finished_at cannot be before started_at"):
        EngineRunRecord(
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            status="succeeded",
            engine_version="0.1.0",
            started_at="2026-06-27T01:00:00Z",
            finished_at="2026-06-27T00:00:00Z",
        )


def test_project_database_rejects_invalid_engine_run_lifecycle() -> None:
    """Engine run records should reject impossible lifecycle states."""
    with pytest.raises(ValueError, match="Completed engine runs require"):
        EngineRunRecord(
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            status="succeeded",
            engine_version="0.1.0",
            started_at=NOW,
        )

    with pytest.raises(ValueError, match="Failed engine runs require"):
        EngineRunRecord(
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            status="failed",
            engine_version="0.1.0",
            started_at=NOW,
            finished_at=NOW,
        )

    with pytest.raises(ValueError, match="Active engine runs cannot"):
        EngineRunRecord(
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            status="running",
            engine_version="0.1.0",
            started_at=NOW,
            finished_at=NOW,
        )


def test_project_database_rejects_export_kind_mismatches() -> None:
    """Exports should describe the snapshot kind they serialize."""
    repository = seeded_repository()
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())
    repository.store_snapshot(snapshot_record())

    with pytest.raises(ValueError, match="Export kind must match"):
        repository.record_export(
            ExportRecord(
                export_id="export_demo",
                project_id="project_demo",
                snapshot_id="snapshot_demo",
                export_kind="world_state",
                export_format="markdown",
                filename="world.md",
                content_type="text/markdown; charset=utf-8",
                storage_ref="storage://exports/world.md",
                created_at=NOW,
            )
        )


def test_project_database_rejects_cross_user_snapshot_and_export_reads() -> None:
    """Snapshot and export reads should stay inside project ownership."""
    repository = seeded_repository()
    repository.create_user(
        UserRecord(
            user_id="user_other",
            email="other@example.com",
            display_name="Other User",
            created_at=NOW,
        )
    )
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())
    repository.store_snapshot(snapshot_record())
    repository.record_export(export_record())

    with pytest.raises(AccessDeniedError, match="not owned"):
        repository.get_snapshot("user_other", "snapshot_demo")

    with pytest.raises(AccessDeniedError, match="not owned"):
        repository.get_export("user_other", "export_demo")


def test_project_database_snapshots_are_append_only() -> None:
    """Snapshots should be immutable records rather than overwritten outputs."""
    repository = seeded_repository()
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())
    repository.store_snapshot(snapshot_record(snapshot_id="snapshot_001"))
    repository.store_snapshot(snapshot_record(snapshot_id="snapshot_002"))

    snapshots = repository.list_snapshots_for_project("user_demo", "project_demo")

    assert [snapshot.snapshot_id for snapshot in snapshots] == [
        "snapshot_001",
        "snapshot_002",
    ]


def test_project_database_lists_story_snapshots_with_kind_filter() -> None:
    """Story snapshot reads should support deterministic kind filtering."""
    repository = seeded_repository()
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())
    repository.store_snapshot(
        snapshot_record(snapshot_id="snapshot_character", snapshot_kind="character_profile")
    )
    repository.store_snapshot(
        snapshot_record(snapshot_id="snapshot_world", snapshot_kind="world_state")
    )

    all_snapshots = repository.list_snapshots_for_story("user_demo", "story_demo")
    character_snapshots = repository.list_snapshots_for_story(
        "user_demo",
        "story_demo",
        snapshot_kind="character_profile",
    )

    assert [snapshot.snapshot_id for snapshot in all_snapshots] == [
        "snapshot_character",
        "snapshot_world",
    ]
    assert character_snapshots == (
        snapshot_record(
            snapshot_id="snapshot_character",
            snapshot_kind="character_profile",
        ),
    )


def test_project_database_rejects_cross_user_story_snapshot_lists() -> None:
    """Story-scoped snapshot reads should enforce project ownership."""
    repository = seeded_repository()
    repository.create_user(
        UserRecord(
            user_id="user_other",
            email="other@example.com",
            display_name="Other User",
            created_at=NOW,
        )
    )

    with pytest.raises(AccessDeniedError, match="not owned"):
        repository.list_snapshots_for_story("user_other", "story_demo")

def test_project_database_rejects_snapshot_for_incomplete_run() -> None:
    """Snapshots should only be stored for successful engine runs."""
    repository = seeded_repository()
    repository.record_import(import_record())
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_demo",
            project_id="project_demo",
            story_id="story_demo",
            import_id="import_demo",
            status="running",
            engine_version="0.1.0",
            started_at=NOW,
        )
    )

    with pytest.raises(ValueError, match="succeeded engine runs"):
        repository.store_snapshot(snapshot_record())


def test_project_database_rejects_snapshot_for_wrong_run_scope() -> None:
    """Snapshots must belong to their run's project and story."""
    repository = seeded_repository()
    repository.create_story(
        StoryRecord(
            story_id="story_other",
            project_id="project_demo",
            title="Other Story",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    repository.record_import(import_record())
    repository.record_engine_run(engine_run_record())

    with pytest.raises(ValueError, match="same project and story"):
        repository.store_snapshot(snapshot_record(story_id="story_other"))


def test_project_database_rejects_invalid_json_snapshots() -> None:
    """JSON snapshots should contain valid serialized JSON."""
    with pytest.raises(ValueError, match="valid JSON"):
        SnapshotRecord(
            snapshot_id="snapshot_demo",
            project_id="project_demo",
            story_id="story_demo",
            run_id="run_demo",
            snapshot_kind="character_profile",
            content_type="application/json",
            serialized_output="not json",
            created_at=NOW,
        )


def test_project_database_models_reject_invalid_audit_timestamps() -> None:
    """Persistence records should use stable audit timestamp strings."""
    with pytest.raises(ValueError, match="ISO UTC timestamp"):
        UserRecord(
            user_id="user_demo",
            email="demo@example.com",
            display_name="Demo User",
            created_at="today",
        )


def test_project_database_models_reject_invalid_calendar_timestamps() -> None:
    """Persistence timestamps should parse as real UTC instants."""
    with pytest.raises(ValueError, match="ISO UTC timestamp"):
        UserRecord(
            user_id="user_demo",
            email="demo@example.com",
            display_name="Demo User",
            created_at="2026-99-99T00:00:00Z",
        )


def test_project_database_models_reject_path_like_filenames() -> None:
    """Filename metadata should not smuggle filesystem paths."""
    with pytest.raises(ValueError, match="path separators"):
        ImportRecord(
            import_id="import_demo",
            story_id="story_demo",
            source_id="source_demo",
            filename="chapters/chapter.txt",
            source_format="txt",
            storage_ref="storage://imports/source_demo/chapter.txt",
            chapter_count=1,
            scene_count=1,
            evidence_anchor_count=1,
            created_at=NOW,
        )


def test_project_database_models_require_explicit_storage_ref_scheme() -> None:
    """Storage references should use scheme://path notation."""
    with pytest.raises(ValueError, match="scheme://path"):
        ExportRecord(
            export_id="export_demo",
            project_id="project_demo",
            snapshot_id="snapshot_demo",
            export_kind="character_profile",
            export_format="markdown",
            filename="character_mark.md",
            content_type="text/markdown; charset=utf-8",
            storage_ref="exports/character_mark.md",
            created_at=NOW,
        )


def test_project_database_models_reject_invalid_storage_ref_schemes() -> None:
    """Storage reference schemes should be stable machine tokens."""
    with pytest.raises(ValueError, match="machine-readable token"):
        ExportRecord(
            export_id="export_demo",
            project_id="project_demo",
            snapshot_id="snapshot_demo",
            export_kind="character_profile",
            export_format="markdown",
            filename="character_mark.md",
            content_type="text/markdown; charset=utf-8",
            storage_ref="bad-scheme://exports/character_mark.md",
            created_at=NOW,
        )


def test_project_database_models_reject_storage_ref_traversal() -> None:
    """Storage references should not contain parent-directory traversal."""
    with pytest.raises(ValueError, match="parent-directory traversal"):
        ExportRecord(
            export_id="export_demo",
            project_id="project_demo",
            snapshot_id="snapshot_demo",
            export_kind="character_profile",
            export_format="markdown",
            filename="character_mark.md",
            content_type="text/markdown; charset=utf-8",
            storage_ref="storage://exports/../character_mark.md",
            created_at=NOW,
        )


def test_project_database_models_reject_file_bytes_as_storage_refs() -> None:
    """Structured records should store references, not raw or whitespace file data."""
    with pytest.raises(ValueError, match="storage reference"):
        ImportRecord(
            import_id="import_demo",
            story_id="story_demo",
            source_id="source_demo",
            filename="chapter.txt",
            source_format="txt",
            storage_ref="raw file text is not a storage ref",
            chapter_count=1,
            scene_count=1,
            evidence_anchor_count=1,
            created_at=NOW,
        )


def seeded_repository() -> InMemoryProjectRepository:
    """Return a repository with user, project, and story parents."""
    repository = InMemoryProjectRepository()
    repository.create_user(user_record())
    repository.create_project(project_record())
    repository.create_story(story_record())
    return repository


def user_record() -> UserRecord:
    """Return a stable user record."""
    return UserRecord(
        user_id="user_demo",
        email="demo@example.com",
        display_name="Demo User",
        created_at=NOW,
    )


def project_record() -> ProjectRecord:
    """Return a stable project record."""
    return ProjectRecord(
        project_id="project_demo",
        owner_user_id="user_demo",
        name="Demo Project",
        created_at=NOW,
        updated_at=NOW,
    )


def story_record() -> StoryRecord:
    """Return a stable story record."""
    return StoryRecord(
        story_id="story_demo",
        project_id="project_demo",
        title="Demo Story",
        created_at=NOW,
        updated_at=NOW,
    )


def import_record(
    import_id: str = "import_demo",
    story_id: str = "story_demo",
) -> ImportRecord:
    """Return a stable import record."""
    return ImportRecord(
        import_id=import_id,
        story_id=story_id,
        source_id="source_demo",
        filename="chapter.txt",
        source_format="txt",
        storage_ref="storage://imports/source_demo/chapter.txt",
        chapter_count=1,
        scene_count=1,
        evidence_anchor_count=1,
        created_at=NOW,
    )


def engine_run_record() -> EngineRunRecord:
    """Return a stable engine run record."""
    return EngineRunRecord(
        run_id="run_demo",
        project_id="project_demo",
        story_id="story_demo",
        import_id="import_demo",
        status="succeeded",
        engine_version="0.1.0",
        started_at=NOW,
        finished_at=NOW,
    )


def snapshot_record(
    snapshot_id: str = "snapshot_demo",
    story_id: str = "story_demo",
    snapshot_kind: SnapshotKind = "character_profile",
) -> SnapshotRecord:
    """Return a stable snapshot record."""
    return SnapshotRecord(
        snapshot_id=snapshot_id,
        project_id="project_demo",
        story_id=story_id,
        run_id="run_demo",
        snapshot_kind=snapshot_kind,
        content_type="application/json",
        serialized_output='{"character_id":"character_mark"}',
        created_at=NOW,
    )


def export_record() -> ExportRecord:
    """Return a stable export record."""
    return ExportRecord(
        export_id="export_demo",
        project_id="project_demo",
        snapshot_id="snapshot_demo",
        export_kind="character_profile",
        export_format="markdown",
        filename="character_mark.md",
        content_type="text/markdown; charset=utf-8",
        storage_ref="storage://exports/character_mark.md",
        created_at=NOW,
    )

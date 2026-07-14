"""Tests for the Phase 11 audit ledger."""

from __future__ import annotations

from dataclasses import replace

import pytest

from aevryn.audit import AuditLedger, AuditLedgerIntegrityError, PostgresqlAuditLedger
from aevryn.audit import postgresql as audit_postgresql
from aevryn.persistence.repository import PersistenceError

NOW = "2026-06-29T00:00:00Z"


def test_audit_ledger_appends_hash_chained_metadata_records() -> None:
    """Audit records should be append-only and tamper evident."""
    ledger = AuditLedger()

    created = ledger.append(
        event_type="project_created",
        occurred_at=NOW,
        actor_id="user_alpha",
        project_id="project_alpha",
        summary="Project created.",
        metadata={"project_count": "1"},
    )
    deleted = ledger.append(
        event_type="story_deleted",
        occurred_at="2026-06-29T00:05:00Z",
        actor_id="user_alpha",
        project_id="project_alpha",
        story_id="story_alpha",
        summary="Story deleted.",
        metadata={"import_count": "2", "snapshot_count": "1"},
    )

    ledger.verify()
    assert created.sequence == 1
    assert deleted.sequence == 2
    assert deleted.previous_hash == created.record_hash
    assert len(created.record_hash) == 64
    assert tuple(record.event_type for record in ledger.records()) == (
        "project_created",
        "story_deleted",
    )


def test_audit_ledger_rejects_tampered_records() -> None:
    """Hash verification should fail if a persisted record is changed."""
    ledger = AuditLedger()
    record = ledger.append(
        event_type="import_saved",
        occurred_at=NOW,
        actor_id="user_alpha",
        project_id="project_alpha",
        story_id="story_alpha",
        summary="Import metadata saved.",
        metadata={"source_format": "txt"},
    )
    tampered = replace(record, summary="Import metadata changed.")

    with pytest.raises(AuditLedgerIntegrityError, match="record hash"):
        AuditLedger((tampered,))


def test_audit_ledger_rejects_reordered_records() -> None:
    """Hash verification should detect reordered records."""
    ledger = AuditLedger()
    first = ledger.append(
        event_type="import_saved",
        occurred_at=NOW,
        actor_id="user_alpha",
        project_id="project_alpha",
        story_id="story_alpha",
        summary="Import metadata saved.",
    )
    second = ledger.append(
        event_type="run_submitted",
        occurred_at="2026-06-29T00:01:00Z",
        actor_id="user_alpha",
        project_id="project_alpha",
        story_id="story_alpha",
        summary="Run submitted.",
    )

    with pytest.raises(AuditLedgerIntegrityError, match="sequence"):
        AuditLedger((second, first))


def test_audit_ledger_rejects_sensitive_payload_metadata() -> None:
    """Audit records should not become hidden copies of deleted manuscripts."""
    ledger = AuditLedger()

    sensitive_metadata = (
        {"source_text": "Mark carried the private dagger."},
        {"serialized_output": "{}"},
        {"api_key": "sk-aevryn-test-secret"},
        {"diagnostic": "C:\\Users\\creator\\private_story.txt"},
    )
    for metadata in sensitive_metadata:
        with pytest.raises(ValueError):
            ledger.append(
                event_type="story_deleted",
                occurred_at=NOW,
                actor_id="user_alpha",
                project_id="project_alpha",
                story_id="story_alpha",
                summary="Story deleted.",
                metadata=metadata,
            )


def test_audit_ledger_rejects_non_concise_summaries() -> None:
    """Audit summaries should remain concise metadata, not prose dumps."""
    ledger = AuditLedger()

    with pytest.raises(ValueError, match="single line"):
        ledger.append(
            event_type="worker_failed",
            occurred_at=NOW,
            summary="Failure summary.\nFull chapter text follows.",
        )
    with pytest.raises(ValueError, match="concise"):
        ledger.append(
            event_type="worker_failed",
            occurred_at=NOW,
            summary="x" * 200,
        )


def test_postgresql_audit_ledger_rejects_blank_database_url() -> None:
    """PostgreSQL audit storage should fail before connecting with bad config."""
    with pytest.raises(ValueError, match="database URL cannot be blank"):
        PostgresqlAuditLedger("", connect_factory=lambda _: None)


def test_postgresql_audit_ledger_rejects_non_postgresql_database_url() -> None:
    """PostgreSQL audit storage should require an explicit PostgreSQL URL."""
    with pytest.raises(ValueError, match="must use postgresql:// or postgres://"):
        PostgresqlAuditLedger("sqlite:///aevryn.db", connect_factory=lambda _: None)


def test_postgresql_audit_ledger_requires_psycopg_when_no_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PostgreSQL audit storage should explain the optional dependency."""

    def missing_psycopg(module_name: str) -> object:
        if module_name == "psycopg":
            raise ModuleNotFoundError(module_name)
        raise AssertionError(f"Unexpected import: {module_name}")

    monkeypatch.setattr("aevryn.audit.postgresql.importlib.import_module", missing_psycopg)

    with pytest.raises(PersistenceError, match="psycopg is required"):
        PostgresqlAuditLedger("postgresql://example.invalid/aevryn")


def test_postgresql_audit_ledger_default_connection_disables_prepared_statements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Transaction poolers should not receive psycopg prepared statement names."""
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

    monkeypatch.setattr("aevryn.audit.postgresql.importlib.import_module", fake_import_module)

    connect = audit_postgresql._default_connect_factory()
    connect("postgresql://example.invalid/aevryn")

    assert observed == {
        "database_url": "postgresql://example.invalid/aevryn",
        "prepare_threshold": None,
    }


def test_postgresql_audit_ledger_appends_and_reloads_hash_chained_records() -> None:
    """PostgreSQL audit storage should persist the same verified ledger contract."""
    connection = FakeAuditConnection()
    ledger = PostgresqlAuditLedger(
        "postgresql://example.invalid/aevryn",
        connect_factory=lambda _: connection,
    )

    created = ledger.append(
        event_type="project_created",
        occurred_at=NOW,
        actor_id="user_alpha",
        project_id="project_alpha",
        summary="Project created.",
        metadata={"project_count": "1"},
    )
    deleted = ledger.append(
        event_type="story_deleted",
        occurred_at="2026-06-29T00:05:00Z",
        actor_id="user_alpha",
        project_id="project_alpha",
        story_id="story_alpha",
        summary="Story deleted.",
        metadata={"import_count": "2"},
    )

    reloaded = PostgresqlAuditLedger(
        "postgresql://example.invalid/aevryn",
        connect_factory=lambda _: connection,
        bootstrap_schema=False,
    )

    assert connection.commits == 3
    assert tuple(record.event_type for record in reloaded.records()) == (
        "project_created",
        "story_deleted",
    )
    assert deleted.sequence == 2
    assert deleted.previous_hash == created.record_hash
    reloaded.verify()


def test_postgresql_audit_ledger_rolls_back_sensitive_metadata() -> None:
    """Rejected audit metadata should not insert hidden source payloads."""
    connection = FakeAuditConnection()
    ledger = PostgresqlAuditLedger(
        "postgresql://example.invalid/aevryn",
        connect_factory=lambda _: connection,
    )

    with pytest.raises(ValueError, match="sensitive payloads"):
        ledger.append(
            event_type="story_deleted",
            occurred_at=NOW,
            actor_id="user_alpha",
            project_id="project_alpha",
            story_id="story_alpha",
            summary="Story deleted.",
            metadata={"source_text": "Private manuscript text."},
        )

    assert connection.records == []
    assert connection.rollbacks == 1


def test_postgresql_audit_ledger_detects_tampered_persisted_rows() -> None:
    """Persisted audit rows should fail closed when the hash chain is invalid."""
    connection = FakeAuditConnection()
    ledger = PostgresqlAuditLedger(
        "postgresql://example.invalid/aevryn",
        connect_factory=lambda _: connection,
    )
    ledger.append(
        event_type="import_saved",
        occurred_at=NOW,
        actor_id="user_alpha",
        project_id="project_alpha",
        story_id="story_alpha",
        summary="Import metadata saved.",
    )
    row = connection.records[0]
    connection.records[0] = (*row[:3], "Import metadata changed.", *row[4:])

    with pytest.raises(AuditLedgerIntegrityError, match="record hash"):
        PostgresqlAuditLedger(
            "postgresql://example.invalid/aevryn",
            connect_factory=lambda _: connection,
            bootstrap_schema=False,
        )


class FakeAuditConnection:
    """Minimal connection test double for audit ledger SQL."""

    def __init__(self) -> None:
        self.records: list[tuple[object, ...]] = []
        self.commits = 0
        self.rollbacks = 0
        self.lock_count = 0

    def __enter__(self) -> FakeAuditConnection:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def cursor(self) -> FakeAuditCursor:
        return FakeAuditCursor(self)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeAuditCursor:
    """Minimal cursor test double for audit ledger SQL."""

    def __init__(self, connection: FakeAuditConnection) -> None:
        self.connection = connection
        self._fetchone: tuple[object, ...] | None = None
        self._fetchall: list[tuple[object, ...]] = []

    def __enter__(self) -> FakeAuditCursor:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, statement: str, params: tuple[object, ...] = ()) -> None:
        normalized = " ".join(statement.lower().split())
        if normalized.startswith("create table") or normalized.startswith("create index"):
            return
        if normalized.startswith("lock table audit_ledger_records"):
            self.connection.lock_count += 1
            return
        if "from audit_ledger_records order by sequence desc" in normalized:
            self._fetchone = self.connection.records[-1] if self.connection.records else None
            return
        if normalized.startswith("insert into audit_ledger_records"):
            stored = list(params)
            stored[7] = _jsonb_value(stored[7])
            self.connection.records.append(tuple(stored))
            return
        if "from audit_ledger_records order by sequence" in normalized:
            self._fetchall = list(self.connection.records)
            return
        raise AssertionError(f"Unexpected SQL: {statement}")

    def fetchone(self) -> tuple[object, ...] | None:
        return self._fetchone

    def fetchall(self) -> list[tuple[object, ...]]:
        return self._fetchall


def _jsonb_value(value: object) -> object:
    """Return the wrapped JSON value from psycopg Jsonb test parameters."""
    for attribute_name in ("obj", "value"):
        if hasattr(value, attribute_name):
            return getattr(value, attribute_name)
    return value

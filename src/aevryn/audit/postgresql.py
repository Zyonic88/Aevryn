"""PostgreSQL-backed audit ledger adapter."""

from __future__ import annotations

import importlib
import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any, cast

from aevryn.audit.ledger import (
    AuditLedger,
    AuditLedgerIntegrityError,
    AuditLedgerRecord,
)
from aevryn.persistence.repository import PersistenceError

ConnectFactory = Callable[[str], Any]


class PostgresqlAuditLedger:
    """Durable append-only audit ledger backed by PostgreSQL."""

    def __init__(
        self,
        database_url: str,
        *,
        connect_factory: ConnectFactory | None = None,
        bootstrap_schema: bool = True,
    ) -> None:
        """Create a PostgreSQL audit ledger adapter."""
        self._database_url = _required_database_url(database_url)
        self._connect_factory = connect_factory or _default_connect_factory()
        if bootstrap_schema:
            self.bootstrap_schema()
        self.verify()

    def bootstrap_schema(self) -> None:
        """Create missing audit ledger tables and indexes."""
        with self._connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS audit_ledger_records (
                            sequence integer PRIMARY KEY,
                            event_type text NOT NULL,
                            occurred_at timestamptz NOT NULL,
                            summary text NOT NULL,
                            actor_id text NOT NULL DEFAULT '',
                            project_id text NOT NULL DEFAULT '',
                            story_id text NOT NULL DEFAULT '',
                            metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
                            previous_hash text NOT NULL,
                            record_hash text NOT NULL UNIQUE,
                            inserted_at timestamptz NOT NULL DEFAULT now(),
                            CONSTRAINT audit_ledger_sequence_positive
                                CHECK (sequence > 0),
                            CONSTRAINT audit_ledger_previous_hash_format
                                CHECK (previous_hash ~ '^[0-9a-f]{64}$'),
                            CONSTRAINT audit_ledger_record_hash_format
                                CHECK (record_hash ~ '^[0-9a-f]{64}$')
                        );
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX IF NOT EXISTS audit_ledger_event_type_idx
                            ON audit_ledger_records (event_type);
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX IF NOT EXISTS audit_ledger_project_id_idx
                            ON audit_ledger_records (project_id);
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX IF NOT EXISTS audit_ledger_story_id_idx
                            ON audit_ledger_records (story_id);
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX IF NOT EXISTS audit_ledger_occurred_at_idx
                            ON audit_ledger_records (occurred_at);
                        """
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def append(
        self,
        *,
        event_type: str,
        occurred_at: str,
        summary: str,
        actor_id: str = "",
        project_id: str = "",
        story_id: str = "",
        metadata: Mapping[str, str] | None = None,
    ) -> AuditLedgerRecord:
        """Append one metadata-only record in a locked transaction."""
        with self._connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("LOCK TABLE audit_ledger_records IN EXCLUSIVE MODE;")
                    cursor.execute(
                        """
                        SELECT
                            sequence,
                            event_type,
                            occurred_at,
                            summary,
                            actor_id,
                            project_id,
                            story_id,
                            metadata,
                            previous_hash,
                            record_hash
                        FROM audit_ledger_records
                        ORDER BY sequence DESC
                        LIMIT 1;
                        """
                    )
                    latest = cursor.fetchone()
                    previous_hash = (
                        str(latest[9])
                        if latest is not None
                        else "0" * 64
                    )
                    sequence = (_row_sequence(latest[0]) + 1) if latest is not None else 1
                    record = AuditLedgerRecord(
                        sequence=sequence,
                        event_type=event_type,
                        occurred_at=occurred_at,
                        summary=summary,
                        actor_id=actor_id,
                        project_id=project_id,
                        story_id=story_id,
                        metadata=metadata or {},
                        previous_hash=previous_hash,
                    ).with_hash()
                    cursor.execute(
                        """
                        INSERT INTO audit_ledger_records (
                            sequence,
                            event_type,
                            occurred_at,
                            summary,
                            actor_id,
                            project_id,
                            story_id,
                            metadata,
                            previous_hash,
                            record_hash
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """,
                        _record_values(record),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return record

    def records(self) -> tuple[AuditLedgerRecord, ...]:
        """Return all persisted audit records in append order."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        sequence,
                        event_type,
                        occurred_at,
                        summary,
                        actor_id,
                        project_id,
                        story_id,
                        metadata,
                        previous_hash,
                        record_hash
                    FROM audit_ledger_records
                    ORDER BY sequence;
                    """
                )
                rows = cursor.fetchall()
        return tuple(_record_from_row(row) for row in rows)

    def verify(self) -> None:
        """Verify persisted sequence and hash-chain integrity."""
        try:
            AuditLedger(self.records()).verify()
        except AuditLedgerIntegrityError:
            raise
        except Exception as error:
            raise PersistenceError("PostgreSQL audit ledger verification failed.") from error

    def _connect(self) -> Any:
        """Return a new PostgreSQL connection."""
        return self._connect_factory(self._database_url)


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
            "psycopg is required for the PostgreSQL audit ledger adapter. "
            "Install the Aevryn postgresql optional dependencies."
        ) from error

    def connect(database_url: str) -> Any:
        return psycopg.connect(database_url, prepare_threshold=None)

    return cast(ConnectFactory, connect)


def _record_values(record: AuditLedgerRecord) -> tuple[object, ...]:
    """Return PostgreSQL parameter values for one audit record."""
    return (
        record.sequence,
        record.event_type,
        record.occurred_at,
        record.summary,
        record.actor_id,
        record.project_id,
        record.story_id,
        _postgresql_jsonb(dict(record.metadata)),
        record.previous_hash,
        record.record_hash,
    )


def _record_from_row(row: tuple[object, ...]) -> AuditLedgerRecord:
    """Return an audit record from one PostgreSQL row."""
    metadata = row[7]
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    if not isinstance(metadata, Mapping):
        raise PersistenceError("PostgreSQL audit metadata must be an object.")
    return AuditLedgerRecord(
        sequence=_row_sequence(row[0]),
        event_type=str(row[1]),
        occurred_at=_timestamp_to_utc_string(row[2]),
        summary=str(row[3]),
        actor_id=str(row[4]),
        project_id=str(row[5]),
        story_id=str(row[6]),
        metadata={str(key): str(value) for key, value in metadata.items()},
        previous_hash=str(row[8]),
        record_hash=str(row[9]),
    )


def _timestamp_to_utc_string(value: object) -> str:
    """Return persisted timestamp values as canonical UTC strings."""
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return str(value)


def _row_sequence(value: object) -> int:
    """Return a PostgreSQL sequence value as a strict integer."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise PersistenceError("PostgreSQL audit sequence must be an integer.")
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

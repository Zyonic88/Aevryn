"""Deterministic JSON authentication store for local platform runs."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any, TypeVar

from aevryn.auth.stores import (
    CredentialRecord,
    InMemoryCredentialStore,
    InMemorySessionStore,
    PasswordResetRecord,
    SessionRecord,
)
from aevryn.persistence import PersistenceError

AUTH_STORE_SCHEMA_VERSION = "aevryn_auth_store_v1"

T = TypeVar("T")


class JsonAuthenticationStore(InMemoryCredentialStore, InMemorySessionStore):
    """Persist local authentication records to deterministic JSON.

    This adapter stores password hashes, session token hashes, and reset token
    hashes for local platform development. It does not store plaintext secrets.
    """

    def __init__(self, store_path: Path) -> None:
        """Open a local authentication store file, creating it on first write."""
        InMemoryCredentialStore.__init__(self)
        InMemorySessionStore.__init__(self)
        self._store_path = store_path
        self._load()

    def create_credential(self, credential: CredentialRecord) -> None:
        """Store a new credential record and flush the local store."""
        self._commit(lambda: InMemoryCredentialStore.create_credential(self, credential))

    def delete_credential_for_auth_rollback(self, user_id: str) -> None:
        """Delete rollback credentials and flush the local store."""
        self._commit(
            lambda: InMemoryCredentialStore.delete_credential_for_auth_rollback(
                self,
                user_id,
            )
        )

    def update_password_hash(
        self,
        user_id: str,
        password_hash: str,
        updated_at: str,
    ) -> None:
        """Replace a password hash and flush the local store."""
        self._commit(
            lambda: InMemoryCredentialStore.update_password_hash(
                self,
                user_id,
                password_hash,
                updated_at,
            )
        )

    def create_session(self, session: SessionRecord) -> None:
        """Store a new session record and flush the local store."""
        self._commit(lambda: InMemorySessionStore.create_session(self, session))

    def create_password_reset(self, reset: PasswordResetRecord) -> None:
        """Store a password reset record and flush the local store."""
        self._commit(lambda: InMemorySessionStore.create_password_reset(self, reset))

    def consume_password_reset(
        self,
        token_hash: str,
        now: str,
    ) -> PasswordResetRecord:
        """Consume a password reset record and flush the local store."""
        consumed: PasswordResetRecord | None = None

        def mutation() -> None:
            nonlocal consumed
            consumed = InMemorySessionStore.consume_password_reset(self, token_hash, now)

        self._commit(mutation)
        if consumed is None:
            raise PersistenceError("Password reset token could not be consumed.")
        return consumed

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
        """Return a shallow copy of all in-memory authentication records."""
        return (
            self._by_email.copy(),
            self._by_user_id.copy(),
            self._sessions_by_hash.copy(),
            self._resets_by_hash.copy(),
        )

    def _restore_state(self, state: tuple[dict[str, Any], ...]) -> None:
        """Restore in-memory authentication records after a failed commit."""
        (
            self._by_email,
            self._by_user_id,
            self._sessions_by_hash,
            self._resets_by_hash,
        ) = state

    def _load(self) -> None:
        """Load existing JSON authentication records into memory."""
        if not self._store_path.exists():
            return
        try:
            payload = json.loads(self._store_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise PersistenceError("Authentication store JSON is malformed.") from error
        if not isinstance(payload, dict):
            raise PersistenceError("Authentication store JSON root must be an object.")
        if payload.get("schema_version") != AUTH_STORE_SCHEMA_VERSION:
            raise PersistenceError("Authentication store schema version is unsupported.")
        _require_payload_sections(payload)

        credentials = _load_records(
            payload,
            "credentials",
            CredentialRecord,
            "user_id",
        )
        sessions = _load_records(payload, "sessions", SessionRecord, "token_hash")
        resets = _load_records(payload, "password_resets", PasswordResetRecord, "token_hash")
        self._by_user_id = credentials
        self._by_email = _credentials_by_email(credentials)
        self._sessions_by_hash = sessions
        self._resets_by_hash = resets

    def _save(self) -> None:
        """Write the current authentication store as deterministic JSON."""
        payload = {
            "schema_version": AUTH_STORE_SCHEMA_VERSION,
            "credentials": _dump_records(self._by_user_id),
            "sessions": _dump_records(self._sessions_by_hash),
            "password_resets": _dump_records(self._resets_by_hash),
        }
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._store_path.with_suffix(f"{self._store_path.suffix}.tmp")
        temporary_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(self._store_path)


def _require_payload_sections(payload: dict[str, Any]) -> None:
    """Require every known authentication store section in persisted JSON."""
    required_sections = {
        "schema_version",
        "credentials",
        "sessions",
        "password_resets",
    }
    missing_sections = sorted(required_sections.difference(payload))
    if missing_sections:
        raise PersistenceError(
            "Authentication store JSON is missing required sections: "
            + ", ".join(missing_sections)
        )
    unknown_sections = sorted(set(payload).difference(required_sections))
    if unknown_sections:
        raise PersistenceError(
            "Authentication store JSON contains unknown sections: "
            + ", ".join(unknown_sections)
        )


def _credentials_by_email(
    credentials: dict[str, CredentialRecord],
) -> dict[str, CredentialRecord]:
    """Return credential records keyed by normalized email, rejecting duplicates."""
    by_email: dict[str, CredentialRecord] = {}
    for credential in credentials.values():
        if credential.email_normalized in by_email:
            raise PersistenceError("Authentication store contains duplicate email.")
        by_email[credential.email_normalized] = credential
    return by_email


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
        raise PersistenceError(f"Authentication store section is invalid: {key}")
    records: dict[str, T] = {}
    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            raise PersistenceError(f"Authentication store record is invalid: {key}")
        record = record_type(**raw_record)
        record_id = getattr(record, id_field)
        if record_id in records:
            raise PersistenceError(
                f"Authentication store contains duplicate record: {record_id}"
            )
        records[record_id] = record
    return records

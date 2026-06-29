"""Tamper-evident metadata-only audit ledger."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType

_GENESIS_HASH = "0" * 64
_MACHINE_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9_:-]*$")
_FORBIDDEN_METADATA_FRAGMENTS = frozenset(
    {
        "ai_response",
        "api_key",
        "content",
        "credential",
        "manuscript",
        "password",
        "payload",
        "prose",
        "quote",
        "secret",
        "serialized_output",
        "source_text",
        "token",
    }
)
_MAX_SUMMARY_LENGTH = 160
_MAX_METADATA_VALUE_LENGTH = 120


class AuditLedgerIntegrityError(ValueError):
    """Raised when an audit ledger hash chain fails verification."""


@dataclass(frozen=True)
class AuditLedgerRecord:
    """One append-only metadata record in a tamper-evident audit ledger."""

    sequence: int
    event_type: str
    occurred_at: str
    summary: str
    actor_id: str = ""
    project_id: str = ""
    story_id: str = ""
    metadata: Mapping[str, str] = MappingProxyType({})
    previous_hash: str = _GENESIS_HASH
    record_hash: str = ""

    def __post_init__(self) -> None:
        """Validate stable metadata-only record fields."""
        _require_non_negative_int(self.sequence, "Audit sequence")
        _require_machine_token(self.event_type, "Audit event type")
        _require_text(self.occurred_at, "Audit occurrence time")
        _require_summary(self.summary)
        for value, label in (
            (self.actor_id, "Audit actor ID"),
            (self.project_id, "Audit project ID"),
            (self.story_id, "Audit story ID"),
        ):
            if value:
                _require_machine_token(value, label)
        _require_hash(self.previous_hash, "Audit previous hash")
        if self.record_hash:
            _require_hash(self.record_hash, "Audit record hash")
        object.__setattr__(self, "metadata", _normalized_metadata(self.metadata))

    def payload_for_hash(self) -> dict[str, object]:
        """Return deterministic record payload used for hash chaining."""
        return {
            "sequence": self.sequence,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "summary": self.summary,
            "actor_id": self.actor_id,
            "project_id": self.project_id,
            "story_id": self.story_id,
            "metadata": dict(self.metadata),
            "previous_hash": self.previous_hash,
        }

    def with_hash(self) -> AuditLedgerRecord:
        """Return this record with its deterministic hash populated."""
        return replace(self, record_hash=_record_hash(self))


class AuditLedger:
    """Append-only in-memory audit ledger with deterministic verification."""

    def __init__(self, records: tuple[AuditLedgerRecord, ...] = ()) -> None:
        """Create a ledger and verify any supplied records."""
        self._records: list[AuditLedgerRecord] = list(records)
        self.verify()

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
        """Append one metadata-only audit record."""
        previous_hash = self._records[-1].record_hash if self._records else _GENESIS_HASH
        record = AuditLedgerRecord(
            sequence=len(self._records) + 1,
            event_type=event_type,
            occurred_at=occurred_at,
            summary=summary,
            actor_id=actor_id,
            project_id=project_id,
            story_id=story_id,
            metadata=metadata or {},
            previous_hash=previous_hash,
        ).with_hash()
        self._records.append(record)
        return record

    def records(self) -> tuple[AuditLedgerRecord, ...]:
        """Return ledger records in append order."""
        return tuple(self._records)

    def verify(self) -> None:
        """Verify sequence numbers and hash-chain integrity."""
        previous_hash = _GENESIS_HASH
        for expected_sequence, record in enumerate(self._records, start=1):
            if record.sequence != expected_sequence:
                raise AuditLedgerIntegrityError("Audit ledger sequence is not append-only.")
            if record.previous_hash != previous_hash:
                raise AuditLedgerIntegrityError("Audit ledger previous hash is invalid.")
            if record.record_hash != _record_hash(record):
                raise AuditLedgerIntegrityError("Audit ledger record hash is invalid.")
            previous_hash = record.record_hash


def _record_hash(record: AuditLedgerRecord) -> str:
    """Return deterministic SHA-256 hash for one audit record."""
    serialized = json.dumps(
        record.payload_for_hash(),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _normalized_metadata(metadata: Mapping[str, str]) -> Mapping[str, str]:
    """Return immutable metadata after privacy validation."""
    normalized: dict[str, str] = {}
    for key, value in sorted(metadata.items()):
        _require_machine_token(key, "Audit metadata key")
        _reject_sensitive_key(key)
        if not isinstance(value, str):
            raise ValueError("Audit metadata values must be strings.")
        clean_value = value.strip()
        _require_text(clean_value, "Audit metadata value")
        if "\n" in clean_value or "\r" in clean_value:
            raise ValueError("Audit metadata values must be single-line summaries.")
        if len(clean_value) > _MAX_METADATA_VALUE_LENGTH:
            raise ValueError("Audit metadata values must be concise.")
        _reject_sensitive_value(clean_value)
        normalized[key] = clean_value
    return MappingProxyType(normalized)


def _require_non_negative_int(value: int, label: str) -> None:
    """Require a non-negative integer that is not a boolean."""
    if isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer.")


def _require_machine_token(value: str, label: str) -> None:
    """Require a stable machine-readable token."""
    if not isinstance(value, str) or not _MACHINE_TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be a machine-readable token.")


def _require_hash(value: str, label: str) -> None:
    """Require a SHA-256 hex digest."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be a SHA-256 hex digest.")


def _require_text(value: str, label: str) -> None:
    """Require nonblank single-line text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")


def _require_summary(value: str) -> None:
    """Require concise metadata-only summary text."""
    _require_text(value, "Audit summary")
    if "\n" in value or "\r" in value:
        raise ValueError("Audit summary must be a single line.")
    if len(value.strip()) > _MAX_SUMMARY_LENGTH:
        raise ValueError("Audit summary must be concise.")
    _reject_sensitive_value(value)


def _reject_sensitive_key(value: str) -> None:
    """Reject metadata keys likely to store private payloads."""
    lowered = value.lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_METADATA_FRAGMENTS):
        raise ValueError("Audit metadata keys must not reference sensitive payloads.")


def _reject_sensitive_value(value: str) -> None:
    """Reject metadata values that look like secrets or local machine data."""
    lowered = value.lower()
    if "sk-" in lowered or "bearer " in lowered or "password" in lowered:
        raise ValueError("Audit metadata must not include credentials or tokens.")
    if "c:\\users\\" in lowered or "/users/" in lowered:
        raise ValueError("Audit metadata must not include machine-local paths.")

"""Tests for the Phase 11 audit ledger."""

from __future__ import annotations

from dataclasses import replace

import pytest

from aevryn.audit import AuditLedger, AuditLedgerIntegrityError

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

"""Tests for production managed identity adapter boundaries."""

from __future__ import annotations

import pytest

from aevryn.auth import (
    InvalidSessionError,
    ManagedIdentity,
    ManagedIdentityAuthenticationAdapter,
    managed_identity_user_id,
)
from aevryn.persistence import InMemoryProjectRepository

NOW = "2026-06-29T00:00:00Z"
SOON = "2026-06-29T00:05:00Z"


class StaticManagedIdentityVerifier:
    """Deterministic verifier for managed identity boundary tests."""

    def __init__(self, identity: ManagedIdentity) -> None:
        self.identity = identity
        self.calls: list[tuple[str, str]] = []

    def validate_bearer_token(self, *, token: str, now: str) -> ManagedIdentity:
        """Return the configured identity for non-empty tokens."""
        self.calls.append((token, now))
        if token == "invalid":
            raise InvalidSessionError("Managed identity token is invalid.")
        return self.identity


def test_managed_identity_user_id_is_stable_and_machine_safe() -> None:
    """External provider subjects should map to stable Aevryn user IDs."""
    user_id = managed_identity_user_id(
        provider="Supabase",
        subject="external-user-1234",
    )

    assert user_id.startswith("user_supabase_")
    assert "-" not in user_id
    assert user_id == managed_identity_user_id(
        provider="supabase",
        subject="external-user-1234",
    )


def test_managed_identity_adapter_creates_and_reuses_user_record() -> None:
    """Verified managed identities should become Aevryn ownership records."""
    repository = InMemoryProjectRepository()
    verifier = StaticManagedIdentityVerifier(
        ManagedIdentity(
            provider="supabase",
            subject="external-user-1234",
            email="CREATOR@example.com",
            display_name="Creator",
        )
    )
    adapter = ManagedIdentityAuthenticationAdapter(
        repository=repository,
        verifier=verifier,
    )

    first = adapter.validate_session(session_token="provider-token", now=NOW)
    second = adapter.validate_session(session_token="provider-token", now=SOON)

    assert first == second
    assert first.user_id == managed_identity_user_id(
        provider="supabase",
        subject="external-user-1234",
    )
    assert first.email == "creator@example.com"
    assert first.display_name == "Creator"
    assert first.created_at == NOW
    assert verifier.calls == [("provider-token", NOW), ("provider-token", SOON)]


def test_managed_identity_adapter_rejects_blank_or_invalid_tokens() -> None:
    """Managed bearer token failures should use the existing session error contract."""
    adapter = ManagedIdentityAuthenticationAdapter(
        repository=InMemoryProjectRepository(),
        verifier=StaticManagedIdentityVerifier(
            ManagedIdentity(
                provider="supabase",
                subject="external-user-1234",
                email="creator@example.com",
                display_name="Creator",
            )
        ),
    )

    with pytest.raises(InvalidSessionError, match="bearer session token"):
        adapter.validate_session(session_token=" ", now=NOW)

    with pytest.raises(InvalidSessionError, match="invalid"):
        adapter.validate_session(session_token="invalid", now=NOW)


def test_managed_identity_rejects_incomplete_provider_metadata() -> None:
    """Provider verifiers must return usable identity metadata."""
    with pytest.raises(ValueError, match="provider"):
        ManagedIdentity(
            provider=" ",
            subject="external-user-1234",
            email="creator@example.com",
            display_name="Creator",
        )
    with pytest.raises(ValueError, match="email"):
        ManagedIdentity(
            provider="supabase",
            subject="external-user-1234",
            email="not-an-email",
            display_name="Creator",
        )

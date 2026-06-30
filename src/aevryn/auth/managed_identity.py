"""Managed identity boundary for production authentication providers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from aevryn.auth.errors import InvalidSessionError
from aevryn.persistence import DuplicateRecordError, ProjectRepository, RecordNotFoundError
from aevryn.persistence.models import UserRecord


@dataclass(frozen=True, slots=True)
class ManagedIdentity:
    """Verified identity returned by a managed authentication provider."""

    provider: str
    subject: str
    email: str
    display_name: str

    def __post_init__(self) -> None:
        """Validate managed identity metadata."""
        if not self.provider.strip():
            raise ValueError("Managed identity provider cannot be blank.")
        if not self.subject.strip():
            raise ValueError("Managed identity subject cannot be blank.")
        if "@" not in self.email:
            raise ValueError("Managed identity email must look like an email address.")
        if not self.display_name.strip():
            raise ValueError("Managed identity display name cannot be blank.")


class ManagedIdentityVerifier(Protocol):
    """Boundary for provider-backed bearer token verification."""

    def validate_bearer_token(self, *, token: str, now: str) -> ManagedIdentity:
        """Return the verified managed identity for an opaque bearer token."""


class ManagedIdentityAuthenticationAdapter:
    """Map verified managed identities into Aevryn user ownership records."""

    def __init__(
        self,
        *,
        repository: ProjectRepository,
        verifier: ManagedIdentityVerifier,
    ) -> None:
        """Create the managed identity adapter."""
        self._repository = repository
        self._verifier = verifier

    def validate_session(self, *, session_token: str, now: str) -> UserRecord:
        """Validate a bearer token and return an Aevryn user record."""
        if not session_token.strip():
            raise InvalidSessionError("A bearer session token is required.")
        identity = self._verifier.validate_bearer_token(token=session_token, now=now)
        user_id = managed_identity_user_id(
            provider=identity.provider,
            subject=identity.subject,
        )
        try:
            return self._repository.get_user(user_id)
        except RecordNotFoundError:
            user = UserRecord(
                user_id=user_id,
                email=identity.email.strip().lower(),
                display_name=identity.display_name.strip(),
                created_at=now,
            )
            try:
                self._repository.create_user(user)
            except DuplicateRecordError:
                return self._repository.get_user(user_id)
            return user


def managed_identity_user_id(*, provider: str, subject: str) -> str:
    """Return a stable Aevryn user ID for one managed provider subject."""
    provider_normalized = provider.strip().lower()
    subject_normalized = subject.strip()
    if not provider_normalized:
        raise ValueError("Managed identity provider cannot be blank.")
    if not subject_normalized:
        raise ValueError("Managed identity subject cannot be blank.")
    digest = hashlib.sha256(
        f"{provider_normalized}:{subject_normalized}".encode()
    ).hexdigest()[:24]
    return f"user_{provider_normalized}_{digest}"

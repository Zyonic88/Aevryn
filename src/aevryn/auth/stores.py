"""Local authentication stores for Phase 4 foundations."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from aevryn.auth.errors import (
    CredentialNotFoundError,
    DuplicateCredentialError,
    InvalidResetTokenError,
    InvalidSessionError,
)


@dataclass(frozen=True, slots=True)
class CredentialRecord:
    """Stored password credential metadata for one user."""

    user_id: str
    email_normalized: str
    password_hash: str
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        """Validate credential metadata."""
        _require_token(self.user_id, "Credential user ID")
        _require_email(self.email_normalized, "Credential email")
        _require_text(self.password_hash, "Credential password hash")
        _require_timestamp(self.created_at, "Credential created_at")
        _require_timestamp(self.updated_at, "Credential updated_at")


@dataclass(frozen=True, slots=True)
class SessionRecord:
    """Stored session token hash for one authenticated user."""

    session_id: str
    user_id: str
    token_hash: str
    created_at: str
    expires_at: str

    def __post_init__(self) -> None:
        """Validate session metadata."""
        _require_token(self.session_id, "Session ID")
        _require_token(self.user_id, "Session user ID")
        _require_text(self.token_hash, "Session token hash")
        created_at = _require_timestamp(self.created_at, "Session created_at")
        expires_at = _require_timestamp(self.expires_at, "Session expires_at")
        if expires_at <= created_at:
            raise ValueError("Session expires_at must be after created_at.")


@dataclass(frozen=True, slots=True)
class PasswordResetRecord:
    """Stored password reset token hash for one user."""

    reset_id: str
    user_id: str
    token_hash: str
    created_at: str
    expires_at: str
    consumed_at: str = ""

    def __post_init__(self) -> None:
        """Validate password reset metadata."""
        _require_token(self.reset_id, "Password reset ID")
        _require_token(self.user_id, "Password reset user ID")
        _require_text(self.token_hash, "Password reset token hash")
        created_at = _require_timestamp(self.created_at, "Password reset created_at")
        expires_at = _require_timestamp(self.expires_at, "Password reset expires_at")
        if expires_at <= created_at:
            raise ValueError("Password reset expires_at must be after created_at.")
        if self.consumed_at:
            consumed_at = _require_timestamp(self.consumed_at, "Password reset consumed_at")
            if consumed_at < created_at:
                raise ValueError("Password reset consumed_at cannot be before created_at.")


class CredentialStore(Protocol):
    """Persistence boundary for authentication credentials."""

    def create_credential(self, credential: CredentialRecord) -> None:
        """Store a new credential record."""

    def get_credential_by_email(self, email_normalized: str) -> CredentialRecord:
        """Return a credential record by normalized email."""

    def delete_credential_for_auth_rollback(self, user_id: str) -> None:
        """Delete credentials created by a failed authentication registration."""

    def update_password_hash(self, user_id: str, password_hash: str, updated_at: str) -> None:
        """Replace a user's password hash."""


class SessionStore(Protocol):
    """Persistence boundary for authentication sessions and resets."""

    def create_session(self, session: SessionRecord) -> None:
        """Store a new session record."""

    def get_session_by_token_hash(self, token_hash: str, now: str) -> SessionRecord:
        """Return an active session by token hash."""

    def create_password_reset(self, reset: PasswordResetRecord) -> None:
        """Store a password reset record."""

    def consume_password_reset(
        self,
        token_hash: str,
        now: str,
    ) -> PasswordResetRecord:
        """Consume and return an active password reset record."""


class InMemoryCredentialStore:
    """Deterministic local credential store for Phase 4 tests."""

    def __init__(self) -> None:
        """Create an empty credential store."""
        self._by_email: dict[str, CredentialRecord] = {}
        self._by_user_id: dict[str, CredentialRecord] = {}

    def create_credential(self, credential: CredentialRecord) -> None:
        """Store a new credential record."""
        if credential.email_normalized in self._by_email:
            raise DuplicateCredentialError("Email is already registered.")
        if credential.user_id in self._by_user_id:
            raise DuplicateCredentialError("User credentials already exist.")
        self._by_email[credential.email_normalized] = credential
        self._by_user_id[credential.user_id] = credential

    def get_credential_by_email(self, email_normalized: str) -> CredentialRecord:
        """Return a credential record by normalized email."""
        credential = self._by_email.get(email_normalized)
        if credential is None:
            raise CredentialNotFoundError("Credential does not exist.")
        return credential

    def delete_credential_for_auth_rollback(self, user_id: str) -> None:
        """Delete credentials created by a failed authentication registration."""
        credential = self._by_user_id.pop(user_id, None)
        if credential is not None:
            self._by_email.pop(credential.email_normalized, None)

    def update_password_hash(self, user_id: str, password_hash: str, updated_at: str) -> None:
        """Replace a user's password hash."""
        credential = self._by_user_id.get(user_id)
        if credential is None:
            raise InvalidResetTokenError("Password reset credential does not exist.")
        updated = replace(
            credential,
            password_hash=password_hash,
            updated_at=updated_at,
        )
        self._by_user_id[user_id] = updated
        self._by_email[updated.email_normalized] = updated


class InMemorySessionStore:
    """Deterministic local session and reset store for Phase 4 tests."""

    def __init__(self) -> None:
        """Create an empty session store."""
        self._sessions_by_hash: dict[str, SessionRecord] = {}
        self._resets_by_hash: dict[str, PasswordResetRecord] = {}

    def create_session(self, session: SessionRecord) -> None:
        """Store a new session record."""
        if session.token_hash in self._sessions_by_hash:
            raise DuplicateCredentialError("Session token already exists.")
        self._sessions_by_hash[session.token_hash] = session

    def get_session_by_token_hash(self, token_hash: str, now: str) -> SessionRecord:
        """Return an active session by token hash."""
        session = self._sessions_by_hash.get(token_hash)
        if session is None:
            raise InvalidSessionError("Session is invalid.")
        if _require_timestamp(now, "Session validation time") >= _require_timestamp(
            session.expires_at,
            "Session expires_at",
        ):
            raise InvalidSessionError("Session is expired.")
        return session

    def create_password_reset(self, reset: PasswordResetRecord) -> None:
        """Store a password reset record."""
        if reset.token_hash in self._resets_by_hash:
            raise DuplicateCredentialError("Password reset token already exists.")
        if any(existing.reset_id == reset.reset_id for existing in self._resets_by_hash.values()):
            raise DuplicateCredentialError("Password reset ID already exists.")
        self._resets_by_hash[reset.token_hash] = reset

    def consume_password_reset(
        self,
        token_hash: str,
        now: str,
    ) -> PasswordResetRecord:
        """Consume and return an active password reset record."""
        reset = self._resets_by_hash.get(token_hash)
        if reset is None or reset.consumed_at:
            raise InvalidResetTokenError("Password reset token is invalid.")
        if _require_timestamp(now, "Password reset validation time") >= _require_timestamp(
            reset.expires_at,
            "Password reset expires_at",
        ):
            raise InvalidResetTokenError("Password reset token is expired.")
        consumed = replace(reset, consumed_at=now)
        self._resets_by_hash[token_hash] = consumed
        return consumed


def normalize_email(email: str) -> str:
    """Return the canonical credential lookup email."""
    _require_email(email, "Email")
    return email.strip().casefold()


def _require_token(value: str, label: str) -> None:
    """Require a stable machine-readable token."""
    if not isinstance(value, str) or not value.replace("_", "").isalnum():
        raise ValueError(f"{label} must be a machine-readable token.")
    if value[0].isdigit():
        raise ValueError(f"{label} cannot start with a digit.")


def _require_text(value: str, label: str) -> None:
    """Require nonblank text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} cannot be blank.")


def _require_email(value: str, label: str) -> None:
    """Require a simple email-like value."""
    _require_text(value, label)
    normalized = value.strip()
    if normalized != value or any(character.isspace() for character in value):
        raise ValueError(f"{label} cannot contain surrounding or inner whitespace.")
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValueError(f"{label} must be email-like.")


def _require_timestamp(value: str, label: str) -> datetime:
    """Require and return a UTC timestamp ending in Z."""
    _require_text(value, label)
    if "T" not in value or not value.endswith("Z"):
        raise ValueError(f"{label} must be an ISO UTC timestamp ending in Z.")
    try:
        return datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO UTC timestamp ending in Z.") from error

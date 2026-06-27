"""Authentication service for Aevryn platform identity."""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Callable
from dataclasses import dataclass

from aevryn.auth.errors import (
    CredentialNotFoundError,
    DuplicateCredentialError,
    InvalidCredentialsError,
)
from aevryn.auth.models import AuthenticatedSession, PasswordResetToken, RegisteredUser
from aevryn.auth.passwords import PasswordHasher
from aevryn.auth.stores import (
    CredentialRecord,
    CredentialStore,
    PasswordResetRecord,
    SessionRecord,
    SessionStore,
    normalize_email,
)
from aevryn.persistence import ProjectRepository, UserRecord

TokenFactory = Callable[[], str]


@dataclass(frozen=True, slots=True)
class AuthenticationConfig:
    """Authentication service timing configuration."""

    session_duration_seconds: int = 86_400
    reset_duration_seconds: int = 3_600

    def __post_init__(self) -> None:
        """Validate authentication timing configuration."""
        if self.session_duration_seconds < 1:
            raise ValueError("Session duration must be positive.")
        if self.reset_duration_seconds < 1:
            raise ValueError("Reset duration must be positive.")


class AuthenticationService:
    """Register, authenticate, and recover platform users."""

    def __init__(
        self,
        *,
        repository: ProjectRepository,
        credential_store: CredentialStore,
        session_store: SessionStore,
        password_hasher: PasswordHasher | None = None,
        token_factory: TokenFactory | None = None,
        config: AuthenticationConfig | None = None,
    ) -> None:
        """Create an authentication service."""
        self._repository = repository
        self._credential_store = credential_store
        self._session_store = session_store
        self._password_hasher = password_hasher or PasswordHasher()
        self._token_factory = token_factory or _secure_token
        self._config = config or AuthenticationConfig()

    def register(
        self,
        *,
        user_id: str,
        email: str,
        display_name: str,
        password: str,
        now: str,
    ) -> RegisteredUser:
        """Register a user and return an authenticated session."""
        email_normalized = normalize_email(email)
        try:
            self._credential_store.get_credential_by_email(email_normalized)
        except CredentialNotFoundError:
            pass
        else:
            raise DuplicateCredentialError("Email is already registered.")
        user = UserRecord(
            user_id=user_id,
            email=email_normalized,
            display_name=display_name,
            created_at=now,
        )
        password_hash = self._password_hasher.hash_password(password)
        self._repository.create_user(user)
        try:
            self._credential_store.create_credential(
                CredentialRecord(
                    user_id=user_id,
                    email_normalized=email_normalized,
                    password_hash=password_hash,
                    created_at=now,
                    updated_at=now,
                )
            )
            session = self._issue_session(user=user, now=now)
        except Exception:
            self._credential_store.delete_credential_for_auth_rollback(user_id)
            self._repository.delete_user_for_auth_rollback(user_id)
            raise
        return RegisteredUser(user=user, session=session)

    def login(self, *, email: str, password: str, now: str) -> AuthenticatedSession:
        """Authenticate a user by email and password."""
        email_normalized = normalize_email(email)
        try:
            credential = self._credential_store.get_credential_by_email(email_normalized)
        except CredentialNotFoundError as error:
            raise InvalidCredentialsError("Invalid email or password.") from error
        if not self._password_hasher.verify_password(password, credential.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")
        user = self._repository.get_user(credential.user_id)
        return self._issue_session(user=user, now=now)

    def validate_session(self, *, session_token: str, now: str) -> UserRecord:
        """Return the authenticated user for a valid session token."""
        token_hash = self._password_hasher.token_hash(session_token)
        session = self._session_store.get_session_by_token_hash(token_hash, now=now)
        return self._repository.get_user(session.user_id)

    def request_password_reset(
        self,
        *,
        email: str,
        reset_id: str,
        now: str,
    ) -> PasswordResetToken:
        """Issue a password reset token for a known email."""
        email_normalized = normalize_email(email)
        credential = self._credential_store.get_credential_by_email(email_normalized)
        reset_token = self._token_factory()
        expires_at = _offset_timestamp(now=now, seconds=self._config.reset_duration_seconds)
        self._session_store.create_password_reset(
            PasswordResetRecord(
                reset_id=reset_id,
                user_id=credential.user_id,
                token_hash=self._password_hasher.token_hash(reset_token),
                created_at=now,
                expires_at=expires_at,
            )
        )
        return PasswordResetToken(
            user_id=credential.user_id,
            reset_token=reset_token,
            expires_at=expires_at,
        )

    def complete_password_reset(
        self,
        *,
        reset_token: str,
        new_password: str,
        now: str,
    ) -> None:
        """Consume a reset token and replace the user's password hash."""
        token_hash = self._password_hasher.token_hash(reset_token)
        reset = self._session_store.consume_password_reset(token_hash, now=now)
        password_hash = self._password_hasher.hash_password(new_password)
        self._credential_store.update_password_hash(
            user_id=reset.user_id,
            password_hash=password_hash,
            updated_at=now,
        )

    def _issue_session(self, *, user: UserRecord, now: str) -> AuthenticatedSession:
        """Issue and store a session for a user."""
        session_token = self._token_factory()
        expires_at = _offset_timestamp(now=now, seconds=self._config.session_duration_seconds)
        self._session_store.create_session(
            SessionRecord(
                session_id=f"session_{user.user_id}_{_token_suffix(session_token)}",
                user_id=user.user_id,
                token_hash=self._password_hasher.token_hash(session_token),
                created_at=now,
                expires_at=expires_at,
            )
        )
        return AuthenticatedSession(
            user=user,
            session_token=session_token,
            expires_at=expires_at,
        )


def _token_suffix(token: str) -> str:
    """Return a machine-safe deterministic suffix for an opaque token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def _secure_token() -> str:
    """Return an opaque URL-safe token."""
    return secrets.token_urlsafe(32)


def _offset_timestamp(*, now: str, seconds: int) -> str:
    """Return a UTC timestamp offset by seconds."""
    from datetime import datetime, timedelta

    if "T" not in now or not now.endswith("Z"):
        raise ValueError("Timestamp must be an ISO UTC timestamp ending in Z.")
    current = datetime.fromisoformat(f"{now[:-1]}+00:00")
    return (current + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")

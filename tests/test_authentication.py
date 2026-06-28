"""Tests for Aevryn V2 Phase 4 authentication foundations."""

from __future__ import annotations

from pathlib import Path

import pytest

from aevryn.auth import (
    AuthenticationConfig,
    AuthenticationService,
    CredentialNotFoundError,
    DuplicateCredentialError,
    InMemoryCredentialStore,
    InMemorySessionStore,
    InvalidCredentialsError,
    InvalidResetTokenError,
    InvalidSessionError,
    JsonAuthenticationStore,
    PasswordHasher,
    PasswordPolicyError,
)
from aevryn.auth.stores import CredentialRecord, PasswordResetRecord, SessionRecord, normalize_email
from aevryn.persistence import (
    InMemoryProjectRepository,
    PersistenceError,
    ProjectRecord,
    RecordNotFoundError,
)

NOW = "2026-06-27T00:00:00Z"
SOON = "2026-06-27T00:30:00Z"
LATER = "2026-06-28T00:00:01Z"
PASSWORD = "StrongPass123"
NEW_PASSWORD = "BetterPass456"


def test_password_hasher_hashes_without_storing_plaintext() -> None:
    """Password hashes should be versioned and not contain plaintext."""
    password_hash = PasswordHasher(iterations=10).hash_password(
        PASSWORD,
        salt=b"fixed_salt",
    )

    assert password_hash.startswith("pbkdf2_sha256$10$")
    assert PASSWORD not in password_hash
    assert PasswordHasher().verify_password(PASSWORD, password_hash)
    assert not PasswordHasher().verify_password("WrongPass123", password_hash)


def test_password_hasher_rejects_weak_passwords() -> None:
    """Local password policy should reject weak secrets."""
    hasher = PasswordHasher(iterations=10)

    with pytest.raises(PasswordPolicyError, match="at least 12"):
        hasher.hash_password("Short1")
    with pytest.raises(PasswordPolicyError, match="uppercase"):
        hasher.hash_password("lowercase1234")
    with pytest.raises(PasswordPolicyError, match="number"):
        hasher.hash_password("NoNumberPass")


def test_authentication_registers_user_and_session() -> None:
    """Registration should create user identity, credentials, and a session."""
    repository = InMemoryProjectRepository()
    credentials = InMemoryCredentialStore()
    service = auth_service(repository=repository, credential_store=credentials)

    result = service.register(
        user_id="user_demo",
        email="Demo@Example.com",
        display_name="Demo User",
        password=PASSWORD,
        now=NOW,
    )

    assert result.user.email == "demo@example.com"
    assert result.session.user.user_id == "user_demo"
    assert result.session.session_token == "token_001"
    credential = credentials.get_credential_by_email("demo@example.com")
    assert credential.user_id == "user_demo"
    assert PASSWORD not in credential.password_hash
    assert repository.get_user("user_demo").display_name == "Demo User"


def test_authentication_rejects_duplicate_registration_email() -> None:
    """Duplicate normalized emails should be rejected."""
    service = auth_service()
    service.register(
        user_id="user_demo",
        email="demo@example.com",
        display_name="Demo User",
        password=PASSWORD,
        now=NOW,
    )

    with pytest.raises(DuplicateCredentialError, match="already registered"):
        service.register(
            user_id="user_other",
            email="DEMO@example.com",
            display_name="Other User",
            password=PASSWORD,
            now=NOW,
        )


def test_authentication_registration_preflights_existing_credentials() -> None:
    """Existing credentials should stop registration before user creation."""
    repository = InMemoryProjectRepository()
    credentials = InMemoryCredentialStore()
    credentials.create_credential(
        CredentialRecord(
            user_id="user_existing",
            email_normalized="demo@example.com",
            password_hash="pbkdf2_sha256$existing",
            created_at=NOW,
            updated_at=NOW,
        )
    )

    with pytest.raises(DuplicateCredentialError, match="already registered"):
        auth_service(repository=repository, credential_store=credentials).register(
            user_id="user_demo",
            email="demo@example.com",
            display_name="Demo User",
            password=PASSWORD,
            now=NOW,
        )

    with pytest.raises(RecordNotFoundError, match="Unknown user"):
        repository.get_user("user_demo")


def test_authentication_rolls_back_user_when_session_creation_fails() -> None:
    """Registration failures after user creation should not leave orphan users."""
    repository = InMemoryProjectRepository()
    service = auth_service(
        repository=repository,
        session_store=FailingSessionStore(),
    )

    with pytest.raises(RuntimeError, match="Session store unavailable."):
        service.register(
            user_id="user_demo",
            email="demo@example.com",
            display_name="Demo User",
            password=PASSWORD,
            now=NOW,
        )

    with pytest.raises(RecordNotFoundError, match="Unknown user"):
        repository.get_user("user_demo")

    retry = auth_service(repository=repository).register(
        user_id="user_demo",
        email="demo@example.com",
        display_name="Demo User",
        password=PASSWORD,
        now=NOW,
    )
    assert retry.user.user_id == "user_demo"


def test_authentication_rollback_refuses_user_with_projects() -> None:
    """Rollback deletion should not remove users that already own projects."""
    repository = InMemoryProjectRepository()
    service = auth_service(repository=repository)
    service.register(
        user_id="user_demo",
        email="demo@example.com",
        display_name="Demo User",
        password=PASSWORD,
        now=NOW,
    )
    repository.create_project(
        ProjectRecord(
            project_id="project_demo",
            owner_user_id="user_demo",
            name="Demo Project",
            created_at=NOW,
            updated_at=NOW,
        )
    )

    with pytest.raises(ValueError, match="owns projects"):
        repository.delete_user_for_auth_rollback("user_demo")


def test_authentication_stores_reject_duplicate_session_and_reset_tokens() -> None:
    """Auth stores should not overwrite token records by hash or reset ID."""
    store = InMemorySessionStore()
    session = SessionRecord(
        session_id="session_demo",
        user_id="user_demo",
        token_hash="sha256$token",
        created_at=NOW,
        expires_at=SOON,
    )
    store.create_session(session)

    with pytest.raises(DuplicateCredentialError, match="Session token already exists"):
        store.create_session(session)

    reset = PasswordResetRecord(
        reset_id="reset_demo",
        user_id="user_demo",
        token_hash="sha256$reset",
        created_at=NOW,
        expires_at=SOON,
    )
    store.create_password_reset(reset)

    with pytest.raises(DuplicateCredentialError, match="Password reset token"):
        store.create_password_reset(reset)
    with pytest.raises(DuplicateCredentialError, match="Password reset ID"):
        store.create_password_reset(
            PasswordResetRecord(
                reset_id="reset_demo",
                user_id="user_demo",
                token_hash="sha256$other",
                created_at=NOW,
                expires_at=SOON,
            )
        )


def test_authentication_login_issues_session_for_valid_credentials() -> None:
    """Login should verify credentials and issue a new session."""
    repository = InMemoryProjectRepository()
    service = auth_service(repository=repository)
    service.register(
        user_id="user_demo",
        email="demo@example.com",
        display_name="Demo User",
        password=PASSWORD,
        now=NOW,
    )

    session = service.login(email="DEMO@example.com", password=PASSWORD, now=NOW)

    assert session.user.user_id == "user_demo"
    assert session.session_token == "token_002"
    assert service.validate_session(session_token=session.session_token, now=SOON) == (
        repository.get_user("user_demo")
    )


def test_authentication_rejects_invalid_credentials() -> None:
    """Login failures should use a stable generic error."""
    service = auth_service()
    service.register(
        user_id="user_demo",
        email="demo@example.com",
        display_name="Demo User",
        password=PASSWORD,
        now=NOW,
    )

    with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
        service.login(email="demo@example.com", password="WrongPass123", now=NOW)
    with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
        service.login(email="missing@example.com", password=PASSWORD, now=NOW)


def test_authentication_rejects_expired_session() -> None:
    """Expired session tokens should fail safely."""
    service = auth_service(
        config=AuthenticationConfig(session_duration_seconds=60, reset_duration_seconds=60)
    )
    result = service.register(
        user_id="user_demo",
        email="demo@example.com",
        display_name="Demo User",
        password=PASSWORD,
        now=NOW,
    )

    with pytest.raises(InvalidSessionError, match="expired"):
        service.validate_session(session_token=result.session.session_token, now=SOON)


def test_authentication_password_reset_replaces_password_and_consumes_token() -> None:
    """Password reset should update credentials and prevent token reuse."""
    service = auth_service()
    service.register(
        user_id="user_demo",
        email="demo@example.com",
        display_name="Demo User",
        password=PASSWORD,
        now=NOW,
    )
    reset = service.request_password_reset(
        email="demo@example.com",
        reset_id="reset_demo",
        now=NOW,
    )

    assert reset.user_id == "user_demo"
    assert reset.reset_token == "token_002"
    service.complete_password_reset(
        reset_token=reset.reset_token,
        new_password=NEW_PASSWORD,
        now=SOON,
    )

    with pytest.raises(InvalidCredentialsError):
        service.login(email="demo@example.com", password=PASSWORD, now=SOON)
    assert service.login(email="demo@example.com", password=NEW_PASSWORD, now=SOON)
    with pytest.raises(InvalidResetTokenError, match="invalid"):
        service.complete_password_reset(
            reset_token=reset.reset_token,
            new_password="AnotherPass789",
            now=SOON,
        )


def test_json_authentication_store_persists_records(tmp_path: Path) -> None:
    """JSON auth store should reload credentials, sessions, and reset state."""
    store_path = tmp_path / "auth_store.json"
    repository = InMemoryProjectRepository()
    store = JsonAuthenticationStore(store_path)
    service = auth_service(
        repository=repository,
        credential_store=store,
        session_store=store,
    )
    result = service.register(
        user_id="user_demo",
        email="demo@example.com",
        display_name="Demo User",
        password=PASSWORD,
        now=NOW,
    )
    reset = service.request_password_reset(
        email="demo@example.com",
        reset_id="reset_demo",
        now=NOW,
    )
    service.complete_password_reset(
        reset_token=reset.reset_token,
        new_password=NEW_PASSWORD,
        now=SOON,
    )

    reloaded = JsonAuthenticationStore(store_path)
    reloaded_service = AuthenticationService(
        repository=repository,
        credential_store=reloaded,
        session_store=reloaded,
        password_hasher=PasswordHasher(iterations=10),
        token_factory=lambda: "token_after_reload",
    )

    assert reloaded_service.validate_session(
        session_token=result.session.session_token,
        now=SOON,
    ).user_id == "user_demo"
    assert reloaded_service.login(
        email="demo@example.com",
        password=NEW_PASSWORD,
        now=SOON,
    ).user.user_id == "user_demo"
    with pytest.raises(InvalidResetTokenError, match="invalid"):
        reloaded_service.complete_password_reset(
            reset_token=reset.reset_token,
            new_password="AnotherPass789",
            now=SOON,
        )


def test_json_authentication_store_rejects_malformed_payload(tmp_path: Path) -> None:
    """JSON auth store should fail clearly when persisted data is malformed."""
    store_path = tmp_path / "auth_store.json"
    store_path.write_text('{"schema_version":"wrong"}', encoding="utf-8")

    with pytest.raises(PersistenceError, match="schema version"):
        JsonAuthenticationStore(store_path)


def test_authentication_rejects_expired_password_reset_token() -> None:
    """Expired reset tokens should not change credentials."""
    service = auth_service(
        config=AuthenticationConfig(session_duration_seconds=60, reset_duration_seconds=60)
    )
    service.register(
        user_id="user_demo",
        email="demo@example.com",
        display_name="Demo User",
        password=PASSWORD,
        now=NOW,
    )
    reset = service.request_password_reset(
        email="demo@example.com",
        reset_id="reset_demo",
        now=NOW,
    )

    with pytest.raises(InvalidResetTokenError, match="expired"):
        service.complete_password_reset(
            reset_token=reset.reset_token,
            new_password=NEW_PASSWORD,
            now=LATER,
        )


def test_authentication_public_exports_are_available() -> None:
    """The auth package should expose service, stores, and errors."""
    assert issubclass(CredentialNotFoundError, Exception)
    assert issubclass(DuplicateCredentialError, Exception)
    assert normalize_email("Demo@Example.com") == "demo@example.com"
    credential = CredentialRecord(
        user_id="user_demo",
        email_normalized="demo@example.com",
        password_hash="pbkdf2_sha256$demo",
        created_at=NOW,
        updated_at=NOW,
    )
    assert credential.email_normalized == "demo@example.com"


def auth_service(
    *,
    repository: InMemoryProjectRepository | None = None,
    credential_store: InMemoryCredentialStore | JsonAuthenticationStore | None = None,
    session_store: InMemorySessionStore | JsonAuthenticationStore | None = None,
    config: AuthenticationConfig | None = None,
) -> AuthenticationService:
    """Return an authentication service with deterministic tokens."""
    token_factory = TokenFactory()
    return AuthenticationService(
        repository=repository or InMemoryProjectRepository(),
        credential_store=credential_store or InMemoryCredentialStore(),
        session_store=session_store or InMemorySessionStore(),
        password_hasher=PasswordHasher(iterations=10),
        token_factory=token_factory.next_token,
        config=config,
    )


class FailingSessionStore(InMemorySessionStore):
    """Session store that fails on session creation."""

    def create_session(self, _session: SessionRecord) -> None:
        """Raise a deterministic storage failure."""
        raise RuntimeError("Session store unavailable.")


class TokenFactory:
    """Deterministic token factory for tests."""

    def __init__(self) -> None:
        """Create a token counter."""
        self._index = 0

    def next_token(self) -> str:
        """Return the next stable token."""
        self._index += 1
        return f"token_{self._index:03d}"

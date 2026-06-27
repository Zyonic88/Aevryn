"""Aevryn authentication boundary."""

from aevryn.auth.errors import (
    AuthenticationError,
    CredentialNotFoundError,
    DuplicateCredentialError,
    InvalidCredentialsError,
    InvalidResetTokenError,
    InvalidSessionError,
    PasswordPolicyError,
)
from aevryn.auth.models import (
    AuthenticatedSession,
    PasswordResetToken,
    RegisteredUser,
)
from aevryn.auth.passwords import PasswordHasher
from aevryn.auth.service import AuthenticationConfig, AuthenticationService
from aevryn.auth.stores import (
    CredentialRecord,
    InMemoryCredentialStore,
    InMemorySessionStore,
    PasswordResetRecord,
    SessionRecord,
)

__all__ = [
    "AuthenticatedSession",
    "AuthenticationConfig",
    "AuthenticationError",
    "AuthenticationService",
    "CredentialNotFoundError",
    "CredentialRecord",
    "DuplicateCredentialError",
    "InMemoryCredentialStore",
    "InMemorySessionStore",
    "InvalidCredentialsError",
    "InvalidResetTokenError",
    "InvalidSessionError",
    "PasswordHasher",
    "PasswordPolicyError",
    "PasswordResetRecord",
    "PasswordResetToken",
    "RegisteredUser",
    "SessionRecord",
]

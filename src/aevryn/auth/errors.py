"""Authentication error types."""

from __future__ import annotations


class AuthenticationError(Exception):
    """Base error for authentication failures."""


class CredentialNotFoundError(AuthenticationError):
    """Raised when credentials do not exist for a lookup identity."""


class DuplicateCredentialError(AuthenticationError):
    """Raised when credentials already exist for an identity."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""


class InvalidSessionError(AuthenticationError):
    """Raised when a session token is invalid or expired."""


class InvalidResetTokenError(AuthenticationError):
    """Raised when a password reset token is invalid or expired."""


class PasswordPolicyError(AuthenticationError):
    """Raised when a password does not satisfy platform policy."""

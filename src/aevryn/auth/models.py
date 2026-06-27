"""Authentication service models."""

from __future__ import annotations

from dataclasses import dataclass

from aevryn.persistence import UserRecord


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    """Authenticated platform session returned after registration or login."""

    user: UserRecord
    session_token: str
    expires_at: str

    def __post_init__(self) -> None:
        """Validate session response fields."""
        if not self.session_token.strip():
            raise ValueError("Session token cannot be blank.")
        if not self.expires_at.strip():
            raise ValueError("Session expiration cannot be blank.")


@dataclass(frozen=True, slots=True)
class RegisteredUser:
    """Registration result containing user identity and active session."""

    user: UserRecord
    session: AuthenticatedSession

    def __post_init__(self) -> None:
        """Validate registration alignment."""
        if self.user.user_id != self.session.user.user_id:
            raise ValueError("Registered user and session user must match.")


@dataclass(frozen=True, slots=True)
class PasswordResetToken:
    """Opaque password reset token returned for delivery."""

    user_id: str
    reset_token: str
    expires_at: str

    def __post_init__(self) -> None:
        """Validate password reset response fields."""
        if not self.user_id.strip():
            raise ValueError("Password reset user ID cannot be blank.")
        if not self.reset_token.strip():
            raise ValueError("Password reset token cannot be blank.")
        if not self.expires_at.strip():
            raise ValueError("Password reset expiration cannot be blank.")

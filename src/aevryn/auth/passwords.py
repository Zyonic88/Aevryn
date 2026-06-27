"""Password hashing utilities for Aevryn authentication."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from aevryn.auth.errors import PasswordPolicyError

_ALGORITHM = "pbkdf2_sha256"
_DEFAULT_ITERATIONS = 210_000
_MIN_PASSWORD_LENGTH = 12


class PasswordHasher:
    """Hash and verify passwords without storing plaintext secrets."""

    def __init__(self, iterations: int = _DEFAULT_ITERATIONS) -> None:
        """Create a password hasher.

        Parameters:
            iterations: PBKDF2 iteration count. Must be positive.
        """
        if isinstance(iterations, bool) or iterations < 1:
            raise ValueError("Password hash iterations must be a positive integer.")
        self._iterations = iterations

    def hash_password(self, password: str, salt: bytes | None = None) -> str:
        """Return a versioned password hash for a plaintext password."""
        self.validate_password(password)
        active_salt = salt if salt is not None else secrets.token_bytes(16)
        if not active_salt:
            raise ValueError("Password hash salt cannot be empty.")
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            active_salt,
            self._iterations,
        )
        return "$".join(
            (
                _ALGORITHM,
                str(self._iterations),
                _b64(active_salt),
                _b64(derived),
            )
        )

    def verify_password(self, password: str, encoded_hash: str) -> bool:
        """Return whether a plaintext password matches a stored hash."""
        try:
            algorithm, iterations_text, salt_text, derived_text = encoded_hash.split("$", 3)
            if algorithm != _ALGORITHM:
                return False
            iterations = int(iterations_text)
            salt = _b64decode(salt_text)
            expected = _b64decode(derived_text)
        except (ValueError, UnicodeEncodeError):
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual, expected)

    def token_hash(self, token: str) -> str:
        """Return a stable hash for an opaque session or reset token."""
        if not isinstance(token, str) or not token.strip():
            raise ValueError("Token cannot be blank.")
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        return f"sha256${_b64(digest)}"

    def validate_password(self, password: str) -> None:
        """Validate password strength for local authentication."""
        if not isinstance(password, str) or len(password) < _MIN_PASSWORD_LENGTH:
            raise PasswordPolicyError("Password must be at least 12 characters.")
        if password.strip() != password:
            raise PasswordPolicyError("Password cannot start or end with whitespace.")
        if not any(character.islower() for character in password):
            raise PasswordPolicyError("Password must include a lowercase letter.")
        if not any(character.isupper() for character in password):
            raise PasswordPolicyError("Password must include an uppercase letter.")
        if not any(character.isdigit() for character in password):
            raise PasswordPolicyError("Password must include a number.")


def _b64(value: bytes) -> str:
    """Return URL-safe base64 text without padding."""
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    """Decode URL-safe base64 text with optional padding removed."""
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))

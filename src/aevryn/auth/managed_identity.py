"""Managed identity boundary for production authentication providers."""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from aevryn.auth.errors import InvalidSessionError
from aevryn.persistence import DuplicateRecordError, ProjectRepository, RecordNotFoundError
from aevryn.persistence.models import UserRecord

JsonMapping = Mapping[str, object]
JwksFetcher = Callable[[str], JsonMapping]


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


class JwtDecoder(Protocol):
    """Boundary for JWT verification and claims extraction."""

    def decode(self, *, token: str, now: str) -> JsonMapping:
        """Return verified JWT claims."""


class SupabaseJwtVerifier:
    """Verify Supabase bearer tokens and return managed identity metadata."""

    def __init__(self, *, decoder: JwtDecoder) -> None:
        """Create a Supabase JWT verifier."""
        self._decoder = decoder

    def validate_bearer_token(self, *, token: str, now: str) -> ManagedIdentity:
        """Return the Supabase identity for a verified bearer token."""
        claims = self._decoder.decode(token=token, now=now)
        subject = _claim_text(claims, "sub")
        email = _claim_text(claims, "email")
        display_name = _supabase_display_name(claims, email=email)
        return ManagedIdentity(
            provider="supabase",
            subject=subject,
            email=email,
            display_name=display_name,
        )


class SupabaseJwksJwtDecoder:
    """Decode and verify Supabase RS256 JWTs against a JWKS endpoint."""

    def __init__(
        self,
        *,
        jwks_url: str,
        issuer: str,
        audience: str = "authenticated",
        leeway_seconds: int = 60,
        jwks_fetcher: JwksFetcher | None = None,
    ) -> None:
        """Create a Supabase JWKS JWT decoder."""
        if not jwks_url.startswith("https://"):
            raise ValueError("Supabase JWKS URL must use https://.")
        if not issuer.startswith("https://"):
            raise ValueError("Supabase issuer must use https://.")
        if leeway_seconds < 0:
            raise ValueError("JWT leeway cannot be negative.")
        self._jwks_url = jwks_url
        self._issuer = issuer.rstrip("/")
        self._audience = audience
        self._leeway_seconds = leeway_seconds
        self._jwks_fetcher = jwks_fetcher or _fetch_jwks

    def decode(self, *, token: str, now: str) -> JsonMapping:
        """Return verified JWT claims."""
        header, payload, signed_content, signature = _parse_compact_jwt(token)
        if header.get("alg") != "RS256":
            raise InvalidSessionError("Supabase JWT must use RS256.")
        kid = _claim_text(header, "kid")
        jwks = self._jwks_fetcher(self._jwks_url)
        key = _jwks_key_for_kid(jwks, kid)
        _verify_rs256_signature(
            key=key,
            signed_content=signed_content,
            signature=signature,
        )
        self._validate_claims(payload=payload, now=now)
        return payload

    def _validate_claims(self, *, payload: JsonMapping, now: str) -> None:
        """Validate Supabase issuer, audience, and time claims."""
        if payload.get("iss") != self._issuer:
            raise InvalidSessionError("Supabase JWT issuer is invalid.")
        audience = payload.get("aud")
        if isinstance(audience, str):
            audience_valid = audience == self._audience
        elif isinstance(audience, list):
            audience_valid = self._audience in audience
        else:
            audience_valid = False
        if not audience_valid:
            raise InvalidSessionError("Supabase JWT audience is invalid.")
        now_seconds = _timestamp_seconds(now)
        exp = _numeric_claim(payload, "exp")
        if exp < now_seconds - self._leeway_seconds:
            raise InvalidSessionError("Supabase JWT has expired.")
        nbf = payload.get("nbf")
        if nbf is not None and _numeric_claim(payload, "nbf") > now_seconds + self._leeway_seconds:
            raise InvalidSessionError("Supabase JWT is not valid yet.")


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


def supabase_issuer_from_url(supabase_url: str) -> str:
    """Return the expected Supabase JWT issuer for a project URL."""
    project_url = supabase_url.strip().rstrip("/")
    if not project_url.startswith("https://"):
        raise ValueError("Supabase URL must use https://.")
    return f"{project_url}/auth/v1"


def _claim_text(claims: JsonMapping, key: str) -> str:
    """Return a required text claim."""
    value = claims.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InvalidSessionError(f"Supabase JWT missing required {key} claim.")
    return value.strip()


def _supabase_display_name(claims: JsonMapping, *, email: str) -> str:
    """Return a useful display name from Supabase claims."""
    metadata = claims.get("user_metadata")
    if isinstance(metadata, Mapping):
        for key in ("display_name", "full_name", "name"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return email.split("@", 1)[0]


def _parse_compact_jwt(token: str) -> tuple[JsonMapping, JsonMapping, bytes, bytes]:
    """Parse a compact JWT into decoded metadata and signed bytes."""
    parts = token.split(".")
    if len(parts) != 3 or not all(parts):
        raise InvalidSessionError("Supabase JWT is malformed.")
    header = _json_from_base64url(parts[0], "header")
    payload = _json_from_base64url(parts[1], "payload")
    signature = _bytes_from_base64url(parts[2], "signature")
    return header, payload, f"{parts[0]}.{parts[1]}".encode(), signature


def _json_from_base64url(value: str, label: str) -> JsonMapping:
    """Decode one base64url JSON JWT section."""
    try:
        decoded = _bytes_from_base64url(value, label)
        payload = json.loads(decoded.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidSessionError(f"Supabase JWT {label} is invalid.") from error
    if not isinstance(payload, dict):
        raise InvalidSessionError(f"Supabase JWT {label} must be an object.")
    return payload


def _bytes_from_base64url(value: str, label: str) -> bytes:
    """Decode unpadded base64url text."""
    try:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(f"{value}{padding}")
    except ValueError as error:
        raise InvalidSessionError(f"Supabase JWT {label} is invalid.") from error


def _jwks_key_for_kid(jwks: JsonMapping, kid: str) -> JsonMapping:
    """Return the JWKS key matching a JWT key ID."""
    keys = jwks.get("keys")
    if not isinstance(keys, list):
        raise InvalidSessionError("Supabase JWKS is invalid.")
    for key in keys:
        if isinstance(key, Mapping) and key.get("kid") == kid:
            return key
    raise InvalidSessionError("Supabase JWT key ID is unknown.")


def _verify_rs256_signature(
    *,
    key: JsonMapping,
    signed_content: bytes,
    signature: bytes,
) -> None:
    """Verify an RS256 JWT signature using a JWK."""
    if key.get("kty") != "RSA":
        raise InvalidSessionError("Supabase JWKS key type is unsupported.")
    n = _int_from_jwk_part(key, "n")
    e = _int_from_jwk_part(key, "e")
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding, rsa
    except ImportError as error:
        raise InvalidSessionError(
            "cryptography is required for Supabase JWT verification."
        ) from error
    public_key = rsa.RSAPublicNumbers(e=e, n=n).public_key()
    try:
        public_key.verify(signature, signed_content, padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature as error:
        raise InvalidSessionError("Supabase JWT signature is invalid.") from error


def _int_from_jwk_part(key: JsonMapping, part: str) -> int:
    """Decode one RSA JWK integer component."""
    value = key.get(part)
    if not isinstance(value, str):
        raise InvalidSessionError("Supabase JWKS RSA key is invalid.")
    return int.from_bytes(_bytes_from_base64url(value, f"jwk_{part}"), "big")


def _numeric_claim(payload: JsonMapping, key: str) -> int:
    """Return a required numeric JWT claim."""
    value = payload.get(key)
    if not isinstance(value, int):
        raise InvalidSessionError(f"Supabase JWT missing numeric {key} claim.")
    return value


def _timestamp_seconds(now: str) -> int:
    """Return seconds for an ISO UTC timestamp."""
    if "T" not in now or not now.endswith("Z"):
        raise InvalidSessionError("JWT validation time must be an ISO UTC timestamp.")
    parsed = datetime.fromisoformat(f"{now[:-1]}+00:00")
    return int(parsed.timestamp())


def _fetch_jwks(jwks_url: str) -> JsonMapping:
    """Fetch a JWKS document without logging secrets or tokens."""
    try:
        with urlopen(jwks_url, timeout=10) as response:
            payload = json.loads(response.read().decode())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise InvalidSessionError("Supabase JWKS could not be loaded.") from error
    if not isinstance(payload, dict):
        raise InvalidSessionError("Supabase JWKS is invalid.")
    return payload

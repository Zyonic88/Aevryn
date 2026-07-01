"""Tests for production managed identity adapter boundaries."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from collections.abc import Mapping

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from aevryn.auth import (
    InvalidSessionError,
    JwtDecoder,
    ManagedIdentity,
    ManagedIdentityAuthenticationAdapter,
    SupabaseHs256JwtDecoder,
    SupabaseJwksJwtDecoder,
    SupabaseJwtVerifier,
    managed_identity_user_id,
    supabase_issuer_from_url,
)
from aevryn.persistence import InMemoryProjectRepository

NOW = "2026-06-29T00:00:00Z"
SOON = "2026-06-29T00:05:00Z"
ISSUER = "https://aevryn-dev.supabase.co/auth/v1"


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


class StaticJwtDecoder:
    """Deterministic JWT decoder for Supabase verifier tests."""

    def __init__(self, claims: Mapping[str, object]) -> None:
        self.claims = claims
        self.calls: list[tuple[str, str]] = []

    def decode(self, *, token: str, now: str) -> Mapping[str, object]:
        """Return configured claims."""
        self.calls.append((token, now))
        return self.claims


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


def test_supabase_jwt_verifier_maps_claims_to_managed_identity() -> None:
    """Supabase claims should normalize into managed identity metadata."""
    decoder: JwtDecoder = StaticJwtDecoder(
        {
            "sub": "external-user-1234",
            "email": "creator@example.com",
            "user_metadata": {"full_name": "Creator Person"},
        }
    )
    verifier = SupabaseJwtVerifier(decoder=decoder)

    identity = verifier.validate_bearer_token(token="provider-token", now=NOW)

    assert identity == ManagedIdentity(
        provider="supabase",
        subject="external-user-1234",
        email="creator@example.com",
        display_name="Creator Person",
    )


def test_supabase_jwks_decoder_verifies_rs256_token() -> None:
    """Supabase JWKS decoder should verify signature and required claims."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = signed_test_jwt(
        private_key=key,
        kid="supabase-key",
        payload={
            "iss": ISSUER,
            "aud": "authenticated",
            "sub": "external-user-1234",
            "email": "creator@example.com",
            "exp": 1_783_200_000,
            "user_metadata": {"display_name": "Creator"},
        },
    )
    decoder = SupabaseJwksJwtDecoder(
        jwks_url="https://aevryn-dev.supabase.co/auth/v1/.well-known/jwks.json",
        issuer=ISSUER,
        jwks_fetcher=lambda _url: jwks_for_key(key, kid="supabase-key"),
    )

    claims = decoder.decode(token=token, now=NOW)

    assert claims["sub"] == "external-user-1234"
    assert claims["email"] == "creator@example.com"


def test_supabase_hs256_decoder_verifies_symmetric_token() -> None:
    """Supabase HS256 decoder should verify signature and required claims."""
    token = signed_hs256_test_jwt(
        key_material="supabase-jwt-secret",
        payload={
            "iss": ISSUER,
            "aud": "authenticated",
            "sub": "external-user-1234",
            "email": "creator@example.com",
            "exp": 1_783_200_000,
            "user_metadata": {"display_name": "Creator"},
        },
    )
    key_material = "supabase-jwt-secret"
    decoder = SupabaseHs256JwtDecoder(
        jwt_secret=key_material,
        issuer=ISSUER,
    )

    claims = decoder.decode(token=token, now=NOW)

    assert claims["sub"] == "external-user-1234"
    assert claims["email"] == "creator@example.com"


def test_supabase_jwks_decoder_rejects_invalid_tokens() -> None:
    """Supabase JWKS decoder should fail closed on malformed or invalid JWTs."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    decoder = SupabaseJwksJwtDecoder(
        jwks_url="https://aevryn-dev.supabase.co/auth/v1/.well-known/jwks.json",
        issuer=ISSUER,
        jwks_fetcher=lambda _url: jwks_for_key(key, kid="supabase-key"),
    )

    with pytest.raises(InvalidSessionError, match="malformed"):
        decoder.decode(token="not-a-jwt", now=NOW)

    expired = signed_test_jwt(
        private_key=key,
        kid="supabase-key",
        payload={
            "iss": ISSUER,
            "aud": "authenticated",
            "sub": "external-user-1234",
            "email": "creator@example.com",
            "exp": 1_000,
        },
    )
    with pytest.raises(InvalidSessionError, match="expired"):
        decoder.decode(token=expired, now=NOW)

    wrong_signature = signed_test_jwt(
        private_key=other_key,
        kid="supabase-key",
        payload={
            "iss": ISSUER,
            "aud": "authenticated",
            "sub": "external-user-1234",
            "email": "creator@example.com",
            "exp": 1_783_200_000,
        },
    )
    with pytest.raises(InvalidSessionError, match="signature"):
        decoder.decode(token=wrong_signature, now=NOW)


def test_supabase_hs256_decoder_rejects_invalid_tokens() -> None:
    """Supabase HS256 decoder should fail closed on malformed or invalid JWTs."""
    key_material = "supabase-jwt-secret"
    decoder = SupabaseHs256JwtDecoder(
        jwt_secret=key_material,
        issuer=ISSUER,
    )
    wrong_signature = signed_hs256_test_jwt(
        key_material="other-secret",
        payload={
            "iss": ISSUER,
            "aud": "authenticated",
            "sub": "external-user-1234",
            "email": "creator@example.com",
            "exp": 1_783_200_000,
        },
    )
    wrong_algorithm = signed_test_jwt(
        private_key=rsa.generate_private_key(public_exponent=65537, key_size=2048),
        kid="supabase-key",
        payload={
            "iss": ISSUER,
            "aud": "authenticated",
            "sub": "external-user-1234",
            "email": "creator@example.com",
            "exp": 1_783_200_000,
        },
    )

    with pytest.raises(InvalidSessionError, match="signature"):
        decoder.decode(token=wrong_signature, now=NOW)

    with pytest.raises(InvalidSessionError, match="HS256"):
        decoder.decode(token=wrong_algorithm, now=NOW)


def test_supabase_issuer_from_url_builds_auth_issuer() -> None:
    """Supabase issuer should derive from the project URL."""
    assert (
        supabase_issuer_from_url("https://aevryn-dev.supabase.co/")
        == "https://aevryn-dev.supabase.co/auth/v1"
    )
    with pytest.raises(ValueError, match="https"):
        supabase_issuer_from_url("http://localhost:54321")


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


def signed_test_jwt(
    *,
    private_key: rsa.RSAPrivateKey,
    kid: str,
    payload: Mapping[str, object],
) -> str:
    """Return a compact RS256 JWT for tests."""
    header = {"alg": "RS256", "typ": "JWT", "kid": kid}
    header_part = base64url_json(header)
    payload_part = base64url_json(payload)
    signed_content = f"{header_part}.{payload_part}".encode()
    signature = private_key.sign(signed_content, padding.PKCS1v15(), hashes.SHA256())
    return f"{header_part}.{payload_part}.{base64url_bytes(signature)}"


def signed_hs256_test_jwt(*, key_material: str, payload: Mapping[str, object]) -> str:
    """Return a compact HS256 JWT for tests."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_part = base64url_json(header)
    payload_part = base64url_json(payload)
    signed_content = f"{header_part}.{payload_part}".encode()
    signature = hmac.new(key_material.encode(), signed_content, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{base64url_bytes(signature)}"


def jwks_for_key(private_key: rsa.RSAPrivateKey, *, kid: str) -> dict[str, object]:
    """Return a JWKS document for a test RSA key."""
    public_numbers = private_key.public_key().public_numbers()
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": kid,
                "alg": "RS256",
                "use": "sig",
                "n": base64url_int(public_numbers.n),
                "e": base64url_int(public_numbers.e),
            }
        ]
    }


def base64url_json(value: Mapping[str, object]) -> str:
    """Return base64url JSON without padding."""
    return base64url_bytes(json.dumps(value, separators=(",", ":")).encode())


def base64url_int(value: int) -> str:
    """Return one JWK integer component."""
    byte_length = (value.bit_length() + 7) // 8
    return base64url_bytes(value.to_bytes(byte_length, "big"))


def base64url_bytes(value: bytes) -> str:
    """Return base64url text without padding."""
    return base64.urlsafe_b64encode(value).decode().rstrip("=")

"""Tests for Aevryn Phase 11 security documentation gates."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_api_security_hardening_document_covers_required_controls() -> None:
    """API hardening docs should cover the Phase 11 public-beta blockers."""
    document = (ROOT / "docs" / "AEVRYN_API_SECURITY_HARDENING.md").read_text(
        encoding="utf-8"
    )

    required_terms = (
        "Stable Error Shapes",
        "Request IDs",
        "Workflow Route Protection",
        "Upload And Request-Size Boundary",
        "CORS And Browser Security Headers",
        "Production Fail-Closed Configuration",
        "Rate Limiting Strategy",
        "CSRF Posture",
        "Timeout Policy",
        "Public Beta Blockers",
        "rate_limited",
        "AEVRYN_DEPLOYMENT_ENV=production",
    )

    for term in required_terms:
        assert term in document

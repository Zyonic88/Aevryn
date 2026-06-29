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


def test_dependency_audit_document_covers_required_controls() -> None:
    """Dependency audit docs should define repeatable backend and frontend gates."""
    document = (ROOT / "docs" / "AEVRYN_DEPENDENCY_AUDIT.md").read_text(
        encoding="utf-8"
    )

    required_terms = (
        "pyproject.toml",
        "web/package-lock.json",
        "python -m pip_audit . --progress-spinner off",
        "npm audit --audit-level=high",
        "No known vulnerabilities found",
        "found 0 vulnerabilities",
        "Do not use a raw environment audit as the release signal.",
        "high or critical vulnerabilities must block release",
        "hosted dependency monitoring",
    )

    for term in required_terms:
        assert term in document


def test_static_security_scan_document_covers_required_controls() -> None:
    """Static security scan docs should define repeatable source checks."""
    document = (ROOT / "docs" / "AEVRYN_STATIC_SECURITY_SCAN.md").read_text(
        encoding="utf-8"
    )

    required_terms = (
        "python -m bandit -r src -q",
        "ruff check .",
        "mypy src",
        "npm.cmd run lint",
        "npm.cmd run build",
        "defusedxml",
        "HTTPS endpoints",
        "B310",
        "B404",
        "B603",
        "B607",
        "CI enforcement",
    )

    for term in required_terms:
        assert term in document


def test_backup_retention_document_covers_deletion_privacy_controls() -> None:
    """Backup retention docs should separate active deletion from recovery windows."""
    document = (ROOT / "docs" / "AEVRYN_BACKUP_RETENTION.md").read_text(
        encoding="utf-8"
    )

    required_terms = (
        "Backups are for recovery.",
        "not hidden story storage",
        "do not implement a separate backup system",
        "deleted story data ages out of backups",
        "Production backups must be encrypted at rest.",
        "restore access is audited",
        "maximum backup retention window",
        "removed from active Aevryn-owned storage",
        "must not be used to recreate deleted stories except for authorized disaster recovery",
        "does not use backups for training, analytics, or support browsing",
    )

    for term in required_terms:
        assert term in document

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
        "docs/AEVRYN_BACKUP_RETENTION_DECISION.md",
        "up to 30 days",
    )

    for term in required_terms:
        assert term in document


def test_backup_retention_decision_records_public_beta_candidate() -> None:
    """Backup retention decision should define the public-beta deletion wording candidate."""
    document = (ROOT / "docs" / "AEVRYN_BACKUP_RETENTION_DECISION.md").read_text(
        encoding="utf-8"
    )

    required_terms = (
        "Decision: Backup retention wording candidate",
        "Status: Provider source rechecked - owner/legal wording review pending",
        "Public beta: Blocked",
        "docs/AEVRYN_BACKUP_RETENTION_OWNER_REVIEW_2026_08_02.md",
        "docs/AEVRYN_BACKUP_RETENTION_PRODUCTION_VERIFICATION.md",
        "Official provider source review was rechecked on 2026-08-02.",
        "python -m aevryn.cli backup-retention-config-check",
        "daily database backup retention depends on plan",
        "Cloudflare R2 object retention and deletion facts were rechecked",
        "production Supabase plan retention is verified against the selected maximum window",
        "production R2 lifecycle/deletion policy is verified against the selected wording",
        "Deletion removes active product data. Backups expire on a disclosed schedule.",
        "Encrypted production backups may retain deleted data for up to 30 days.",
        "Backups are used only for authorized disaster recovery and service restoration.",
        (
            "Backups are not used for AI training, analytics, support browsing, "
            "or product exploration."
        ),
        "Active-storage deletion means Aevryn removes scoped active product data",
        "be access-limited to authorized recovery operators",
        "be used only for recovery and restore validation",
        "be used to bypass a user's deletion decision outside authorized disaster recovery",
        "Aevryn can truthfully tell users what deletion removes immediately",
    )

    for term in required_terms:
        assert term in document


def test_backup_retention_owner_review_records_source_recheck_without_beta_approval() -> None:
    """Backup retention review should narrow evidence without approving beta."""
    document = (
        ROOT / "docs" / "AEVRYN_BACKUP_RETENTION_OWNER_REVIEW_2026_08_02.md"
    ).read_text(encoding="utf-8")

    required_terms = (
        "Review: Backup retention owner/legal review",
        "Date: 2026-08-02",
        (
            "Status: Provider source rechecked - production verification tooling "
            "implemented; owner/legal wording review pending"
        ),
        "Public beta: Blocked",
        "Deletion removes active product data. Backups expire on a disclosed schedule.",
        "This is a maximum-window candidate",
        "Official provider source review was rechecked on 2026-08-02.",
        "https://supabase.com/docs/guides/platform/backups",
        "Pro 7 days",
        "Team 14 days",
        "Enterprise up to 30 days",
        "Database backups do not include Supabase Storage API objects.",
        "https://developers.cloudflare.com/r2/buckets/object-lifecycles/",
        "https://developers.cloudflare.com/r2/objects/delete-objects/",
        "Object deletion through supported R2 tools is irreversible.",
        "docs/AEVRYN_BACKUP_RETENTION_PRODUCTION_VERIFICATION.md",
        "python -m aevryn.cli backup-retention-config-check",
        "Production verification tooling",
        "isolated restore drill passed",
        "Production Supabase plan retention",
        "Production R2 lifecycle/deletion policy",
        "Attorney review",
        "owner_legal_backup_wording_review=complete",
        "public_beta_backup_wording=approved",
    )

    for term in required_terms:
        assert term in document


def test_backup_retention_production_verification_records_fail_closed_contract() -> None:
    """Production verification docs should define exact metadata-only checks."""
    document = (
        ROOT / "docs" / "AEVRYN_BACKUP_RETENTION_PRODUCTION_VERIFICATION.md"
    ).read_text(encoding="utf-8")

    required_terms = (
        "Verification: Production backup retention configuration",
        "Status: Verification tooling implemented - owner production values pending",
        "Public beta: Blocked",
        "Deletion removes active product data. Backups expire on a disclosed schedule.",
        "python -m aevryn.cli backup-retention-config-check",
        "AEVRYN_BACKUP_RETENTION_MAX_DAYS",
        "AEVRYN_SUPABASE_PLAN",
        "AEVRYN_SUPABASE_BACKUP_RETENTION_DAYS",
        "AEVRYN_R2_DELETION_POLICY",
        "secrets_printed=0",
        "ok=backup_retention_config_contract_checked",
        "declared Supabase retention exceeds the public maximum",
        "lifecycle expiration mode has no enabled lifecycle expiration rule",
        "object keys, source prose",
        "production_supabase_plan_retention=blocked_pending_owner_verification",
        "production_r2_lifecycle_policy=blocked_pending_owner_verification",
        "backup_retention_legal_review=blocked",
    )

    for term in required_terms:
        assert term in document

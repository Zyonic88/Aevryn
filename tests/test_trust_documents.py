"""Tests for Aevryn trust, legal, and platform policy documents."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_doc(relative_path: str) -> str:
    """Read a repository document."""
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_platform_trust_documents_exist_and_cover_core_principles() -> None:
    """Platform trust docs should preserve Aevryn's ownership and security promises."""
    required_documents = {
        "docs/AEVRYN_SECURITY.md": (
            "Security is architecture, not a feature.",
            "Authentication",
            "Authorization",
            "Secret Management",
            "Audit Ledger",
            "Incident Response",
            "Security Review Process",
        ),
        "docs/AEVRYN_PRIVACY.md": (
            "Uploaded manuscripts",
            "Aetherra Labs does not train models on user stories without explicit opt-in.",
            "Account Deletion",
            "Third-Party AI Providers",
            "Data Residency",
            "Internal Employee Access",
        ),
        "docs/AEVRYN_CONTENT_CLASSIFICATION.md": (
            "Aevryn is content-aware, not content-opinionated.",
            "General",
            "Teen",
            "Mature",
            "Explicit",
            "Future Moderation",
        ),
        "docs/AEVRYN_TRUST_MODEL.md": (
            "Your work belongs to you.",
            "Evidence-Backed Canon",
            "Deterministic Outputs",
            "AI Never Owns Truth",
        ),
        "docs/AEVRYN_USER_RIGHTS.md": (
            "You own it.",
            "Off by default.",
            "Opt-in only.",
            "Employees do not browse customer stories by default.",
        ),
        "docs/DATA_RETENTION_POLICY.md": (
            "Accounts",
            "Projects",
            "Uploads",
            "Snapshots",
            "Logs",
            "Audit Records",
        ),
        "docs/BACKUP_AND_RECOVERY.md": (
            "Backup Frequency",
            "Encryption",
            "Recovery Testing",
            "Disaster Recovery",
            "Restore Validation",
        ),
    }

    for relative_path, terms in required_documents.items():
        document = read_doc(relative_path)
        for term in terms:
            assert term in document, f"{term!r} missing from {relative_path}"


def test_legal_draft_documents_exist_and_require_attorney_review() -> None:
    """Legal-facing drafts should exist and clearly require legal review."""
    required_documents = {
        "docs/TERMS_OF_SERVICE.md": (
            "attorney review",
            "Acceptable Use",
            "User Responsibilities",
            "Payments",
            "Intellectual Property",
            "Warranty Disclaimer",
            "Liability Limitation",
            "Governing Law",
        ),
        "docs/PRIVACY_POLICY.md": (
            "attorney review",
            "Information Collected",
            "Cookies",
            "Analytics",
            "Uploaded Files",
            "Third-Party Processors",
            "User Rights",
            "Contact Information",
        ),
        "docs/ACCEPTABLE_USE_POLICY.md": (
            "attorney review",
            "Allowed Uses",
            "Not Allowed",
            "Mature Fiction",
            "copyright infringement",
            "malware",
            "spam",
        ),
        "docs/SECURITY_DISCLOSURE.md": (
            "Responsible disclosure",
            "Reporting Vulnerabilities",
            "Safe Harbor Intent",
            "Response Process",
            "Public contact information must be added before launch.",
        ),
    }

    for relative_path, terms in required_documents.items():
        document = read_doc(relative_path)
        for term in terms:
            assert term in document, f"{term!r} missing from {relative_path}"


def test_v2_closeout_document_separates_completion_from_public_beta() -> None:
    """V2 closeout should record product completion without approving public beta."""
    document = read_doc("docs/AEVRYN_V2_CLOSEOUT.md")

    required_terms = (
        "Version 2 product development is complete for private/internal alpha.",
        "Version 2 is not public-beta approved yet.",
        "without touching the CLI",
        "V2 Release Candidate Readiness",
        "production identity provider decision",
        "production secret manager",
        "rate limiting at the deployment edge or API gateway",
        "attorney-reviewed Terms of Service",
        "V2 Platform: Complete for private/internal alpha.",
        "Version 3: Not started.",
    )

    for term in required_terms:
        assert term in document

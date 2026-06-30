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
            "security@aevryn.ai",
            "Public contact information must be verified before launch.",
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


def test_v2_release_candidate_readiness_document_defines_public_beta_gates() -> None:
    """Release candidate readiness should define non-feature public beta gates."""
    document = read_doc("docs/AEVRYN_V2_RELEASE_CANDIDATE_READINESS.md")

    required_terms = (
        "V2 Release Candidate Readiness is the active work track.",
        "Public beta is not approved yet.",
        "Release Candidate Readiness is not Version 3.",
        "Gate 1 - Public-Facing Trust Documentation",
        "Gate 2 - Legal Review",
        "Gate 3 - Production Infrastructure",
        "Gate 4 - Security Operations",
        "Gate 5 - Backup, Recovery, And Audit",
        "Gate 6 - AI Provider And Data Use",
        "Gate 7 - Public Beta Support Readiness",
        "Gate 8 - Release Candidate Test Pass",
        "docs/AEVRYN_PRODUCTION_INFRASTRUCTURE_READINESS.md",
        "docs/AEVRYN_SECURITY_OPERATIONS_READINESS.md",
        "docs/AEVRYN_BACKUP_RECOVERY_AUDIT_READINESS.md",
        "docs/AEVRYN_AI_PROVIDER_DATA_USE_READINESS.md",
        "docs/AEVRYN_RELEASE_CANDIDATE_TEST_READINESS.md",
        "docs/AEVRYN_PRODUCTION_INFRASTRUCTURE_DECISIONS.md",
        "docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md",
        "docs/AEVRYN_PUBLIC_BETA_SETUP_CHECKLIST.md",
        "Public beta blocked.",
    )

    for term in required_terms:
        assert term in document


def test_public_beta_setup_checklist_tracks_external_blockers() -> None:
    """Public beta setup checklist should consolidate non-repository blockers."""
    document = read_doc("docs/AEVRYN_PUBLIC_BETA_SETUP_CHECKLIST.md")

    required_terms = (
        "Checklist: Public Beta External Setup",
        "Status: Not complete",
        "Public beta: Blocked",
        "Public beta requires verified operations, not remembered intentions.",
        "Product Contact Aliases",
        "support@aevryn.ai",
        "privacy@aevryn.ai",
        "security@aevryn.ai",
        "abuse@aevryn.ai",
        "GitHub Branch Protection And Hosted Security Controls",
        "Production Provider And Data-Use Review",
        "Backup, Retention, Restore, And Audit",
        "Production-Like Deployment Smoke",
        "Public Trust And Legal Publication",
        "Release Candidate Run And Signoff",
        "Local production config contract passed.",
        "Release-candidate run not complete.",
        "Public beta: Blocked",
    )

    for term in required_terms:
        assert term in document


def test_public_trust_readiness_document_tracks_gate_one_blockers() -> None:
    """Gate 1 should distinguish existing drafts from public-beta-ready pages."""
    document = read_doc("docs/AEVRYN_PUBLIC_TRUST_READINESS.md")

    required_terms = (
        "Gate: Public-Facing Trust Documentation",
        "Status: Started",
        "Public beta: Blocked",
        "Public trust pages must be true, plain-language, and backed by implementation.",
        "Draft exists. Legal review required.",
        "Target contact selected. Provisioning and testing required.",
        "Support Contact",
        "Started. Target contact paths selected; provisioning and testing required.",
        "Plain-Language Requirements",
        "Truthfulness Requirements",
        "Not accepted.",
    )

    for term in required_terms:
        assert term in document


def test_public_trust_page_copy_preserves_plain_language_promises() -> None:
    """Public trust copy should be user-readable without overpromising readiness."""
    document = read_doc("docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md")

    required_terms = (
        "Your work belongs to you.",
        "Aevryn is built to understand stories, not to own them.",
        "AI does not own truth.",
        "Your stories are private by default.",
        "Aetherra Labs does not train on user stories without explicit opt-in.",
        "security@aevryn.ai",
        "privacy@aevryn.ai",
        "support@aevryn.ai",
        "abuse@aevryn.ai",
        "Please do not send full manuscripts",
        "Aevryn is content-aware, not content-opinionated.",
        "Lawful mature fiction is not automatically prohibited.",
        "Attorney safe-harbor review",
        "contact aliases must be provisioned and tested",
        "production backup retention window must be selected",
        "AI provider review must be completed",
        "without overpromising public-beta readiness",
    )

    for term in required_terms:
        assert term in document


def test_public_support_readiness_document_tracks_contact_paths() -> None:
    """Public support readiness should define privacy-preserving contact paths."""
    document = read_doc("docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md")

    required_terms = (
        "Gate: Public support and contact readiness",
        "Status: Started",
        "Public beta: Blocked",
        "Users must be able to get help without exposing manuscripts unnecessarily.",
        "general support",
        "privacy questions",
        "security vulnerability reports",
        "abuse reports",
        "account deletion requests",
        "support@aevryn.ai",
        "privacy@aevryn.ai",
        "security@aevryn.ai",
        "abuse@aevryn.ai",
        "source-prose redaction guidance",
        "Support should not ask for full source prose by default.",
    )

    for term in required_terms:
        assert term in document


def test_public_contacts_document_tracks_product_domain_aliases() -> None:
    """Public contacts should define product-domain aliases without approving beta."""
    document = read_doc("docs/AEVRYN_PUBLIC_CONTACTS.md")

    required_terms = (
        "aevryn.ai",
        "Aetherra Labs is the operator identity.",
        "aevryn.dev",
        "aevryn.io",
        "aetherra.ai",
        "aetherra.dev",
        "support@aevryn.ai",
        "privacy@aevryn.ai",
        "security@aevryn.ai",
        "abuse@aevryn.ai",
        "full manuscripts",
        "screenshots containing private story text",
        "enable MFA for mailbox/admin access",
        "provisioned and tested before public beta",
    )

    for term in required_terms:
        assert term in document


def test_production_infrastructure_readiness_document_tracks_gate_three() -> None:
    """Gate 3 should block public beta on concrete production infrastructure decisions."""
    document = read_doc("docs/AEVRYN_PRODUCTION_INFRASTRUCTURE_READINESS.md")

    required_terms = (
        "Gate: Production Infrastructure",
        "Status: Started",
        "Public beta: Blocked",
        "Production infrastructure must fail closed and preserve story privacy by default.",
        "production database",
        "production object storage",
        "production identity provider",
        "production secret manager",
        "HTTPS and HSTS edge policy",
        "domain and DNS strategy",
        "local JSON storage",
        "local source-byte storage",
        "production-like deployment smoke test passes",
        "docs/AEVRYN_PRODUCTION_INFRASTRUCTURE_DECISIONS.md",
        "metadata-only",
        "Managed PostgreSQL is approved as the production Project Database target.",
        "Decision 2 - Object Storage",
        "`aevryn production-config-check` verifies the production startup contract",
        "startup_contract=ready",
    )

    for term in required_terms:
        assert term in document


def test_production_infrastructure_decisions_document_records_proposed_architecture() -> None:
    """Gate 3 decisions should track approved and remaining production architecture."""
    document = read_doc("docs/AEVRYN_PRODUCTION_INFRASTRUCTURE_DECISIONS.md")

    required_terms = (
        "Decision status: Decisions 1-2 approved",
        "Owner approval: Decisions 1-2 approved",
        (
            "Implementation status: Decisions 1-2 implemented; "
            "Decisions 3-8 fail-closed contract started"
        ),
        "Public beta: Blocked",
        "managed PostgreSQL",
        "private S3-compatible storage-reference model",
        "Supabase Auth",
        "managed deployment secrets",
        "separate API and worker runtimes",
        "HTTPS only with HSTS",
        "Production deployment must fail closed if local-only adapters are selected accidentally.",
        "AEVRYN_PROJECT_DATABASE_ADAPTER=postgresql",
        "Production mode rejects AEVRYN_PROJECT_DATABASE_PATH",
        "PostgreSQL Project Database adapter is implemented",
        "Local PostgreSQL browser/API smoke passed",
        "Cloudflare R2 storage adapter is implemented",
        "Storage owns bytes. Database owns references. Engine owns meaning.",
        "Generated export storage service writes bytes through StorageService",
        "Generated export API/download routes are implemented.",
        "`aevryn production-config-check` verifies production startup configuration",
        "startup_contract=ready",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_IDENTITY_PROVIDER=managed.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_IDENTITY_PROVIDER_NAME=supabase.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_SUPABASE_URL.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_SUPABASE_JWKS_URL.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_SUPABASE_ANON_KEY.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_SUPABASE_SERVICE_ROLE_KEY.",
        "Provider-neutral ManagedIdentityVerifier boundary is implemented.",
        "ManagedIdentityAuthenticationAdapter maps verified provider identities",
        "Supabase RS256 JWT/JWKS verification adapter is implemented.",
        "Production app factory wiring is implemented.",
        "Production-like smoke execution remains open.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_SESSION_AUTHORITY=bearer.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_SECRET_MANAGER=deployment.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_PASSWORD_RESET_ENABLED=true.",
        (
            "AEVRYN_DEPLOYMENT_ENV=production requires "
            "AEVRYN_ACCOUNT_DELETION_HANDOFF_CONFIGURED=true."
        ),
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_ENVIRONMENT_NAME=production.",
        "AEVRYN_DEPLOYMENT_ENV=production requires HTTPS-only CORS origins.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_PUBLIC_FRONTEND_BASE_URL.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_PUBLIC_API_BASE_URL.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_HTTPS_ONLY=true.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_HSTS_ENABLED=true.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_WORKER_RUNTIME=managed.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_WORKER_QUEUE_PROVIDER=managed.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_WORKER_API_KEY.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_LOG_DESTINATION=hosted.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_MONITORING_DESTINATION=hosted.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_SECURITY_ALERTS_ENABLED=true.",
        "AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_METADATA_ONLY_LOGGING=true.",
        "Public beta remains blocked.",
        "Public beta remains blocked.",
    )

    for term in required_terms:
        assert term in document


def test_security_operations_readiness_document_tracks_gate_four() -> None:
    """Gate 4 should block public beta on hosted security operations controls."""
    document = read_doc("docs/AEVRYN_SECURITY_OPERATIONS_READINESS.md")

    required_terms = (
        "Gate: Security Operations",
        "Status: Started",
        "Public beta: Blocked",
        "Security controls must protect the release path, not just the local machine.",
        "hosted secret scanning",
        "push protection",
        "hosted dependency alerts",
        "protected branch rules",
        "required CI release gates",
        "production rate limits",
        "security monitoring alerts",
        "incident response routing",
        "metadata-only",
    )

    for term in required_terms:
        assert term in document


def test_branch_protection_document_tracks_hosted_release_controls() -> None:
    """Branch protection should define the hosted checks required before public beta."""
    document = read_doc("docs/AEVRYN_BRANCH_PROTECTION.md")

    required_terms = (
        "Public-beta code must pass protected release gates before it can reach the "
        "protected branch.",
        "master",
        "release-candidate branch",
        "Backend gates / Python 3.11",
        "Backend gates / Python 3.13",
        "Frontend gates",
        "Repository secret scan",
        "Dependency audit",
        "Static security scan",
        "pull request before merge",
        "force pushes disabled",
        "push protection",
        "dependency alerts",
        "Hosted checks and repository protections prevent unverified code",
    )

    for term in required_terms:
        assert term in document


def test_backup_recovery_audit_readiness_document_tracks_gate_five() -> None:
    """Gate 5 should block public beta on production backup and audit decisions."""
    document = read_doc("docs/AEVRYN_BACKUP_RECOVERY_AUDIT_READINESS.md")

    required_terms = (
        "Gate: Backup, Recovery, And Audit",
        "Status: Started",
        "Public beta: Blocked",
        "Recovery must not become hidden retention.",
        "backup frequency",
        "recovery point objective",
        "recovery time objective",
        "backup retention window",
        "restore test",
        "production audit storage",
        "audit retention",
        "audit access controls",
        "metadata-only",
        "tamper-evident",
    )

    for term in required_terms:
        assert term in document


def test_restore_test_plan_document_tracks_recovery_privacy_drill() -> None:
    """Restore test planning should preserve privacy and ownership boundaries."""
    document = read_doc("docs/AEVRYN_RESTORE_TEST_PLAN.md")

    required_terms = (
        "Recovery must restore service without weakening story privacy.",
        "PostgreSQL project metadata",
        "Cloudflare R2 object references",
        "staging or release-candidate environment",
        "full manuscripts",
        "machine-local paths",
        "dedicated test account",
        "disposable deleted story",
        "Confirm deleted active-storage data is unavailable.",
        "project ownership boundaries",
        "source and export storage references",
        "audit-ledger integrity checks",
        "metadata-only",
        "public beta remains blocked",
        "privacy incident",
    )

    for term in required_terms:
        assert term in document


def test_ai_provider_data_use_readiness_document_tracks_gate_six() -> None:
    """Gate 6 should block public beta on AI provider data-use decisions."""
    document = read_doc("docs/AEVRYN_AI_PROVIDER_DATA_USE_READINESS.md")

    required_terms = (
        "Gate: AI Provider And Data Use",
        "Status: Started",
        "Public beta: Blocked",
        "Users must know when story content leaves Aevryn-owned systems.",
        "provider name",
        "model family or model configuration",
        "data retention terms",
        "provider training behavior",
        "No training on user stories without explicit opt-in.",
        "Provider output is not Canon.",
        "metadata-only",
        "provider data-use disclosure",
    )

    for term in required_terms:
        assert term in document


def test_ai_provider_review_document_tracks_provider_data_use_contract() -> None:
    """Provider review should record data-use, training, and disclosure requirements."""
    document = read_doc("docs/AEVRYN_AI_PROVIDER_REVIEW.md")

    required_terms = (
        "Provider output is never Canon, and provider data use is never hidden.",
        "Provider: OpenAI",
        "Status: Internal alpha candidate only",
        "Public beta approval: Not approved",
        "AEVRYN_EXTRACTION_MODE=openai",
        "AEVRYN_OPENAI_API_KEY",
        "AEVRYN_OPENAI_MODEL",
        "data retention terms",
        "training behavior",
        "selected scene text required for extraction",
        "evidence anchor identifiers",
        "full provider prompts",
        "full provider responses",
        "No training on user stories without explicit opt-in.",
        "approved_for_public_beta",
        "blocked_pending_terms_review",
    )

    for term in required_terms:
        assert term in document


def test_release_candidate_test_readiness_document_tracks_gate_eight() -> None:
    """Gate 8 should define the repeatable release-candidate test pass."""
    document = read_doc("docs/AEVRYN_RELEASE_CANDIDATE_TEST_READINESS.md")

    required_terms = (
        "Gate: Release Candidate Test Pass",
        "Status: Started",
        "Public beta: Blocked",
        "Public beta must be repeatable, not lucky.",
        "backend tests",
        "frontend tests",
        "dependency audits",
        "repository secret scan",
        "performance regression check",
        "production-like deployment smoke test",
        "final manual alpha-to-beta pass",
        "release-candidate signoff",
        "metadata-only",
        "docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md",
    )

    for term in required_terms:
        assert term in document


def test_release_candidate_run_record_template_tracks_final_signoff() -> None:
    """Release candidate run record should capture the final public beta decision."""
    document = read_doc("docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md")

    required_terms = (
        "Record type: Release Candidate Run Template",
        "Status: Not run",
        "Public beta: Blocked",
        "Release Candidate Run ID",
        "Automated Gate Record",
        "Backend tests",
        "Repository secret scan",
        "Production config check",
        "Product Smoke Record",
        "The smoke path must not require CLI knowledge from the tester.",
        "Recovery Record",
        "Can the user continue?",
        "Privacy And Trust Record",
        "full manuscripts",
        "full provider prompts",
        "Production-Like Smoke Record",
        "Accepted Residual Risks",
        "If a risk touches story privacy",
        "Signoff",
        "Product",
        "Security",
        "Privacy",
        "Legal",
        "Operations",
        "Support",
        "Release candidate run has not been completed.",
    )

    for term in required_terms:
        assert term in document


def test_future_ideas_document_preserves_scope_boundary() -> None:
    """Future ideas should be preserved without becoming roadmap commitments."""
    document = read_doc("docs/AEVRYN_FUTURE_IDEAS.md")

    required_terms = (
        "These ideas are **not commitments**.",
        "separate from the official roadmap",
        "Future capabilities should consume Canon rather than replace it.",
        "Idea 001 - Narrative Perspective",
        "Idea 002 - Production Presets",
        "Idea 003 - Audiobook Production Engine",
        "Canon remains unchanged.",
        "Production Presets influence Presentation, Prompt generation, and Export formatting "
        "without modifying Canon.",
        "This engine consumes Canon-backed scene understanding and never modifies Canon itself.",
    )

    for term in required_terms:
        assert term in document

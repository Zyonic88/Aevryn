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
        "Version 2 product development was previously complete for private/internal alpha.",
        "Version 2 Phase 12 Language And Identity Understanding is accepted.",
        "Version 2 is not public-beta approved yet.",
        "without touching the CLI",
        "Translation Foundation",
        "Entity Resolution Foundation",
        "docs/AEVRYN_V2_PHASE_12_ACCEPTANCE.md",
        "V2 Release Candidate Readiness",
        "production identity provider decision",
        "production secret manager",
        "rate limiting at the deployment edge or API gateway",
        "attorney-reviewed Terms of Service",
        "V2 Platform: Product scope accepted after Phase 12 Language And Identity Understanding.",
        "V2 Release Candidate Readiness: Active.",
        "Version 3: Not started.",
    )

    for term in required_terms:
        assert term in document


def test_v2_release_candidate_readiness_document_defines_public_beta_gates() -> None:
    """Release candidate readiness should define non-feature public beta gates."""
    document = read_doc("docs/AEVRYN_V2_RELEASE_CANDIDATE_READINESS.md")

    required_terms = (
        "V2 product scope is accepted after Phase 12 Language And Identity Understanding.",
        "V2 Release Candidate Readiness is active.",
        "Public beta is not approved yet.",
        "Release Candidate Readiness is not Version 3.",
        "docs/AEVRYN_V2_PHASE_12_ACCEPTANCE.md",
        "Translation Foundation acceptance",
        "Entity Resolution Foundation acceptance",
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
        "docs/AEVRYN_SECURITY_ALERT_ROUTING.md",
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


def test_v2_language_identity_documents_define_required_boundaries() -> None:
    """Phase 12 docs should define translation and entity-resolution authority."""
    required_documents = {
        "docs/AEVRYN_ENTITY_RESOLUTION.md": (
            "Extraction proposes entities.",
            "Resolution determines identity.",
            "Canon decides truth.",
            "alias detection",
            "pronoun resolution",
            "confidence score",
            "surface-reference tracking",
            "Ambiguous stays ambiguous.",
        ),
        "docs/AEVRYN_TRANSLATION_ENGINE.md": (
            "Translate for meaning.",
            "Preserve canon.",
            "Never change story facts.",
            "translated scene text that still points back to original source anchors",
            "For V2 release-candidate readiness, Translation Foundation is required",
        ),
        "docs/AEVRYN_V2_PHASE_12_ACCEPTANCE.md": (
            "Language And Identity Understanding",
            "Translation preserves meaning.",
            "Resolution preserves identity.",
            "Canon decides truth.",
            "ambiguous references remain unresolved candidates",
            "no full source prose is logged",
        ),
    }

    for relative_path, terms in required_documents.items():
        document = read_doc(relative_path)
        for term in terms:
            assert term in document, f"{term!r} missing from {relative_path}"


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
        "docs/AEVRYN_ALIAS_PROVISIONING_RECORD.md",
        "docs/AEVRYN_REPLY_IDENTITY_SETUP.md",
        "docs/AEVRYN_SECURITY_ALERT_ROUTING.md",
        "GitHub Branch Protection And Hosted Security Controls",
        "Production Provider And Data-Use Review",
        "Backup, Retention, Restore, And Audit",
        "Production-Like Deployment Smoke",
        "Public Trust And Legal Publication",
        "Release Candidate Run And Signoff",
        "Cloudflare routing rules created, inbound delivery passed",
        "Cloudflare inbound DNS/routing health passed",
        "Cloudflare/Gmail MFA verified.",
        "Cloudflare Email Sending SMTP successfully sent support/privacy/security/abuse "
        "aliases to zyonic88@gmail.com.",
        "SPF/DKIM/DMARC received-message verification passed.",
        "Public-page publication remains open.",
        "Local production config contract passed.",
        "docs/AEVRYN_PRODUCTION_LIKE_SMOKE_RECORD.md",
        "2026-07-01 local smoke attempt verified fail-closed behavior",
        "2026-07-01 local production-style smoke passed",
        "docs/AEVRYN_CLOUD_RUN_DEPLOYMENT.md",
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
        "Replies should come from the specific product identity unless Aetherra Labs is "
        "intentionally speaking as the company.",
        "full manuscripts",
        "screenshots containing private story text",
        "enable MFA for mailbox/admin access",
        "docs/AEVRYN_ALIAS_PROVISIONING_RECORD.md",
        "docs/AEVRYN_REPLY_IDENTITY_SETUP.md",
        "provisioned and tested before public beta",
    )

    for term in required_terms:
        assert term in document


def test_alias_provisioning_record_tracks_contact_setup_verification() -> None:
    """Alias provisioning should record delivery, reply, MFA, and DNS status."""
    document = read_doc("docs/AEVRYN_ALIAS_PROVISIONING_RECORD.md")

    required_terms = (
        "Record: Public Contact Alias Provisioning",
        "Status: Inbound, DNS, access, outbound reply identities, and mail "
        "authentication verified",
        "Public beta: Blocked",
        "Cloudflare Email Routing",
        "Cloudflare",
        "aetherra.project@gmail.com",
        "Mailbox or forwarding model",
        "MFA enabled for admin access",
        "support@aevryn.ai",
        "privacy@aevryn.ai",
        "security@aevryn.ai",
        "abuse@aevryn.ai",
        "MX records",
        "SPF",
        "DKIM",
        "DMARC",
        "Test inbound delivery",
        "Test outbound replies",
        "Cloudflare shows Status Enabled, DNS records Enabled, 4 routing rules, "
        "1 destination, 9 received, 9 forwarded, 0 failed, and 0 rejected.",
        "Replies should come from the specific product identity unless Aetherra Labs is "
        "intentionally speaking as the company.",
        "Cloudflare MFA and Gmail MFA are enabled.",
        "Do not publish untested aliases.",
        "Cloudflare Email Routing rules are created",
        "Inbound delivery from zyonic88@gmail.com to all four aliases passed.",
        "Gmail filters route all four Aevryn aliases into their respective folders.",
        "Privacy, security, and abuse reply tests passed: Cloudflare Email Sending SMTP "
        "sent synthetic outbound tests to zyonic88@gmail.com.",
        "Outbound-specific SPF, DKIM, and DMARC received-message verification passed "
        "in Gmail.",
        "Outbound reply identity setup is tracked in docs/AEVRYN_REPLY_IDENTITY_SETUP.md.",
        "private-story redaction guidance",
    )

    for term in required_terms:
        assert term in document


def test_reply_identity_setup_document_tracks_outbound_sender_boundary() -> None:
    """Reply identity setup should separate inbound routing from trusted sending."""
    document = read_doc("docs/AEVRYN_REPLY_IDENTITY_SETUP.md")

    required_terms = (
        "Gate: Product reply identity",
        "Status: Product reply identity verified",
        "Public beta: Blocked",
        "Cloudflare Email Sending is the preferred candidate",
        "Cloudflare Email Sending SMTP has successfully sent synthetic outbound tests "
        "from `support@aevryn.ai`, `privacy@aevryn.ai`, `security@aevryn.ai`, and "
        "`abuse@aevryn.ai` to `zyonic88@gmail.com`.",
        "Replies should come from the specific product identity unless Aetherra Labs is "
        "intentionally speaking as the company.",
        "Cloudflare Email Routing",
        "support@aevryn.ai",
        "privacy@aevryn.ai",
        "security@aevryn.ai",
        "abuse@aevryn.ai",
        "Preferred Candidate - Cloudflare Email Sending",
        "Managed Business Mailbox",
        "Helpdesk With Verified Sending",
        "Gmail Send-As Bridge",
        "SPF",
        "DKIM",
        "DMARC",
        "Do not include real manuscripts",
        "SPF, DKIM, and DMARC passed in Gmail received-message details.",
        "Aevryn can receive and reply through tested product-domain identities",
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
        "docs/AEVRYN_PRODUCTION_LIKE_SMOKE_RECORD.md",
        "docs/AEVRYN_CLOUD_RUN_DEPLOYMENT.md",
        "2026-07-01 local smoke attempt verified fail-closed behavior",
        "2026-07-01 local production-style smoke passed",
        "aevryn-api-00003-9v4",
        "/v2/health returned OK",
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
        "docs/AEVRYN_SECURITY_ALERT_ROUTING.md",
        "hosted secret scanning",
        "push protection",
        "hosted dependency alerts",
        "protected branch rules",
        "required CI release gates",
        "production rate limits",
        "security monitoring alerts",
        "incident response routing",
        "Hosted alert routing runbook is documented.",
        "Synthetic GitHub-hosted alert path was tested through issue #10.",
        "Email inbox receipt from GitHub notification settings remains unverified.",
        "metadata-only",
    )

    for term in required_terms:
        assert term in document


def test_security_alert_routing_document_tracks_human_alert_paths() -> None:
    """Security alert routing should map hosted alerts to human-owned channels."""
    document = read_doc("docs/AEVRYN_SECURITY_ALERT_ROUTING.md")

    required_terms = (
        "Gate: Security Alert Routing",
        "Status: Routing runbook documented; synthetic GitHub alert path tested",
        "Public beta: Blocked",
        "Alerts must route to a responsible human without exposing private user stories.",
        "support@aevryn.ai",
        "privacy@aevryn.ai",
        "security@aevryn.ai",
        "abuse@aevryn.ai",
        "Secret scanning alert",
        "Code scanning high severity",
        "Dependabot critical or high alert",
        "Cross-user authorization failure",
        "Project or account deletion failure",
        "Metadata-Only Alert Payloads",
        "full manuscripts",
        "GitHub secret scanning",
        "GitHub CodeQL code scanning",
        "GitHub Actions release gates",
        "At least one synthetic hosted alert or equivalent notification path is tested.",
        "Synthetic Hosted Alert Drill",
        "https://github.com/Zyonic88/Aevryn/issues/10",
        "GitHub-hosted issue alert path verified with metadata-only evidence.",
        "Email inbox receipt from GitHub notification settings remains unverified.",
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
        "docs/AEVRYN_GITHUB_HOSTED_CONTROLS.md",
        "Protected-path verification drill exercised through PR #9.",
        "Direct pushes to master were blocked.",
        "Final hosted checks passed on the PR branch after fixes.",
        "Hosted checks and repository protections prevent unverified code",
    )

    for term in required_terms:
        assert term in document


def test_github_hosted_controls_document_tracks_external_settings() -> None:
    """Hosted controls should define exact GitHub settings before public beta."""
    document = read_doc("docs/AEVRYN_GITHUB_HOSTED_CONTROLS.md")

    required_terms = (
        "Gate: GitHub hosted controls",
        "Status: GitHub branch and security settings configured; protected-path drill "
        "exercised",
        "Public beta: Blocked",
        "Hosted controls must block unsafe release changes before they reach the "
        "protected branch.",
        "Backend gates / Python 3.11",
        "Backend gates / Python 3.13",
        "Frontend gates",
        "Repository secret scan",
        "Dependency audit",
        "Static security scan",
        "Require status checks to pass before merging",
        "Configured with 1 required approval",
        "Restrict deletions enabled",
        "Secret scanning",
        "Push protection",
        "Dependency graph",
        "Dependabot alerts",
        "CodeQL default setup configured",
        "Verification Drill",
        ".github/CODEOWNERS",
        ".github/dependabot.yml",
        ".github/SECURITY.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        "GitHub branch protection settings are configured for master.",
        "Bypass controls were not exposed in the current GitHub branch-rule UI.",
        "Protected-path verification drill exercised through PR #9.",
        "Direct push to `master` was blocked by GitHub branch protection.",
        "Final hosted checks passed",
        "GitHub hosted settings require the documented CI and security checks",
    )

    for term in required_terms:
        assert term in document


def test_github_support_files_exist_for_hosted_controls() -> None:
    """GitHub support files should reinforce branch protection and security intake."""
    required_documents = {
        ".github/CODEOWNERS": ("* @Zyonic88",),
        ".github/dependabot.yml": (
            "package-ecosystem: pip",
            "package-ecosystem: npm",
            "package-ecosystem: github-actions",
            "timezone: America/Denver",
        ),
        ".github/SECURITY.md": (
            "security@aevryn.ai",
            "docs/SECURITY_DISCLOSURE.md",
            "Do not include full manuscripts",
        ),
        ".github/PULL_REQUEST_TEMPLATE.md": (
            "No secrets, tokens, credentials",
            "public-beta readiness gates",
            "Residual risks or deferred external setup items are recorded.",
        ),
    }

    for relative_path, terms in required_documents.items():
        document = read_doc(relative_path)
        for term in terms:
            assert term in document, f"{term!r} missing from {relative_path}"


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
        "Record type: Release Candidate Run Record",
        "Status: Completed",
        "Internal release candidate: Signed off",
        "Public beta: Blocked",
        "rc-v2-2026-07-14-001",
        "2026-07-14",
        "db19d5b8aa2953db82d051bef9c45385f25ef728",
        "Hosted production-like environment",
        "Release Candidate Run ID",
        "Automated Gate Record",
        "Backend tests",
        "Repository secret scan",
        "Production config check",
        "Performance regression check",
        "Accepted residual risk",
        "Product Smoke Record",
        "The smoke path must not require CLI knowledge from the tester.",
        "Delete project",
        "Project data is removed from active product surfaces",
        "Recovery Record",
        "Can the user continue?",
        "Can the user continue? Yes for the checked release-candidate path.",
        "Privacy And Trust Record",
        "full manuscripts",
        "full provider prompts",
        "Provider failures",
        "Production-Like Smoke Record",
        "Worker processing",
        "Hosted ten-chapter retry succeeded",
        "Accepted Residual Risks",
        "If a risk touches story privacy",
        "Signoff",
        "Product",
        "Security",
        "Privacy",
        "Legal",
        "Operations",
        "Support",
        "Internal V2 release candidate: Signed off",
        "Public beta remains blocked by public-facing legal/trust/support publication",
        "The release-candidate pass is complete, privacy-preserving, repeatable",
    )

    for term in required_terms:
        assert term in document


def test_production_like_smoke_record_tracks_fail_closed_attempt() -> None:
    """Production-like smoke attempts should distinguish fail-closed checks from success."""
    document = read_doc("docs/AEVRYN_PRODUCTION_LIKE_SMOKE_RECORD.md")

    required_terms = (
        "Record type: Production-Like Smoke Attempt Log",
        "Status: Started",
        "Public beta: Blocked",
        "Latest attempt: 2026-07-14 hosted creator workflow retry passed",
        "Production-like smoke proves configuration and workflow safety.",
        "python -m aevryn.cli production-config-check",
        "python -m aevryn.cli project-db-smoke",
        "python -m aevryn.cli storage-smoke",
        "AEVRYN_DEPLOYMENT_ENV=production is required",
        "AEVRYN_PROJECT_DATABASE_URL is required in the process environment",
        "AEVRYN_STORAGE_PROVIDER is required in the process environment",
        "PASS for fail-closed behavior.",
        "FAIL/blocked for production-like smoke completion.",
        "No secret values were printed.",
        "No source prose was used.",
        "Local PostgreSQL And R2 Smoke",
        "deployment_env=production",
        "startup_contract=ready",
        "secrets_printed=0",
        "ok=production_config_contract_checked",
        "ok=project_database_postgresql_smoke_completed",
        "ok=storage_r2_smoke_completed",
        "Hosted Cloud Run API Health Smoke",
        "aevryn-api-00003-9v4",
        "https://aevryn-api-561437810621.us-central1.run.app",
        "/v2/health returned status OK.",
        "PASS for hosted Cloud Run API startup.",
        "Hosted Custom-Domain API Health Smoke",
        "api.aevryn.ai resolved to ghs.googlehosted.com.",
        "https://api.aevryn.ai/v2/health returned status OK.",
        "PASS for api.aevryn.ai custom-domain DNS.",
        "PASS for Google-managed certificate provisioning.",
        "PASS for custom-domain HTTPS health endpoint availability.",
        "Hosted Frontend/API Custom-Domain Smoke",
        "Frontend project: aevryn-web",
        "https://app.aevryn.ai returned HTTP OK.",
        "API CORS returned access-control-allow-origin: https://app.aevryn.ai.",
        "PASS for Cloudflare Pages custom-domain frontend availability.",
        "PASS for API CORS allowing the intended frontend origin.",
        "Hosted Browser-Flow Smoke",
        "Login page loaded.",
        "Register page loaded.",
        "Unauthenticated /dashboard access redirected to /login.",
        "Synthetic fake login stayed on /login and returned: Managed identity provider owns login.",
        "Unauthenticated GET /v2/projects returned 401 session_required.",
        "PASS for protected API route requiring bearer managed identity.",
        "BLOCKED for managed identity login completion.",
        "Hosted Managed Identity And Project Smoke",
        "managed identity login and authenticated project create/read/list passed",
        "PASS for managed identity login completion.",
        "PASS for authenticated project creation.",
        "PASS for authenticated project detail read.",
        "PASS for authenticated project list read.",
        "OPEN for import processing workflow smoke in the hosted environment.",
        "Hosted Creator Workflow Smoke Plan",
        "Project ID: project_447d9366_5a2a_4b38_8c28_ab7bf41de973.",
        "Failure summary: AI extraction timed out while reading the provider response.",
        "FINDING: Monitoring displayed latest import as aevryn_import_bundle.txt.",
        "Hosted Creator Workflow Smoke Retry",
        "Cloud Run revision after timeout hardening: aevryn-api-00021-lk7",
        "Project ID: project_30c12069_caf1_43da_b91d_de2887097e77.",
        "Final run state: succeeded.",
        (
            "Monitoring import label: latest import displayed as Chapter import, "
            "not the internal bundle filename."
        ),
        (
            "Export creation: passed. A JSON canon snapshot export was created "
            "and displayed with a download action."
        ),
        (
            "Export monitoring: export availability yes; export count 1; "
            "recent event recorded Export Created."
        ),
        "Cleanup: passed. Project deletion removed the smoke project from the dashboard",
        "PASSED for hosted import processing workflow.",
        "PASSED for export creation from the latest canon snapshot.",
        "PASSED for smoke project deletion cleanup.",
        "PASSED for internal release-candidate signoff.",
        "OPEN for public-beta approval.",
        "Hosted Log Review",
        "Sample size: 200 recent service-log lines",
        "Status: Passed with metadata-only access-log finding",
        "Request logs did not include manuscript text.",
        "Request logs did not include full AI provider responses.",
        "Request logs did not include credentials, tokens, secret values",
        "PASSED for hosted log review of the checked import, monitoring, and export smoke window.",
        "PASSED for no source prose in sampled hosted logs.",
        "AEVRYN_PROJECT_DATABASE_ADAPTER=postgresql",
        "AEVRYN_API_ALLOWED_ORIGINS",
        "Passed locally",
        (
            "hosted import processing, monitoring workflow status, hosted export "
            "creation, bounded hosted log review, smoke project cleanup, and "
            "internal release-candidate signoff have passed"
        ),
        (
            "Public beta remains blocked by public-facing legal/trust/support "
            "publication, broader observability policy, backup/restore/audit readiness, "
            "prompt-pack polish, and final public-beta approval."
        ),
    )

    for term in required_terms:
        assert term in document


def test_cloud_run_deployment_document_tracks_hosted_api_runbook() -> None:
    """Cloud Run deployment prep should preserve runtime and secret boundaries."""
    document = read_doc("docs/AEVRYN_CLOUD_RUN_DEPLOYMENT.md")
    dockerfile = read_doc("Dockerfile")
    dockerignore = read_doc(".dockerignore")

    required_terms = (
        "Deployment target: Google Cloud Run",
        "Status: Deployed - health smoke passed",
        "Public beta: Blocked",
        "Cloud Run owns API runtime. Cloudflare owns edge, DNS, R2, and email.",
        "Cloud Run Admin API",
        "Artifact Registry API",
        "Cloud Build API",
        "Secret Manager API",
        "Dockerfile",
        ".dockerignore",
        ".[platform,postgresql,object-storage,identity]",
        "python -m aevryn.cli api",
        "Cloud Run provides `PORT`.",
        "AEVRYN_PROJECT_DATABASE_ADAPTER=postgresql",
        "AEVRYN_API_ALLOWED_ORIGINS=https://app.aevryn.ai",
        "Secret-backed Cloud Run variables",
        "AEVRYN_PROJECT_DATABASE_URL",
        "AEVRYN_R2_SECRET_ACCESS_KEY",
        "AEVRYN_SUPABASE_SERVICE_ROLE_KEY",
        "Do not put secret values",
        "gcloud builds submit",
        "gcloud run deploy aevryn-api",
        "curl.exe https://YOUR_CLOUD_RUN_URL/v2/health",
        "aevryn-api-00003-9v4",
        "https://aevryn-api-561437810621.us-central1.run.app",
        "Result: /v2/health returned HTTP OK",
        "Header/status check: HTTP OK",
        "Custom-domain health smoke result:",
        "Domain: api.aevryn.ai",
        "Certificate: Google-managed certificate provisioned",
        "Result: https://api.aevryn.ai/v2/health returned HTTP OK",
        "api.aevryn.ai",
        "Hosted Cloud Run API health smoke has passed",
        "Hosted frontend/API header smoke has passed.",
        "Unauthenticated browser-route/API protection checks have passed.",
        "Cloudflare Pages frontend is deployed at https://app.aevryn.ai.",
        "API CORS allows Origin https://app.aevryn.ai.",
        "Unauthenticated GET /v2/projects returns 401 session_required.",
        "Synthetic fake login returns \"Managed identity provider owns login.\"",
        "managed-identity login completion and creator workflow smoke have not passed",
    )

    for term in required_terms:
        assert term in document

    docker_terms = (
        "FROM python:3.13-slim",
        "PORT=8080",
        ".[platform,postgresql,object-storage,identity]",
        "python -m aevryn.cli api --host 0.0.0.0",
        "${AEVRYN_API_ALLOWED_ORIGINS:-https://app.aevryn.ai}",
    )

    for term in docker_terms:
        assert term in dockerfile

    ignored_terms = (
        ".env",
        ".env.*",
        ".local/",
        "runtime/",
        "snapshots/",
        "web/node_modules/",
    )

    for term in ignored_terms:
        assert term in dockerignore


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

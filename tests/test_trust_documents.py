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
            "Public contact information must be published accurately before launch.",
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
        "docs/AEVRYN_PUBLIC_SITE_PUBLICATION_PLAN.md",
        "docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md",
        "docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md",
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
        "docs/AEVRYN_BACKUP_RETENTION_DECISION.md",
        "docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md",
        "docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md",
        "GitHub Branch Protection And Hosted Security Controls",
        "Production Provider And Data-Use Review",
        "Backup, Retention, Restore, And Audit",
        "Production-Like Deployment Smoke",
        "Public Trust And Legal Publication",
        "Release Candidate Run And Signoff",
        "docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md",
        "docs/AEVRYN_OWNER_PUBLIC_REVIEW_RECORD.md",
        "docs/AEVRYN_PUBLIC_LEGAL_REVIEW_PACKET.md",
        "Cloudflare routing rules created, inbound delivery passed",
        "Cloudflare inbound DNS/routing health passed",
        "Cloudflare/Gmail MFA verified.",
        "Cloudflare Email Sending SMTP successfully sent support/privacy/security/abuse "
        "aliases to zyonic88@gmail.com.",
        "SPF/DKIM/DMARC received-message verification passed.",
        "Initial public support/trust/privacy pages are published.",
        "Support procedure owner review remains open.",
        "Public-beta backup retention wording candidate selected for owner/legal review.",
        "Public review matrix exists in `docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md`.",
        "Owner public review record exists in `docs/AEVRYN_OWNER_PUBLIC_REVIEW_RECORD.md`.",
        "Public legal review packet exists in `docs/AEVRYN_PUBLIC_LEGAL_REVIEW_PACKET.md`.",
        "Official OpenAI source review was recorded on 2026-07-24",
        "production account/project verification checklist exists",
        "Production OpenAI account/project data-control verification",
        "backup/provider verification",
        "Local production config contract passed.",
        "docs/AEVRYN_PRODUCTION_LIKE_SMOKE_RECORD.md",
        "2026-07-01 local smoke attempt verified fail-closed behavior",
        "2026-07-01 local production-style smoke passed",
        "docs/AEVRYN_CLOUD_RUN_DEPLOYMENT.md",
        "Internal release-candidate run is completed and signed off.",
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
        "Draft exists. Legal review required. Privacy contact verified.",
        "Target contact selected and tested. Attorney safe-harbor review required.",
        "Support Contact",
        "Contact paths verified. Public support page publication required.",
        "Plain-Language Requirements",
        "Truthfulness Requirements",
        "public review matrix is not complete",
        "docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md",
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
        "verified contact aliases must be published accurately",
        (
            "production backup retention window must be verified against the selected "
            "public-beta wording candidate"
        ),
        "up to 30 days",
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
        "Status: Contact paths verified; public support page published; support procedure drafted",
        "Public beta: Blocked",
        "Users must be able to get help without exposing manuscripts unnecessarily.",
        "The required aliases are provisioned and tested",
        "docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md",
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
        "Initial public support page is published at /support",
        "support procedure owner review",
    )

    for term in required_terms:
        assert term in document


def test_public_support_procedure_defines_metadata_first_triage() -> None:
    """Support procedure should protect story privacy during public support intake."""
    document = read_doc("docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md")

    required_terms = (
        "Procedure: Public support operations",
        "Status: Draft operational procedure",
        "Public beta: Blocked",
        "Support solves the issue with metadata first.",
        "support@aevryn.ai",
        "privacy@aevryn.ai",
        "security@aevryn.ai",
        "abuse@aevryn.ai",
        "If a user writes to the wrong alias, route the request internally",
        "Allowed Request Metadata",
        "import ID, run ID, export ID, or request ID",
        "Source Excerpt Exception",
        "the requested excerpt is the smallest practical excerpt",
        "Full manuscripts and full chapters are not valid default support artifacts.",
        "Initial human acknowledgment within 2 business days.",
        "metadata-first triage",
        "Aevryn can triage user support requests through verified product-domain aliases",
    )

    for term in required_terms:
        assert term in document


def test_public_site_publication_plan_maps_pages_to_sources() -> None:
    """Public site publication plan should map public pages without approving beta."""
    document = read_doc("docs/AEVRYN_PUBLIC_SITE_PUBLICATION_PLAN.md")

    required_terms = (
        "Plan: Public site publication",
        "Status: Started",
        "Public beta: Blocked",
        "Public pages must say only what Aevryn can truthfully support.",
        "/trust",
        "/privacy",
        "/security",
        "/user-rights",
        "/content",
        "/support",
        "/security/disclosure",
        "/terms",
        "/acceptable-use",
        "support@aevryn.ai",
        "privacy@aevryn.ai",
        "security@aevryn.ai",
        "abuse@aevryn.ai",
        "Implemented with verified contact details",
        "docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md",
        "docs/AEVRYN_BACKUP_RETENTION_DECISION.md",
        "docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md",
        "docs/AEVRYN_OWNER_PUBLIC_REVIEW_RECORD.md",
        "support procedure owner review",
        "No public page is approved merely because it is implemented or reachable.",
        "the public review matrix has no remaining blocked rows",
        "full manuscripts",
        "backup retention wording is verified",
        "AI provider data-use disclosure",
        "final public-beta signoff explicitly approves publication",
    )

    for term in required_terms:
        assert term in document


def test_public_review_matrix_tracks_page_level_approval_status() -> None:
    """Public-facing pages should have one review matrix before public beta."""
    document = read_doc("docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md")

    required_terms = (
        "Review: Public-facing legal, trust, support, provider, and backup wording",
        "Status: Started",
        "Public beta: Blocked",
        "Public copy must be true before it is polished.",
        "Required Review Roles",
        "Owner",
        "Legal",
        "Security",
        "Privacy",
        "Operations",
        "Provider Review",
        "docs/AEVRYN_OWNER_PUBLIC_REVIEW_RECORD.md",
        "Page Review Matrix",
        "/trust",
        "/privacy",
        "/security",
        "/user-rights",
        "/content",
        "/support",
        "/security/disclosure",
        "/terms",
        "/acceptable-use",
        "Cross-Page Consistency Checks",
        "support@aevryn.ai",
        "privacy@aevryn.ai",
        "security@aevryn.ai",
        "abuse@aevryn.ai",
        "no training on user stories without explicit opt-in",
        "active-storage deletion versus backup retention boundaries",
        "metadata-first support, monitoring, and observability",
        "Current Verified Evidence",
        "Final bounded hosted observability review: passed",
        "Restore/audit drill: passed",
        "OpenAI official source review: recorded on 2026-07-24",
        "OpenAI production account verification checklist: recorded, not complete",
        "OpenAI provider config check: passed with metadata-only output on 2026-07-17",
        "Remaining Blocking Reviews",
        "Owner public review record: created, not complete",
        "Attorney review: open",
        "Public legal review packet: prepared",
        "Provider terms and data-use review: open",
        "OpenAI production account/project data-control verification: open",
        "Backup retention public wording owner/legal review: open",
        "Support procedure owner review: open",
        "Stop Conditions",
        "legal-sensitive pages have not been owner-reviewed and attorney-reviewed",
        "provider-backed extraction is enabled without verified and published provider disclosure",
        "backup/deletion wording does not match production behavior",
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


def test_public_legal_review_packet_tracks_attorney_handoff_scope() -> None:
    """Legal review packet should consolidate legal-sensitive public beta blockers."""
    document = read_doc("docs/AEVRYN_PUBLIC_LEGAL_REVIEW_PACKET.md")

    required_terms = (
        "Review packet: Public legal review",
        "Status: Prepared for owner and attorney review",
        "Public beta: Blocked",
        "Legal copy must match product behavior.",
        "Documents Requiring Attorney Review",
        "docs/TERMS_OF_SERVICE.md",
        "docs/PRIVACY_POLICY.md",
        "docs/ACCEPTABLE_USE_POLICY.md",
        "docs/SECURITY_DISCLOSURE.md",
        "Supporting Trust Documents",
        "docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md",
        "docs/AEVRYN_BACKUP_RETENTION_DECISION.md",
        "docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md",
        "docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md",
        "docs/AEVRYN_OWNER_PUBLIC_REVIEW_RECORD.md",
        "Non-Negotiable Product Promises",
        "uploaded stories belong to their creators",
        "Aetherra Labs does not train on user stories without explicit opt-in",
        "provider output is not Canon",
        "support is metadata-first",
        "backup retention must be disclosed accurately",
        "Open Legal Decisions",
        "governing_law=blocked",
        "liability_limitation=blocked",
        "privacy_processor_list=blocked",
        "provider_disclosure=blocked",
        "backup_retention_wording=blocked",
        "public pages imply attorney review happened when it did not",
        "owner-controlled product-truth decisions tracked separately",
    )

    for term in required_terms:
        assert term in document


def test_owner_public_review_record_tracks_product_truth_decisions() -> None:
    """Owner review should be tracked separately from attorney approval."""
    document = read_doc("docs/AEVRYN_OWNER_PUBLIC_REVIEW_RECORD.md")

    required_terms = (
        "Review: Owner public-facing review",
        "Status: Not started",
        "Public beta: Blocked",
        "The owner approves product truth; counsel approves legal language.",
        "Attorney review still controls legal approval",
        "Required Source Documents",
        "docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md",
        "docs/AEVRYN_PUBLIC_LEGAL_REVIEW_PACKET.md",
        "docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md",
        "docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md",
        "docs/AEVRYN_BACKUP_RETENTION_DECISION.md",
        "docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md",
        "docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md",
        "approved_by_owner",
        "blocked_needs_attorney",
        "blocked_needs_provider_verification",
        "blocked_needs_backup_verification",
        "Owner Review Checklist",
        "Operator identity",
        "Trust promise",
        "Story ownership",
        "AI training posture",
        "Provider disclosure",
        "Backup/deletion wording",
        "Support procedure",
        "Public beta readiness",
        "Does the wording avoid promising behavior Aevryn cannot verify?",
        "provider-backed extraction is enabled without verified provider disclosure",
        "deletion wording ignores backup retention",
        "support procedures invite users to send full manuscripts by default",
        "Every owner-controlled public-facing promise has an explicit owner decision",
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


def test_public_beta_setup_tracks_production_observability_policy() -> None:
    """Public beta checklist should track hosted observability verification."""
    document = read_doc("docs/AEVRYN_PUBLIC_BETA_SETUP_CHECKLIST.md")

    required_terms = (
        "docs/AEVRYN_PRODUCTION_OBSERVABILITY_POLICY.md",
        "hosted logs and monitoring are metadata-only",
        "Production observability policy candidate selected for owner/security review.",
        "Public beta remains blocked by non-smoke readiness items.",
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
    """Gate 5 should track completed backup, recovery, and audit evidence."""
    document = read_doc("docs/AEVRYN_BACKUP_RECOVERY_AUDIT_READINESS.md")

    required_terms = (
        "Gate: Backup, Recovery, And Audit",
        "Status: Passed for public-beta readiness evidence",
        "Public beta: Not blocked by Gate 5",
        "Recovery must not become hidden retention.",
        "backup frequency",
        "recovery point objective",
        "recovery time objective",
        "backup retention window",
        "restore test",
        "docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md",
        "docs/AEVRYN_BACKUP_RESTORE_RUNBOOK.md",
        "docs/AEVRYN_RESTORE_AUDIT_DRILL_2026_07_17.md",
        "repeatable restore/audit drill record and stop conditions",
        "selected Supabase PostgreSQL and Cloudflare R2 restore procedure",
        "custom role password reset caveat",
        "restore-api-config-check",
        "AEVRYN_RESTORE_DRILL_TARGET=true",
        "AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false",
        "production_traffic_attached=false",
        "restore-drill-verify",
        "docs/AEVRYN_AUDIT_STORAGE_POLICY_DECISION.md",
        "managed PostgreSQL audit tables",
        "production audit storage",
        "audit retention",
        "audit access controls",
        "is_table_owner=false",
        "metadata-only",
        "tamper-evident",
        "source-environment restore preflight passed",
        "hosted source fixture",
        "synthetic project/story/import/run/snapshot/export evidence",
        "source restore-point candidate",
        "Gate 5 is no",
        "longer a public-beta blocker.",
        "aevryn-restore-drill-2026-07-22",
        "zemkfcbijtauvvencxyy",
        "not attached to the production Cloud Run API",
        "restored database audit verification passed through a restricted",
        "records_verified=5195",
        "private Cloud Run restore API service named",
        "aevryn-restore-config-check-pgz2r",
        "isolated restore API boundary verifier passed",
        "bounded hosted restore",
        "service/job log review sampled 47 restore service log lines",
        "no source prose",
        "no full provider payloads",
        "credentials/tokens/private URLs",
        "no storage refs or signed URLs",
        "no user email",
        "addresses, no machine-local paths",
        "no machine-local paths",
    )

    for term in required_terms:
        assert term in document


def test_audit_storage_policy_decision_selects_candidate_without_unblocking_beta() -> None:
    """Audit storage policy should select a candidate while keeping verification honest."""
    document = read_doc("docs/AEVRYN_AUDIT_STORAGE_POLICY_DECISION.md")

    required_terms = (
        "Decision: Audit storage policy candidate",
        "Status: Selected for owner/security review",
        "Public beta: Blocked",
        "Audit records explain what happened.",
        "They never preserve the private thing that happened.",
        "managed PostgreSQL audit tables",
        "Project Database environment",
        "PostgresqlAuditLedger",
        "append-only",
        "metadata-only",
        "full manuscripts",
        "full source prose",
        "full AI provider prompts",
        "full AI provider responses",
        "credentials",
        "tokens",
        "private URLs",
        "hostnames",
        "usernames",
        "machine-local paths",
        "retained for up to 1 year",
        "Deletion events may outlive deleted content",
        "hash-chain verification",
        "restore/audit drill",
        "This document selects the candidate policy.",
        "Core API and worker workflow events are wired to the configured audit writer.",
        "Public beta remains blocked until",
        "PostgreSQL audit adapter configuration is verified in hosted production",
        "worker drain completion",
        "audit access controls are configured and reviewed",
        "deletion events are verified as metadata-only",
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
        "docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md",
        "docs/AEVRYN_BACKUP_RESTORE_RUNBOOK.md",
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


def test_restore_audit_drill_record_tracks_public_beta_drill_template() -> None:
    """Restore/audit drill record should define pass/fail evidence and stop conditions."""
    document = read_doc("docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md")

    required_terms = (
        "Record type: Restore and audit drill record",
        "Status: Template selected",
        "Public beta: Blocked",
        "docs/AEVRYN_BACKUP_RESTORE_RUNBOOK.md",
        "Restore service without restoring private story exposure.",
        "Production traffic attached",
        "one disposable story that is deleted before backup capture",
        "Cross-user project/story reads fail closed",
        "Source bytes resolve only for the owner",
        "Export access resolves only for the owner",
        "Deleted story does not reappear in active product surfaces",
        "Audit integrity check passes after restore",
        "full manuscript text appears in logs",
        "full provider prompts or responses appear in logs",
        "credentials, tokens, database URLs, provider keys",
        "Any exposed secret must be rotated.",
        "Any exposed private story content must be treated as a privacy incident.",
        "Public beta remains blocked unless the final result is `passed`.",
    )

    for term in required_terms:
        assert term in document


def test_dated_restore_audit_drill_record_tracks_preflight_without_closing_gate() -> None:
    """Dated restore drill record should distinguish source preflight from restore pass."""
    document = read_doc("docs/AEVRYN_RESTORE_AUDIT_DRILL_2026_07_17.md")

    required_terms = (
        "Drill ID: restore-audit-2026-07-17-001",
        "Status: Restore/audit drill passed",
        "Source fixture: Passed",
        "Final result: passed",
        "production_config_check=passed",
        "audit_ledger_verify=passed",
        "records_verified=1375",
        "can_update=false",
        "can_delete=false",
        "can_truncate=false",
        "is_table_owner=false",
        "observability_config_check=passed",
        "storage_smoke=passed",
        "objects_created=1",
        "objects_deleted=1",
        "project_id=restore_drill_project_1acd3f86bd984a258fc04c976642131d",
        "active_story_id=restore_drill_story_1acd3f86bd984a258fc04c976642131d",
        "disposable_story_id=restore_drill_disposable_1acd3f86bd984a258fc04c976642131d",
        "import_id=restore_drill_import_1acd3f86bd984a258fc04c976642131d",
        "run_id=restore_drill_run_1acd3f86bd984a258fc04c976642131d",
        "Source fixture result: PASSED",
        "restore_drill_fixture_prepared",
        "source_restore_point_candidate_utc=2026-07-17T02:27:13Z",
        "records_verified=1413",
        "source_r2_storage_smoke=passed",
        "storage_smoke_objects_created=1",
        "storage_smoke_objects_deleted=1",
        "restore_project_name=aevryn-restore-drill-2026-07-22",
        "restore_project_ref=zemkfcbijtauvvencxyy",
        "restore_project_ref_differs_from_production=true",
        "production_cloud_run_points_to_restore_project=false",
        "cloud_run_restore_service_exists=true",
        "cloud_run_restore_service_name=aevryn-api-restore",
        "cloud_run_restore_public_access=false",
        "restore_api_authenticated_health=passed",
        "restore_api_unauthenticated_health_denied=passed",
        "restore_api_config_check=passed",
        "restore_api_config_execution=aevryn-restore-config-check-pgz2r",
        "restore_api_config_ok=restore_api_config_contract_checked",
        "restore_api_config_secrets_printed=0",
        "restore_database_audit_access_report=passed",
        "restore_database_audit_access_verify=passed",
        "restore_database_audit_ledger_verify=passed",
        "records_verified=5195",
        "ok=restore_api_config_contract_checked",
        "production_traffic_attached=false",
        "PARTIAL - restored Supabase project exists, private restore API exists, "
        "config preflight passed, and no production Cloud Run traffic is attached",
        "PASSED WITH LIMITATION - restored Supabase project name/ref recorded; "
        "provider restore-point ID not available in this record",
        "PASSED - restored database audit ledger verified 5195 records",
        "PASSED - restore API boundary verifier denied cross-user "
        "project/story/import/export access",
        "PASSED - restore API boundary verifier confirmed owner-scoped import "
        "metadata and denied cross-user source access",
        "PASSED - restore API boundary verifier confirmed owner export "
        "metadata/download and denied cross-user export access",
        "PASSED - restore API boundary verifier confirmed deleted story absence",
        "deleted_story_absent_from_product_surfaces=passed",
        "restore_drill_api_boundaries_verified=passed",
        "audit_ledger_integrity_after_restore=passed",
        "operator_broad_manuscript_access_required=false",
        "production_traffic_attached=false",
        "Restore API boundary result: PASSED",
        "Deletion-after-restore result: PASSED THROUGH ISOLATED API",
        "Metadata-only log review result: SOURCE PREFLIGHT, RESTORED DATABASE "
        "CLI OUTPUT, AND BOUNDED HOSTED RESTORE LOG REVIEW PASSED",
        "Service sampled lines: 47",
        "Job sampled lines: 11",
        "restore_logs_no_source_prose=passed",
        "restore_logs_no_full_provider_payloads=passed",
        "restore_logs_no_credentials_or_private_urls=passed",
        "restore_logs_no_storage_refs_or_signed_urls=passed",
        "restore_logs_metadata_only=passed",
        "This dated record is accepted as source-environment preflight evidence",
        "This dated restore/audit drill is accepted as complete for the restore/audit",
        "ok=restore_drill_api_boundaries_verified",
    )

    for term in required_terms:
        assert term in document


def test_backup_restore_runbook_tracks_provider_specific_restore_drill() -> None:
    """Backup/restore runbook should define provider-specific public-beta drill steps."""
    document = read_doc("docs/AEVRYN_BACKUP_RESTORE_RUNBOOK.md")

    required_terms = (
        "Runbook: Backup and restore",
        "Status: Selected for restore/audit drill execution",
        "Public beta: Blocked",
        "Supabase managed PostgreSQL",
        "Cloudflare R2 private bucket",
        "Managed PostgreSQL audit table through PostgresqlAuditLedger",
        "restore-drill-fixture",
        "restore-api-config-check",
        "restore-drill-verify",
        "AEVRYN_RESTORE_DRILL_TARGET=true",
        "AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false",
        "restore_api_config_check=passed",
        "AEVRYN_RESTORE_DRILL_BEARER_TOKEN",
        "AEVRYN_RESTORE_DRILL_OTHER_BEARER_TOKEN",
        "AEVRYN_RESTORE_DRILL_CLOUD_RUN_IDENTITY_TOKEN",
        "X-Serverless-Authorization",
        "This command does not run the restore drill and does not approve public beta.",
        "The command fails closed when pointed at `https://api.aevryn.ai`",
        "Supabase database backups do not include Storage API objects.",
        "custom database roles",
        "passwords may need to be reset after restore",
        "R2 lifecycle rules can expire objects by bucket or prefix.",
        "Objects are typically removed within 24 hours of the expiration value.",
        "Encrypted production backups may retain deleted data for up to 30 days.",
        "separate database target",
        "separate R2 bucket or prefix",
        "one disposable story deleted before the restore point is captured",
        "docs/AEVRYN_RESTRICTED_DATABASE_ROLE_RUNBOOK.md",
        "python -m aevryn.cli audit-ledger-verify",
        "python -m aevryn.cli audit-access-verify",
        "python -m aevryn.cli observability-config-check",
        "restore_drill_api_boundaries_verified=passed",
        "deleted_story_absent_from_product_surfaces=passed",
        "operator_broad_manuscript_access_required=false",
        "production_traffic_attached=false",
        "Stop Conditions",
        "Any exposed private story content must be treated as a privacy incident.",
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
        "docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md",
        "Users must know when story content leaves Aevryn-owned systems.",
        "docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md",
        "provider name",
        "model family or model configuration",
        "data retention terms",
        "provider training behavior",
        "No training on user stories without explicit opt-in.",
        "Provider output is not Canon.",
        "selected public-beta disclosure candidate",
        "metadata-only",
        "OpenAI official data-use and API data-controls review was recorded on 2026-07-24.",
        "docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md",
        "OpenAI abuse-monitoring logs may contain prompts and responses",
        "Modified Abuse Monitoring, Zero Data Retention, and data residency posture",
        "provider configuration gate passed on 2026-07-17",
        "Responses API extraction adapter now sends store=false",
        "request_storage=disabled",
        "responses_store=false",
        "ok=provider_config_contract_checked",
        "provider data-use disclosure",
    )

    for term in required_terms:
        assert term in document


def test_ai_provider_review_document_tracks_provider_data_use_contract() -> None:
    """Provider review should record data-use, training, and disclosure requirements."""
    document = read_doc("docs/AEVRYN_AI_PROVIDER_REVIEW.md")

    required_terms = (
        "Provider output is never Canon, and provider data use is never hidden.",
        "docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md",
        "docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md",
        "docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md",
        "Provider: OpenAI",
        "Status: Internal alpha candidate only",
        "Public beta approval: Not approved",
        "AEVRYN_EXTRACTION_MODE=openai",
        "AEVRYN_OPENAI_API_KEY",
        "AEVRYN_OPENAI_MODEL",
        "OpenAI Responses API",
        "store=false",
        "official OpenAI",
        "data-use and API data-controls material",
        "not used for model training by",
        "abuse-monitoring retention listed as 30 days",
        "abuse-monitoring logs",
        "application state retention is 30 days by default or when `store=true`",
        "Monitoring require approval and additional requirements",
        "data retention terms",
        "training behavior",
        "selected scene text required for extraction",
        "evidence anchor identifiers",
        "full provider prompts",
        "full provider responses",
        "No training on user stories without explicit opt-in.",
        "stateful Conversations, Assistants, Threads, Vector Stores, Files, Batches",
        "approved_for_public_beta",
        "blocked_pending_terms_review",
    )

    for term in required_terms:
        assert term in document


def test_ai_provider_disclosure_decision_records_public_beta_candidate() -> None:
    """Provider disclosure should name the candidate and keep public beta blocked."""
    document = read_doc("docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md")

    required_terms = (
        "Decision: AI provider disclosure candidate",
        "Status: Selected for owner/legal/provider review",
        "Public beta: Blocked",
        "Provider: OpenAI",
        "Use: Evidence-bounded extraction",
        "Users must know when story content leaves Aevryn-owned systems.",
        "The current provider candidate is OpenAI.",
        "selected story excerpts, scene context, evidence anchors",
        "Aevryn does not send account passwords, session tokens, API keys",
        "Provider output is not Canon.",
        "No training on user stories without explicit opt-in.",
        "Responses API extraction requests set `store=false`",
        "OpenAI abuse-monitoring logs may contain prompts and responses",
        "up to 30 days by default",
        "abuse-monitoring retention behavior is disclosed accurately",
        "production account data-control settings",
        "provider-backed extraction must remain disabled for public beta",
        "full provider prompts",
        "full provider responses",
        "final model configuration is recorded",
    )

    for term in required_terms:
        assert term in document


def test_dated_openai_provider_review_records_official_source_findings() -> None:
    """Dated OpenAI review should preserve official source facts without approval drift."""
    document = read_doc("docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md")

    required_terms = (
        "Review: OpenAI provider data-use review",
        "Date: 2026-07-24",
        "Status: Terms reviewed; production account verification still required",
        "Public beta: Blocked",
        "Provider-backed extraction must be disclosed, bounded, and fail-closed.",
        "Official Sources Reviewed",
        "https://platform.openai.com/docs/models/default-usage-policies-by-endpoint",
        "https://platform.openai.com/docs/api-reference/introduction",
        (
            "https://help.openai.com/en/articles/10306912-sharing-feedback-"
            "evaluation-and-fine-tuning-data-and-api-inputs-and-outputs-with-openai"
        ),
        (
            "API inputs and outputs are not used to train or improve OpenAI models "
            "unless the organization explicitly opts in"
        ),
        "abuse-monitoring logs may contain prompts and responses",
        "retained for up to 30 days by default",
        "`/v1/responses` as not used for training",
        "the Responses API stores application state for 30 days by default or when `store=true`",
        "Modified Abuse Monitoring and Zero Data Retention as controls that require approval",
        "OpenAI API keys stay server-side only.",
        "Responses API extraction requests keep `store=false`.",
        "Provider-backed extraction must not send",
        "Public Disclosure Candidate",
        "Required Production Account Verification",
        "data-sharing controls are not opted in for API inputs/outputs",
        "Modified Abuse Monitoring or Zero Data Retention",
        "Provider-backed extraction must remain disabled for public beta",
    )

    for term in required_terms:
        assert term in document


def test_openai_production_account_verification_keeps_provider_beta_blocked() -> None:
    """Production OpenAI verification should require real account evidence."""
    document = read_doc("docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md")

    required_terms = (
        "Verification: OpenAI production organization and project data controls",
        "Status: Not started",
        "Public beta: Blocked",
        "Verify the actual production account, not the intended policy.",
        "docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md",
        "Non-Secret Evidence Rules",
        "Forbidden evidence",
        "OpenAI API keys",
        "provider request payloads",
        "source prose from user manuscripts",
        "Production OpenAI organization identified",
        "Production OpenAI project identified",
        "Final model configuration recorded",
        "API inputs/outputs data sharing not opted in",
        "feedback/evaluation/fine-tuning data sharing disabled unless explicitly disclosed",
        "Responses API extraction sends `store=false`",
        "background mode disabled for extraction",
        "Modified Abuse Monitoring state recorded",
        "Zero Data Retention state recorded",
        "data residency state recorded",
        "python -m aevryn.cli provider-config-check",
        "request_storage=disabled",
        "responses_store=false",
        "secrets_printed=0",
        "docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md",
        "docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md",
        "docs/PRIVACY_POLICY.md",
        "OpenAI production account verification: Blocked",
        "Provider-backed extraction for public beta: Blocked",
        "Fallback: Disable provider-backed extraction for public beta",
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
        "f5c19d7e9fc6a7d25139b453590b09dbf48108bd",
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
        "Public beta remains blocked by public-facing legal/trust/support review",
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
        "Latest attempt: 2026-07-24 final bounded hosted observability review passed",
        "Production-like smoke proves configuration and workflow safety.",
        "Hosted Restricted Audit Role Verification",
        "Provider And Observability Config Gates",
        "records_verified=1338",
        "can_update=false",
        "can_delete=false",
        "can_truncate=false",
        "is_table_owner=false",
        "ok=audit_access_append_only_verified",
        "ok=provider_config_contract_checked",
        "ok=observability_config_contract_checked",
        "PASSED for provider request storage disabled posture.",
        "PASSED for hosted observability configuration metadata.",
        "Final bounded hosted observability review has passed.",
        "PASSED for least-privilege append-only audit access.",
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
        "Final Bounded Hosted Observability Review",
        "Post-deletion sample deletion_summary=http=DELETE status=204",
        "Forbidden-data scan:",
        "PASSED for final bounded hosted observability review.",
        "PASSED for project deletion observability as metadata only.",
        (
            "Project deletion succeeded, but the browser view required a refresh "
            "or tab change before the deleted project state visibly refreshed."
        ),
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
            "publication, final provider review, backup retention wording "
            "owner/legal review, prompt-pack polish, deletion refresh UX "
            "hardening, and final public-beta approval."
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
        "AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false",
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


def test_database_privilege_template_preserves_append_only_audit_contract() -> None:
    """Runtime privilege SQL should keep audit history append-only."""
    document = read_doc("docs/AEVRYN_DATABASE_PRIVILEGE_HARDENING.md")
    template = read_doc("docs/AEVRYN_POSTGRESQL_RUNTIME_PRIVILEGES.sql")
    runbook = read_doc("docs/AEVRYN_RESTRICTED_DATABASE_ROLE_RUNBOOK.md")

    required_document_terms = (
        "AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false",
        "docs/AEVRYN_POSTGRESQL_RUNTIME_PRIVILEGES.sql",
        "docs/AEVRYN_RESTRICTED_DATABASE_ROLE_RUNBOOK.md",
        "audit_ledger_records TRUNCATE: false",
        "audit_ledger_records TABLE OWNER: false",
        "is_table_owner=false",
        "transaction-scoped PostgreSQL advisory lock",
    )

    for term in required_document_terms:
        assert term in document

    required_template_terms = (
        "Replace <runtime_role> and <migration_owner> only in the reviewed execution copy.",
        "Cloud Run must use AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false.",
        'GRANT USAGE ON SCHEMA public TO "<runtime_role>";',
        'ALTER TABLE public.audit_ledger_records OWNER TO "<migration_owner>";',
        "REVOKE ALL ON TABLE public.audit_ledger_records FROM PUBLIC;",
        "public.background_jobs",
        "public.project_settings",
        'GRANT SELECT, INSERT ON TABLE public.audit_ledger_records TO "<runtime_role>";',
        (
            'REVOKE UPDATE, DELETE, TRUNCATE ON TABLE public.audit_ledger_records '
            'FROM "<runtime_role>";'
        ),
    )

    for term in required_template_terms:
        assert term in template

    required_runbook_terms = (
        "Do not use the administrative `postgres` connection string in Cloud Run.",
        "Do not use the Supabase service role key as the PostgreSQL runtime password.",
        "AEVRYN_PROJECT_DATABASE_URL",
        "AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false",
        "can_update=false",
        "can_delete=false",
        "can_truncate=false",
        "is_table_owner=false",
        "ok=audit_access_append_only_verified",
        "Do not weaken the command or tests.",
        "No source prose, credentials, storage URLs, or full AI payloads",
    )

    for term in required_runbook_terms:
        assert term in runbook

    forbidden_terms = (
        "postgresql://",
        "postgres://",
        "YOUR_",
        "aevryn_app",
    )

    for term in forbidden_terms:
        assert term not in template


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

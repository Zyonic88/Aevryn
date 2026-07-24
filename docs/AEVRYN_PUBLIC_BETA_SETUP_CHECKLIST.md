# Aevryn Public Beta Setup Checklist

> Built by **Aetherra Labs**

This checklist tracks the external setup required before Aevryn can enter public beta.

It consolidates the remaining work that cannot be completed by repository code alone.

Internal alpha is limited to Aetherra Labs owner/operator development and Codex-assisted verification. Public beta is the first milestone where outside users may be invited to upload their own work.

The combined engineering, product, operations, legal, and hardening backlog is tracked in `docs/AEVRYN_V2_REMAINING_WORK.md`.

---

# Status

```text
Checklist: Public Beta External Setup
Status: Not complete
Public beta: Blocked
```

Public beta remains blocked until each required item is completed, verified, or explicitly accepted as a residual risk in the release-candidate run record.

---

# Core Rule

```text
Public beta requires verified operations, not remembered intentions.
```

Every external setup item needs an owner, a verification step, and a recorded result.

---

# Setup Items

## 1. Product Contact Aliases

Required aliases:

* `support@aevryn.ai`
* `privacy@aevryn.ai`
* `security@aevryn.ai`
* `abuse@aevryn.ai`

Verification:

* inbound delivery works
* replies work from the intended identity
* mailbox/admin access uses MFA
* owners or recipients are documented
* public support pages include source-prose redaction guidance

Tracking docs:

* `docs/AEVRYN_PUBLIC_CONTACTS.md`
* `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`
* `docs/AEVRYN_ALIAS_PROVISIONING_RECORD.md`
* `docs/AEVRYN_REPLY_IDENTITY_SETUP.md`

Status:

```text
Cloudflare routing rules created, inbound delivery passed, Cloudflare inbound DNS/routing health passed, and Cloudflare/Gmail MFA verified. Cloudflare Email Sending SMTP successfully sent support/privacy/security/abuse aliases to zyonic88@gmail.com. SPF/DKIM/DMARC received-message verification passed. Initial public support/trust/privacy pages are published. Support procedure owner review remains open.
```

---

## 2. GitHub Branch Protection And Hosted Security Controls

Required controls:

* protected default branch
* required hosted CI checks
* repository secret scanning
* push protection
* dependency alerts
* static security scan enforcement
* narrow bypass permissions

Verification:

* required checks appear in GitHub branch protection
* a failing check blocks merge
* secret scanning and dependency alerts are enabled
* bypass permissions are reviewed
* release-candidate branch or protected path is exercised

Tracking docs:

* `docs/AEVRYN_BRANCH_PROTECTION.md`
* `docs/AEVRYN_SECURITY_OPERATIONS_READINESS.md`
* `docs/AEVRYN_GITHUB_HOSTED_CONTROLS.md`
* `docs/AEVRYN_SECURITY_ALERT_ROUTING.md`

Status:

```text
Workflows, CODEOWNERS, Dependabot configuration, GitHub security policy, pull request template, branch protection, required checks, secret scanning, push protection, dependency alerts, private vulnerability reporting, and default CodeQL are configured. Protected-path drill was exercised through PR #9 and final hosted checks passed. Hosted alert routing runbook is documented; synthetic GitHub-hosted alert path was tested through issue #10. Email inbox receipt from GitHub notification settings remains unverified.
```

---

## 3. Production Provider And Data-Use Review

Required decisions:

* provider list
* model configuration
* data retention terms
* training behavior
* abuse-monitoring behavior
* provider timeout posture
* user-facing disclosure

Verification:

* provider review is completed
* `aevryn provider-config-check` passes without printing secrets
* no-training-by-default posture is preserved
* public disclosure matches provider terms
* provider failure logging remains metadata-only
* provider-backed extraction is disabled for public beta if review is incomplete

Tracking docs:

* `docs/AEVRYN_AI_PROVIDER_REVIEW.md`
* `docs/AEVRYN_AI_PROVIDER_DATA_USE_READINESS.md`
* `docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md`
* `docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md`

Status:

```text
OpenAI is documented as an internal-alpha candidate only. Public-beta provider disclosure candidate selected for owner/legal/provider review. Hosted production-like `aevryn provider-config-check` passed with metadata-only output on 2026-07-17, including `request_storage=disabled` and `responses_store=false`. Official OpenAI source review was recorded on 2026-07-24 in `docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md`. Production OpenAI account/project data-control verification, owner/legal review, final provider disclosure approval, and public-beta approval remain open.
```

---

## 4. Backup, Retention, Restore, And Audit

Required decisions:

* backup provider
* backup frequency
* backup retention window
* restore process
* audit storage provider
* audit retention window
* audit access controls

Verification:

* restore drill is run in staging or release-candidate environment
* deleted active-storage data does not reappear in product surfaces
* audit integrity survives restore
* backup and restore logs remain metadata-only
* public deletion/backup language matches production behavior

Tracking docs:

* `docs/AEVRYN_RESTORE_TEST_PLAN.md`
* `docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md`
* `docs/AEVRYN_BACKUP_RESTORE_RUNBOOK.md`
* `docs/AEVRYN_RESTORE_AUDIT_DRILL_2026_07_17.md`
* `docs/AEVRYN_BACKUP_RECOVERY_AUDIT_READINESS.md`
* `docs/AEVRYN_BACKUP_RETENTION.md`
* `docs/AEVRYN_BACKUP_RETENTION_DECISION.md`
* `docs/AEVRYN_AUDIT_STORAGE_POLICY_DECISION.md`
* `docs/AEVRYN_DATABASE_PRIVILEGE_HARDENING.md`

Status:

```text
Restore plan, restore/audit drill record template, and provider-specific backup/restore runbook exist. Public-beta backup retention wording candidate selected for owner/legal review. Public-beta audit storage policy candidate selected for owner/security review. PostgreSQL audit adapter implementation exists. Workflow, identity, settings, access-denial, and production configuration-check failure audit events are wired when the configured audit writer is available. Audit integrity, access verification, and access-report commands exist. Hosted audit integrity verification passed with metadata-only output. Hosted audit access report and append-only access verification passed with a restricted runtime PostgreSQL role; the report showed `can_update=false`, `can_delete=false`, `can_truncate=false`, and `is_table_owner=false`. Production now requires `AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false` so schema bootstrap and migrations are separated from the runtime app role. Production backup provider verification runbook is selected. The 2026-07-17/2026-07-23 restore/audit drill passed source preflight, restored database audit verification, isolated restore API boundary verification, deleted-story verification, owner-scoped source/export verification, and bounded hosted restore log review with metadata-only evidence. Gate 5 is no longer a public-beta blocker; public-facing wording still requires owner/legal review.
```

---

## 5. Production-Like Deployment Smoke

Required checks:

* production config check passes without printing secrets
* HTTPS and CORS behavior is explicit
* managed PostgreSQL is used
* private Cloudflare R2 storage is used
* managed identity is used
* worker runtime and queue posture are production-safe
* hosted logs and monitoring are metadata-only

Verification:

* `aevryn production-config-check` reports `startup_contract=ready`
* smoke run completes outside the purely local private-alpha path
* workflow state is observable through Monitoring
* export preview works through production storage boundaries
* `aevryn observability-config-check` passes without printing secrets
* logs do not expose manuscripts, credentials, tokens, private URLs, hostnames, usernames, or machine-local paths

Tracking docs:

* `docs/AEVRYN_PRODUCTION_INFRASTRUCTURE_READINESS.md`
* `docs/AEVRYN_PRODUCTION_INFRASTRUCTURE_DECISIONS.md`
* `docs/AEVRYN_PRODUCTION_LIKE_SMOKE_RECORD.md`
* `docs/AEVRYN_CLOUD_RUN_DEPLOYMENT.md`
* `docs/AEVRYN_PRODUCTION_OBSERVABILITY_POLICY.md`
* `docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md`

Status:

```text
Local production config contract passed. 2026-07-01 local smoke attempt verified fail-closed behavior when production-like environment variables were absent. 2026-07-01 local production-style smoke passed for PostgreSQL Project Database and Cloudflare R2. Cloud Run revision aevryn-api-00003-9v4 deployed and /v2/health returned OK. api.aevryn.ai custom-domain health smoke returned OK. Frontend, managed-identity, hosted creator workflow, export creation, log review, and smoke project cleanup passed in the hosted production-like environment. Hosted production-like `aevryn observability-config-check` passed with metadata-only output on 2026-07-17. Production observability policy candidate selected for owner/security review. Final bounded hosted log review passed with metadata-only evidence on 2026-07-24. Public beta remains blocked by non-smoke readiness items.
```

---

## 6. Public Trust And Legal Publication

Required work:

* public trust page
* public privacy page
* public security page
* public user-rights page
* public content-classification page
* public support page
* public security disclosure page
* attorney review for legal-sensitive documents

Verification:

* public copy matches implementation
* legal-sensitive pages are reviewed or explicitly blocked
* contact aliases are live before publication
* pages do not overpromise deletion, backup behavior, provider behavior, employee access, or public-beta readiness

Tracking docs:

* `docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md`
* `docs/AEVRYN_PUBLIC_TRUST_READINESS.md`
* `docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md`
* `docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md`
* `docs/TERMS_OF_SERVICE.md`
* `docs/PRIVACY_POLICY.md`
* `docs/ACCEPTABLE_USE_POLICY.md`
* `docs/SECURITY_DISCLOSURE.md`

Status:

```text
Initial public pages are implemented and deployed for trust, privacy, security, user rights, content classification, support, security disclosure, terms, and acceptable use. Contact verification passed. Public-beta backup wording candidate and AI provider disclosure candidate selected. Public review matrix exists in `docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md`. Owner review, legal review, backup/provider verification, support procedure owner review, and final public-beta signoff remain open.
```

---

## 7. Release Candidate Run And Signoff

Required work:

* automated gates recorded
* product smoke recorded
* recovery checks recorded
* privacy checks recorded
* production-like smoke recorded
* limitations recorded
* residual risks accepted or resolved
* product, security, privacy, legal, operations, and support signoff recorded

Verification:

* `docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md` is completed or copied into a dated run record
* public beta decision is explicit
* blocked risks are not waived silently

Tracking docs:

* `docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md`
* `docs/AEVRYN_RELEASE_CANDIDATE_TEST_READINESS.md`

Status:

```text
Internal release-candidate run is completed and signed off. Public beta signoff remains blocked by listed residual risks.
```

---

# Public Beta Decision

Public beta remains blocked until:

* all required setup items are complete
* verification evidence is recorded
* unresolved risks are explicitly accepted
* the release-candidate run record signs off the final decision

Default decision:

```text
Public beta: Blocked
```

---

# Acceptance

This checklist is accepted when:

```text
Every external setup item needed for public beta has a verified result, and the final release-candidate record can make a truthful public-beta decision.
```

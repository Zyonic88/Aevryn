# Aevryn Public Review Matrix

> Built by **Aetherra Labs**

This document is the single public-facing review tracker for Aevryn V2 public beta.

It does not approve public beta.

---

# Status

```text
Review: Public-facing legal, trust, support, provider, and backup wording
Status: Started
Public beta: Blocked
```

Public beta remains blocked until every row below is either approved with recorded evidence or explicitly left blocked in the release-candidate run record.

---

# Core Rule

```text
Public copy must be true before it is polished.
```

No public page may promise a behavior that Aevryn cannot verify through implementation, provider terms, production configuration, or owner/legal review.

---

# Required Review Roles

| Role | Scope |
| --- | --- |
| Owner | Product intent, brand voice, public-beta readiness, contact ownership |
| Legal | Terms, privacy, acceptable use, liability, warranty, governing law, safe harbor |
| Security | vulnerability disclosure, incident response, monitoring, employee access, abuse handling |
| Privacy | user ownership, deletion, backups, provider data use, support boundaries |
| Operations | backup/restore behavior, support procedure, contact routing, hosted evidence |
| Provider Review | AI provider terms, retention, training posture, abuse monitoring, final model configuration |

One person may hold more than one role, but each role must still be reviewed explicitly.

---

# Page Review Matrix

| Public Page | Route | Source Docs | Required Review | Current State | Public-Beta Decision |
| --- | --- | --- | --- | --- | --- |
| Trust | `/trust` | `docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md`, `docs/AEVRYN_TRUST_MODEL.md` | Owner, Privacy, Security | Implemented and production-reachable; owner review pending | Blocked |
| Privacy | `/privacy` | `docs/PRIVACY_POLICY.md`, `docs/AEVRYN_PRIVACY.md`, `docs/AEVRYN_BACKUP_RETENTION_DECISION.md`, `docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md` | Owner, Legal, Privacy, Provider Review | Implemented as draft; backup/provider wording candidates selected | Blocked |
| Security | `/security` | `docs/AEVRYN_SECURITY.md`, `docs/SECURITY_DISCLOSURE.md`, `docs/AEVRYN_PRODUCTION_OBSERVABILITY_POLICY.md` | Owner, Security, Legal | Implemented as draft; hosted observability evidence passed | Blocked |
| User Rights | `/user-rights` | `docs/AEVRYN_USER_RIGHTS.md`, `docs/AEVRYN_BACKUP_RETENTION_DECISION.md` | Owner, Legal, Privacy, Operations | Implemented with backup wording candidate | Blocked |
| Content Classification | `/content` | `docs/AEVRYN_CONTENT_CLASSIFICATION.md`, `docs/ACCEPTABLE_USE_POLICY.md` | Owner, Legal, Provider Review | Implemented as draft; provider-policy review pending | Blocked |
| Support | `/support` | `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`, `docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md`, `docs/AEVRYN_PUBLIC_CONTACTS.md` | Owner, Support, Privacy, Security | Implemented with verified aliases; procedure owner review pending | Blocked |
| Security Disclosure | `/security/disclosure` | `docs/SECURITY_DISCLOSURE.md`, `docs/AEVRYN_PUBLIC_CONTACTS.md` | Owner, Security, Legal | Implemented as draft; safe-harbor review pending | Blocked |
| Terms | `/terms` | `docs/TERMS_OF_SERVICE.md` | Owner, Legal | Implemented as draft; governing law and liability language pending counsel | Blocked |
| Acceptable Use | `/acceptable-use` | `docs/ACCEPTABLE_USE_POLICY.md`, `docs/AEVRYN_CONTENT_CLASSIFICATION.md` | Owner, Legal, Provider Review | Implemented as draft; mature/explicit handling review pending | Blocked |

---

# Cross-Page Consistency Checks

Before public beta, all public pages must agree on:

* Aetherra Labs as the operator identity
* `aevryn.ai` as the product domain
* `support@aevryn.ai`, `privacy@aevryn.ai`, `security@aevryn.ai`, and `abuse@aevryn.ai` as verified contact paths
* user ownership of uploaded stories, Canon, generated outputs, and exports
* no training on user stories without explicit opt-in
* provider-backed extraction disclosure or provider-backed extraction disabled for public beta
* active-storage deletion versus backup retention boundaries
* metadata-first support, monitoring, and observability
* no request for full manuscripts, full chapters, full provider responses, credentials, tokens, private URLs, or screenshots containing private story text by default
* no claim that employees can never access data under any circumstance
* no claim that deleted data disappears instantly from all backups unless production backup behavior makes that true

---

# Current Verified Evidence

```text
Contact aliases: verified
Inbound routing: verified
Outbound product-domain sending: verified
SPF/DKIM/DMARC received-message verification: passed
Cloudflare/Gmail MFA: enabled
Hosted production-like smoke: passed
Final bounded hosted observability review: passed
Restore/audit drill: passed
Hosted audit append-only access verification: passed
```

---

# Remaining Blocking Reviews

```text
Owner review: open
Attorney review: open
Provider terms and data-use review: open
Backup retention public wording owner/legal review: open
Support procedure owner review: open
Final public-beta approval: open
```

---

# Stop Conditions

Do not approve public beta if:

* legal-sensitive pages have not been owner-reviewed and attorney-reviewed
* provider-backed extraction is enabled without verified and published provider disclosure
* backup/deletion wording does not match production behavior
* support pages ask for full manuscripts by default
* public pages claim public-beta readiness before final signoff
* public pages expose internal-only language such as release gates, local adapters, internal smoke IDs, or implementation-only diagnostics

---

# Acceptance

This matrix is accepted when:

```text
Every public-facing page has an explicit review state, required role list, source document list, cross-page consistency checks, and a public-beta decision that cannot be mistaken for approval.
```

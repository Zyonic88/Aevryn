# Aevryn Public Site Publication Plan

> Built by **Aetherra Labs**

This document turns Aevryn's public-facing trust, legal, privacy, support, and security drafts into a concrete publication plan for `aevryn.ai`.

It does not approve public beta.

---

# Status

```text
Plan: Public site publication
Status: Started
Public beta: Blocked
```

The required contact aliases are verified. The initial public pages are implemented in the browser app and reachable on the production app domain. Owner review, legal review where required, backup/provider verification, and final public-beta signoff remain open.

---

# Core Rule

```text
Public pages must say only what Aevryn can truthfully support.
```

Public copy must not convert internal intent into public promises.

---

# Required Pages

| Page | Proposed Route | Source Documents | Publication Status |
| --- | --- | --- | --- |
| Trust | `/trust` | `docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md`, `docs/AEVRYN_TRUST_MODEL.md` | Implemented; owner review pending |
| Privacy | `/privacy` | `docs/PRIVACY_POLICY.md`, `docs/AEVRYN_PRIVACY.md` | Implemented as draft; attorney review required |
| Security | `/security` | `docs/AEVRYN_SECURITY.md`, `docs/SECURITY_DISCLOSURE.md` | Implemented as draft; incident-response review required |
| User Rights | `/user-rights` | `docs/AEVRYN_USER_RIGHTS.md`, `docs/AEVRYN_BACKUP_RETENTION_DECISION.md`, `docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md` | Implemented with public-beta backup wording candidate; owner/legal review pending |
| Content Classification | `/content` | `docs/AEVRYN_CONTENT_CLASSIFICATION.md` | Implemented as draft; legal/provider-policy review required |
| Support | `/support` | `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`, `docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md`, `docs/AEVRYN_PUBLIC_CONTACTS.md` | Implemented with verified contact details; support procedure owner review pending |
| Security Disclosure | `/security/disclosure` | `docs/SECURITY_DISCLOSURE.md` | Implemented as draft; safe-harbor review required |
| Terms | `/terms` | `docs/TERMS_OF_SERVICE.md` | Implemented as draft; attorney review required |
| Acceptable Use | `/acceptable-use` | `docs/ACCEPTABLE_USE_POLICY.md` | Implemented as draft; attorney review required |

---

# Verified Contact Paths

Public pages may use these contacts because inbound routing, outbound product-domain sending, SPF, DKIM, DMARC, mailbox filtering, and MFA-protected operator access have been recorded as passed:

* `support@aevryn.ai`
* `privacy@aevryn.ai`
* `security@aevryn.ai`
* `abuse@aevryn.ai`

Contact publication must preserve the private-story redaction guidance from `docs/AEVRYN_PUBLIC_CONTACTS.md`.

---

# Required User-Facing Warnings

Support, privacy, security, and abuse pages must tell users not to send:

* full manuscripts
* full chapters
* full AI responses
* generated exports unless explicitly requested
* passwords
* API keys
* provider keys
* session tokens
* private URLs
* screenshots containing private story text
* machine-local paths

---

# Public Beta Blockers

Public beta remains blocked until:

* legal-sensitive pages receive owner and attorney review
* production backup retention wording is verified against final production backup behavior
* AI provider data-use disclosure is completed or provider-backed extraction is disabled for public beta
* support procedure owner review confirms metadata-first triage and escalation handling
* final public-beta signoff explicitly approves publication

---

# Acceptance

This plan is accepted when:

```text
The public site has a concrete page map, verified contact paths, source documents, publication blockers, and truthfulness boundaries that can guide implementation without approving public beta prematurely.
```

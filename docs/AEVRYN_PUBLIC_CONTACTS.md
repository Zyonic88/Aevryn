# Aevryn Public Contacts

> Built by **Aetherra Labs**

This document defines the target public contact paths for Aevryn public beta.

These paths must be provisioned and tested before public beta.

---

# Domain Posture

Aevryn's public product domain is:

```text
aevryn.ai
```

Aetherra Labs is the operator identity.

Aetherra Labs does not need a separate public company website before Aevryn public beta, but public Aevryn trust, legal, privacy, support, and security pages must clearly identify Aetherra Labs as the operator.

Known owned domains:

* `aevryn.ai`
* `aevryn.dev`
* `aevryn.io`
* `aetherra.ai`
* `aetherra.dev`

For public beta, user-facing Aevryn support should use `aevryn.ai` addresses.

Company-level Aetherra domains may be used later for broader company pages, press, hiring, or multi-product operations.

---

# Target Public Aliases

Before public beta, provision and test:

* `support@aevryn.ai`
* `privacy@aevryn.ai`
* `security@aevryn.ai`
* `abuse@aevryn.ai`

Optional future aliases:

* `legal@aevryn.ai`
* `billing@aevryn.ai`

Billing remains future scope unless payments are introduced.

---

# Contact Path Mapping

Use these mappings for public pages:

* General support: `support@aevryn.ai`
* Account access help: `support@aevryn.ai`
* Project deletion help: `support@aevryn.ai`
* Account deletion requests: `privacy@aevryn.ai`
* Privacy questions: `privacy@aevryn.ai`
* AI provider data-use questions: `privacy@aevryn.ai`
* Security vulnerability reports: `security@aevryn.ai`
* Suspected account compromise: `security@aevryn.ai`
* Abuse reports: `abuse@aevryn.ai`
* Copyright or rights escalation: `abuse@aevryn.ai`

If a report arrives at the wrong address, Aetherra Labs should route it internally without requiring the user to resend private story material.

---

# Reply Identity

Aevryn product contact should reply from Aevryn product identities.

Replies for Aevryn support, privacy, security, abuse, deletion, account, import, export, or story-processing issues should come from the matching `aevryn.ai` alias once reply sending is configured.

Aetherra Labs may send company-wide, legal, press, or multi-product messages from an Aetherra Labs identity. It may also send an Aevryn or Aetherra product announcement as Aetherra Labs when the message is intentionally from the company.

Core rule:

```text
Replies should come from the specific product identity unless Aetherra Labs is intentionally speaking as the company.
```

---

# User Guidance

Public contact instructions must tell users not to include:

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

Support may ask for:

* account email or user identifier
* project name or project ID
* short issue summary
* error code
* approximate time of issue
* redacted screenshots

Support should not ask for full source prose by default.

---

# Provisioning Checklist

Before public beta:

* create the target aliases
* verify inbound delivery
* verify replies send from the intended identity
* enable MFA for mailbox/admin access
* document who receives each alias
* document triage expectations
* document source-prose redaction guidance
* add contacts to Privacy Policy, Security Disclosure, support page, and trust pages

Provisioning and test results should be recorded in `docs/AEVRYN_ALIAS_PROVISIONING_RECORD.md`.

---

# Acceptance

Public contact readiness is accepted when:

```text
Aevryn users can reach Aetherra Labs through tested product-domain contact paths without being asked to expose private manuscripts by default.
```

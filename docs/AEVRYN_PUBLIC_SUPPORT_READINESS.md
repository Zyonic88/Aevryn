# Aevryn Public Support Readiness

> Built by **Aetherra Labs**

This document defines the public contact and support paths Aevryn needs before public beta.

---

# Status

```text
Gate: Public support and contact readiness
Status: Started
Public beta: Blocked
```

Aevryn target support, privacy, security, and abuse contact paths are selected for the `aevryn.ai` product domain.

The aliases still need to be provisioned, tested, and added to public pages before public beta.

---

# Core Rule

```text
Users must be able to get help without exposing manuscripts unnecessarily.
```

Support workflows must assume uploaded stories are private creative work.

---

# Required Contact Paths

Before public beta, Aevryn needs public contact paths for:

* general support
* account access help
* privacy questions
* security vulnerability reports
* abuse reports
* project deletion help
* account deletion requests
* billing questions if payments are introduced later

Each contact path must explain what users should and should not include.

Users should be told not to include full manuscripts, full chapters, full AI responses, credentials, tokens, API keys, private URLs, or machine-local paths in support requests.

Target public contact paths are defined in `docs/AEVRYN_PUBLIC_CONTACTS.md`.

Provisioning and verification are tracked in `docs/AEVRYN_ALIAS_PROVISIONING_RECORD.md`.

Target aliases:

* `support@aevryn.ai`
* `privacy@aevryn.ai`
* `security@aevryn.ai`
* `abuse@aevryn.ai`

These aliases are selected targets, not public-beta approval by themselves.

---

# Support Request Guidance

Support forms or instructions should ask for:

* account email or user identifier when needed
* project name or project ID when needed
* short issue summary
* relevant error code
* approximate time of issue
* screenshots with private story text redacted

Support should not ask for full source prose by default.

If source excerpts are required for debugging, that access must be explicit, narrow, and user-approved.

---

# Privacy Contact Path

The privacy contact path must support:

* data access questions
* export questions
* project deletion questions
* account deletion requests
* backup retention questions
* AI provider data-use questions

The public Privacy Policy must include this contact path before public beta.

Target alias:

```text
privacy@aevryn.ai
```

---

# Security Contact Path

The security contact path must support:

* vulnerability reports
* suspected account compromise
* suspected data exposure
* platform abuse that affects security

The public Security Disclosure must include this contact path before public beta.

Target alias:

```text
security@aevryn.ai
```

---

# Abuse Report Path

The abuse path must support reports of:

* platform attacks
* spam
* malware
* copyright abuse notices or escalation
* attempts to access another user's data
* prohibited content or illegal use reports

Abuse handling must not become a general-purpose way for employees to browse user stories.

Target alias:

```text
abuse@aevryn.ai
```

---

# Deletion Support

Deletion support must explain:

* how to delete a project or story in-product
* how to request help if deletion fails
* what active-storage deletion means
* what backup retention may mean after deletion
* how account deletion will be handled once available

Support responses must not promise instant deletion from all backups unless production backup architecture makes that true.

Target aliases:

```text
support@aevryn.ai
privacy@aevryn.ai
```

---

# Public Beta Blockers

Public beta remains blocked until:

* support contact path is provisioned and tested
* privacy contact path is provisioned and tested
* security report contact path is provisioned and tested
* abuse report path is provisioned and tested
* deletion/account help path is provisioned and tested
* contact paths are added to public trust/legal pages
* support instructions include source-prose redaction guidance
* security disclosure includes report intake details

Current implementation progress:

```text
Target product-domain aliases are selected in docs/AEVRYN_PUBLIC_CONTACTS.md.
Alias provisioning record exists in docs/AEVRYN_ALIAS_PROVISIONING_RECORD.md.
Alias provisioning, delivery testing, mailbox access controls, and public-page publication remain open.
```

---

# Acceptance

This readiness item is accepted when:

```text
Users can contact Aetherra Labs for support, privacy, security, abuse, and deletion help without being asked to expose private manuscripts by default.
```

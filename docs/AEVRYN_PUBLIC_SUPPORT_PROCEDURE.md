# Aevryn Public Support Procedure

> Built by **Aetherra Labs**

This document defines how Aetherra Labs handles Aevryn public support requests without exposing private story material unnecessarily.

It does not approve public beta.

---

# Status

```text
Procedure: Public support operations
Status: Draft operational procedure
Public beta: Blocked
```

The contact aliases are provisioned and tested. The first public support page is live. Public beta still requires owner review of this procedure and any legal-sensitive support wording.

---

# Core Rule

```text
Support solves the issue with metadata first.
```

Support must not request full manuscripts, full chapters, full AI responses, generated exports, credentials, tokens, private URLs, screenshots containing private story text, or machine-local paths by default.

---

# Intake Paths

Use the Aevryn product identities recorded in `docs/AEVRYN_PUBLIC_CONTACTS.md`:

* `support@aevryn.ai` for product help, account access help, import or processing issues, export issues, and project deletion help
* `privacy@aevryn.ai` for privacy questions, account deletion requests, backup retention questions, and AI provider data-use questions
* `security@aevryn.ai` for vulnerability reports, suspected account compromise, suspected data exposure, and security-impacting abuse
* `abuse@aevryn.ai` for platform abuse, spam, malware, rights escalations, illegal use reports, and attempts to access another user's data

If a user writes to the wrong alias, route the request internally without asking the user to resend private story content.

---

# Triage Categories

| Category | Primary Alias | Initial Handling |
| --- | --- | --- |
| Login or account access | `support@aevryn.ai` | Ask for account email and approximate time; do not ask for passwords or tokens. |
| Import, processing, or export issue | `support@aevryn.ai` | Ask for project ID, import/run ID if visible, error code, approximate time, and redacted screenshots. |
| Project deletion help | `support@aevryn.ai` | Confirm account ownership through the product identity flow before assisting. |
| Account deletion or privacy request | `privacy@aevryn.ai` | Confirm request scope and explain active storage versus backup retention limits. |
| Vulnerability or suspected exposure | `security@aevryn.ai` | Preserve report privately; do not request unrelated story content. |
| Abuse, spam, malware, or rights escalation | `abuse@aevryn.ai` | Capture metadata and URLs; avoid requesting full source prose. |

---

# Allowed Request Metadata

Support may ask for:

* account email or user identifier
* project name or project ID
* import ID, run ID, export ID, or request ID
* short issue summary
* visible error code or concise error message
* approximate time and timezone
* redacted screenshots
* browser name and operating system when relevant

Support must keep this information metadata-only unless the user explicitly approves a narrow source excerpt.

---

# Source Excerpt Exception

A source excerpt may be requested only when metadata is insufficient and all of the following are true:

* the issue cannot be reproduced or diagnosed from metadata, status, run IDs, logs, or redacted screenshots
* the requested excerpt is the smallest practical excerpt
* the user is told why the excerpt is needed
* the user explicitly approves sending it
* the excerpt is not copied into logs, issue trackers, or broad internal notes

Full manuscripts and full chapters are not valid default support artifacts.

---

# Response Boundaries

Support responses must not:

* promise public beta approval
* promise instant deletion from all backups unless production backup architecture makes that true
* claim legal guarantees not reviewed by counsel
* claim provider data-use behavior beyond documented provider review
* ask for passwords, API keys, provider keys, session tokens, or private URLs
* move sensitive reports into public GitHub issues or public discussion

Support responses should:

* acknowledge the request
* identify the support category
* request only the minimum needed metadata
* explain any safe workaround
* escalate privacy, security, abuse, or legal-sensitive requests to the matching alias
* keep story content private by default

---

# Beta Response Target

During public beta, Aevryn should target:

```text
Initial human acknowledgment within 2 business days.
```

This is an operational target, not a guaranteed service-level agreement.

---

# Verification

This procedure is ready for public-beta support only when:

* public support copy links to verified contact paths
* support procedure owner review confirms metadata-first triage
* support operators review the no-full-manuscripts-by-default rule
* support, privacy, security, and abuse aliases remain deliverable
* outbound replies send from the intended product identity
* privacy and deletion language matches production backup behavior
* legal-sensitive wording is reviewed before public launch

---

# Acceptance

This procedure is accepted when:

```text
Aevryn can triage user support requests through verified product-domain aliases while preserving private-story boundaries by default.
```

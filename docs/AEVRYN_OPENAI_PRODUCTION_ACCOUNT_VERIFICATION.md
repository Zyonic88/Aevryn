# Aevryn OpenAI Production Account Verification

> Built by **Aetherra Labs**

This document is the production-account verification record for OpenAI-backed
extraction.

It does not approve public beta by itself.

It does not contain secrets.

---

# Status

```text
Verification: OpenAI production organization and project data controls
Status: Not started
Public beta: Blocked
```

---

# Core Rule

```text
Verify the actual production account, not the intended policy.
```

Official OpenAI documentation explains default provider behavior. This record
must confirm that Aevryn's production OpenAI organization, project, model, and
data-control settings match the public disclosure before provider-backed
extraction is enabled for public beta.

---

# Source Review Dependency

The dated policy/source review is recorded in:

* `docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md`

That source review records official OpenAI documentation about API no-training
defaults, abuse-monitoring retention, Responses API `store=false`, Zero Data
Retention, Modified Abuse Monitoring, and API-key handling.

This document records the production account/project verification that still
must happen after the source review.

---

# Non-Secret Evidence Rules

Allowed evidence:

* production organization name or opaque identifier
* production project name or opaque identifier
* verification date
* reviewer name or role
* model name
* plain-language data-control state
* pass/fail result
* non-secret checklist notes

Forbidden evidence:

* OpenAI API keys
* OpenAI organization secrets
* provider request payloads
* provider responses
* screenshots containing secrets
* bearer tokens
* database URLs
* storage references
* source prose from user manuscripts

---

# Verification Checklist

Record one of these states for each item:

```text
verified
not_available
not_approved
not_enabled
blocked
not_applicable
```

| Item | Required Public-Beta State | Recorded State | Evidence |
| --- | --- | --- | --- |
| Production OpenAI organization identified | verified | blocked | Not recorded yet |
| Production OpenAI project identified | verified | blocked | Not recorded yet |
| Final model configuration recorded | verified | blocked | Not recorded yet |
| API inputs/outputs data sharing not opted in | verified | blocked | Not recorded yet |
| feedback/evaluation/fine-tuning data sharing disabled unless explicitly disclosed | verified | blocked | Not recorded yet |
| Responses API extraction sends `store=false` | verified | blocked | Re-run `aevryn provider-config-check` after final provider settings |
| background mode disabled for extraction | verified | blocked | Not recorded yet |
| Responses API endpoint scope confirmed | verified | blocked | Not recorded yet |
| Conversations/Assistants/Threads/Vector Stores/Files/Batches/Evals/fine-tuning out of public-beta extraction scope | verified | blocked | Not recorded yet |
| abuse-monitoring retention disclosed accurately | verified | blocked | Not recorded yet |
| Modified Abuse Monitoring state recorded | verified, not_approved, or not_available | blocked | Not recorded yet |
| Zero Data Retention state recorded | verified, not_approved, or not_available | blocked | Not recorded yet |
| data residency state recorded | verified, not_approved, or not_available | blocked | Not recorded yet |
| public Privacy Policy matches verified account/project posture | verified | blocked | Not recorded yet |
| public Trust/User Rights pages match verified account/project posture | verified | blocked | Not recorded yet |

---

# Required Commands

Run this after the final provider environment is configured:

```powershell
python -m aevryn.cli provider-config-check
```

Expected metadata-only posture:

```text
provider=openai
extraction_mode=openai
request_storage=disabled
responses_store=false
secrets_printed=0
ok=provider_config_contract_checked
```

Do not paste provider keys, request bodies, response bodies, or screenshots with
secrets into this document.

---

# Public Disclosure Match

Before public beta, the verified account/project posture must match:

* `docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md`
* `docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md`
* `docs/PRIVACY_POLICY.md`
* `docs/AEVRYN_USER_RIGHTS.md`

If those documents say OpenAI API inputs and outputs are not used for model
training by default, the production OpenAI account/project must not be opted in
to training or data sharing unless Aevryn adds explicit user opt-in and updates
the public disclosure.

If those documents say OpenAI may retain prompts and responses in
abuse-monitoring logs for up to 30 days by default, the account/project review
must either confirm that default posture or document the approved control that
changes it.

---

# Public-Beta Decision

```text
OpenAI production account verification: Blocked
Provider-backed extraction for public beta: Blocked
Fallback: Disable provider-backed extraction for public beta
```

---

# Acceptance

This verification is accepted when:

```text
Aetherra Labs has verified the actual production OpenAI organization/project
settings, recorded non-secret evidence, matched public disclosure to those
settings, and explicitly approved or disabled provider-backed extraction for
public beta.
```

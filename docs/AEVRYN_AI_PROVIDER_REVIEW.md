# Aevryn AI Provider Review

> Built by **Aetherra Labs**

This document defines the provider-by-provider review required before public beta.

It is not a provider approval by itself.

---

# Purpose

Aevryn may use third-party AI providers for evidence-bounded extraction.

Before any provider receives public user manuscripts, Aetherra Labs must review what data leaves Aevryn-owned systems, what the provider may do with it, and how users are told.

Core rule:

```text
Provider output is never Canon, and provider data use is never hidden.
```

---

# Current Candidate Provider

Current internal-alpha implementation supports:

```text
Provider: OpenAI
Mode: AEVRYN_EXTRACTION_MODE=openai
Status: Internal alpha candidate only
Public beta approval: Not approved
```

OpenAI mode requires:

* `AEVRYN_OPENAI_API_KEY`
* `AEVRYN_OPENAI_MODEL`

The default worker path remains non-provider-backed unless provider mode is explicitly configured.

The current public-beta disclosure candidate is recorded in
`docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md`.

That disclosure candidate does not approve OpenAI for public beta. It records the user-facing boundary that must be verified against provider terms and final production configuration.

---

# Provider Review Checklist

Each provider review must record:

* provider name
* product or API used
* model family or exact model configuration
* endpoint type
* account or organization configuration
* data retention terms
* training behavior
* abuse-monitoring behavior
* logging behavior
* subprocessors if applicable
* data residency or region posture if available
* timeout and retry posture
* cost and quota risk
* outage behavior
* deletion implications
* public disclosure language
* approval result

If the provider terms change, the review must be repeated before public-beta signoff.

---

# Data Sent

Provider-backed extraction may send:

* selected scene text required for extraction
* scene identifiers
* evidence anchor identifiers
* evidence anchor snippets or metadata required to validate output
* extraction instructions
* schema requirements for structured output

Aevryn should send the smallest useful story context required for accurate extraction.

Provider requests must not include:

* account passwords
* session tokens
* Aevryn API keys
* provider API keys
* unrelated projects
* unrelated stories
* support tickets
* product logs
* local machine paths

---

# Data Returned

Provider responses may contain:

* entity candidates
* relationship candidates
* fact candidates
* state-change candidates
* confidence information
* evidence references
* provider error metadata

Provider output remains a proposal.

Aevryn must validate provider output against evidence anchors before Canon Updating can accept anything.

---

# Logging Boundary

Provider-related logs, monitoring, audit records, support messages, and frontend errors must not include:

* full manuscripts
* full chapters
* full provider prompts
* full provider responses
* credentials
* tokens
* private URLs
* hostnames
* usernames
* machine-local paths

Failures should use stable machine-readable codes plus concise user-facing summaries.

---

# Training And Retention Decision

Aevryn's required public-beta posture is:

```text
No training on user stories without explicit opt-in.
```

Before a provider can be approved, the review must determine whether provider-submitted content may be:

* used for model training
* retained for abuse monitoring
* retained for debugging
* retained in logs
* shared with subprocessors
* deleted or aged out on a predictable schedule

If no-training behavior cannot be guaranteed or disclosed accurately, provider-backed extraction must remain disabled for public beta unless users explicitly opt in with plain-language consent.

---

# User Disclosure Requirements

Public user-facing disclosure must explain:

* whether provider-backed extraction is enabled
* which provider may receive story content
* what story content may be sent
* why the provider receives it
* whether the provider may retain it
* whether the provider may train on it
* whether users can disable provider-backed extraction
* what happens when provider extraction fails
* how deletion interacts with provider-submitted content

The disclosure must align with:

* `docs/AEVRYN_PRIVACY.md`
* `docs/PRIVACY_POLICY.md`
* `docs/AEVRYN_USER_RIGHTS.md`

---

# Approval States

Provider review may end in one of these states:

* `approved_for_public_beta`
* `approved_for_private_alpha_only`
* `blocked_pending_terms_review`
* `blocked_pending_disclosure`
* `blocked_pending_technical_controls`
* `rejected`

The default state is blocked.

---

# Acceptance

Provider review is accepted when:

```text
Aetherra Labs can explain exactly what provider receives story content, why it receives it, what it may do with it, and how Aevryn preserves no-training-by-default story privacy.
```

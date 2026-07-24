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

Aevryn's current OpenAI integration uses the OpenAI Responses API endpoint for
evidence-bounded extraction.

The request payload explicitly sets:

```text
store=false
```

That setting is required so Aevryn does not intentionally create persistent
provider application state for extraction requests.

The current provider review was updated on 2026-07-24 against official OpenAI
data-use and API data-controls material. The dated review record is:

* `docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md`
* `docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md`

Reviewed facts:

* OpenAI states that API inputs and outputs are not used for model training by
  default unless an organization explicitly opts in.
* OpenAI's API data-controls documentation identifies `/v1/responses` as not
  used for training, with abuse-monitoring retention listed as 30 days by
  default.
* OpenAI's API data-controls documentation states that abuse-monitoring logs
  may contain prompts and responses.
* OpenAI's API data-controls documentation states that `/v1/responses`
  application state retention is 30 days by default or when `store=true`.
* OpenAI's API data-controls documentation states that Zero Data Retention
  treats `store` as false and that Zero Data Retention/Modified Abuse
  Monitoring require approval and additional requirements.

Source URLs reviewed:

* `https://platform.openai.com/docs/models/default-usage-policies-by-endpoint`
* `https://platform.openai.com/docs/api-reference/introduction`
* `https://help.openai.com/en/articles/10306912-sharing-feedback-evaluation-and-fine-tuning-data-and-api-inputs-and-outputs-with-openai`

This review reduces uncertainty, but it does not approve OpenAI for public
beta by itself.

Public beta remains blocked until Aetherra Labs records the final production
OpenAI organization/project data-control posture, final model configuration,
account-level opt-in status, retention posture, and user-facing disclosure.

The default worker path remains non-provider-backed unless provider mode is
explicitly configured.

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

For OpenAI Responses API extraction, public-beta approval also requires:

* request payloads keep `store=false`
* background mode remains disabled unless separately reviewed
* stateful Conversations, Assistants, Threads, Vector Stores, Files, Batches,
  Evals, and fine-tuning endpoints remain out of scope unless separately
  reviewed
* organization or project data-sharing controls remain opt-out by default
* any Zero Data Retention or Modified Abuse Monitoring decision is recorded
  accurately before public disclosure
* provider logs and Aevryn logs remain metadata-only

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

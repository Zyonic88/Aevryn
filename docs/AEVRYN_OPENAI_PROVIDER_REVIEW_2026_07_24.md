# Aevryn OpenAI Provider Review - 2026-07-24

> Built by **Aetherra Labs**

This document records the dated OpenAI provider review for Aevryn V2 public-beta readiness.

It does not approve public beta by itself.

It does not replace attorney review.

---

# Status

```text
Review: OpenAI provider data-use review
Date: 2026-07-24
Status: Terms reviewed; production account verification still required
Public beta: Blocked
```

---

# Core Rule

```text
Provider-backed extraction must be disclosed, bounded, and fail-closed.
```

OpenAI output is never Canon. OpenAI output is only a candidate extraction result that Aevryn validates against uploaded-story evidence before accepting anything into Canon-backed project state.

---

# Official Sources Reviewed

The 2026-07-24 review used official OpenAI sources only:

* OpenAI API data controls: `https://platform.openai.com/docs/models/default-usage-policies-by-endpoint`
* OpenAI API reference introduction and authentication guidance: `https://platform.openai.com/docs/api-reference/introduction`
* OpenAI Help Center data-sharing controls: `https://help.openai.com/en/articles/10306912-sharing-feedback-evaluation-and-fine-tuning-data-and-api-inputs-and-outputs-with-openai`

---

# Reviewed Facts

The reviewed OpenAI sources support the following public-beta candidate posture:

* OpenAI states that API inputs and outputs are not used to train or improve OpenAI models unless the organization explicitly opts in.
* OpenAI data controls identify abuse-monitoring logs as a default API storage path.
* OpenAI data controls state that abuse-monitoring logs may contain prompts and responses and are retained for up to 30 days by default unless law requires longer retention.
* OpenAI data controls identify `/v1/responses` as not used for training.
* OpenAI data controls identify `/v1/responses` as Zero Data Retention eligible, with caveats.
* OpenAI data controls state that the Responses API stores application state for 30 days by default or when `store=true`.
* OpenAI data controls state that, when Zero Data Retention is enabled, `store` is treated as false.
* OpenAI documents Modified Abuse Monitoring and Zero Data Retention as controls that require approval and additional requirements.
* OpenAI API reference states API keys must not be exposed in browsers or client-side code.
* OpenAI API reference states request IDs can be used for troubleshooting.

---

# Aevryn Technical Posture

Current Aevryn OpenAI extraction posture:

```text
Provider: OpenAI
Endpoint family: Responses API
Mode: AEVRYN_EXTRACTION_MODE=openai
Configured hosted model: gpt-5.4-mini
Request storage: disabled
Responses store flag: false
Provider config check: passed with metadata-only output on 2026-07-17
```

Aevryn requires:

* OpenAI API keys stay server-side only.
* Browser/frontend code never receives OpenAI API keys.
* Responses API extraction requests keep `store=false`.
* Background mode remains disabled unless separately reviewed.
* stateful Conversations, Assistants, Threads, Vector Stores, Files, Batches, Evals, and fine-tuning endpoints remain out of public-beta extraction scope unless separately reviewed.
* Aevryn logs, support artifacts, monitoring, frontend errors, and audit records remain metadata-only.
* provider errors use concise user-facing summaries and stable machine codes.

---

# Data Boundary

Provider-backed extraction may send only the smallest useful story context needed for extraction, such as:

* selected source excerpts required for extraction
* scene context
* evidence anchor identifiers
* evidence anchor snippets or metadata needed to validate output
* extraction instructions
* structured-output schema requirements

Provider-backed extraction must not send:

* account passwords
* session tokens
* Aevryn API keys
* provider API keys
* unrelated projects
* unrelated stories
* support tickets
* full product logs
* local machine paths

---

# Public Disclosure Candidate

The current public disclosure can truthfully say:

```text
Aevryn may use OpenAI for evidence-bounded extraction when provider-backed processing is enabled. Aevryn sends only selected story context needed for extraction, not passwords, API keys, unrelated projects, support tickets, or product logs.

OpenAI API inputs and outputs are not used to train OpenAI models by default unless the API organization explicitly opts in. OpenAI may retain API prompts and responses in abuse-monitoring logs for up to 30 days by default unless a different approved retention control applies or law requires longer retention.

Aevryn sends Responses API extraction requests with store=false so Aevryn does not intentionally create persistent OpenAI application state for extraction requests.

OpenAI output is not Canon. Aevryn validates provider output against story evidence before accepting it into Canon-backed project state.
```

If Aetherra Labs cannot verify the production OpenAI account/project settings, provider-backed extraction must remain disabled for public beta or the public disclosure must say the review is incomplete.

---

# Required Production Account Verification

Before OpenAI-backed extraction can be approved for public beta, Aetherra Labs must record:

* production OpenAI organization name or opaque identifier
* production OpenAI project name or opaque identifier
* data-sharing controls are not opted in for API inputs/outputs unless Aevryn adds explicit user opt-in
* feedback/evaluation/fine-tuning data sharing is not enabled for Aevryn production projects unless separately disclosed
* Responses API extraction still sends `store=false`
* no background mode is used for extraction
* final model configuration is recorded
* whether Modified Abuse Monitoring or Zero Data Retention is unavailable, unapproved, approved, or enabled
* whether any data residency control is unavailable, unapproved, approved, or enabled
* public Privacy Policy and Trust pages match the verified account/project posture

Do not paste API keys, organization secrets, provider screenshots containing secrets, or raw provider payloads into this record.

---

# Public-Beta Decision

```text
OpenAI provider review: Partially complete
Public beta provider-backed extraction: Blocked pending production account verification and owner/legal approval
Fallback if not approved: Provider-backed extraction must remain disabled for public beta
```

---

# Acceptance

This record is accepted when:

```text
Aevryn can tell users exactly when OpenAI receives story content, what content is sent, what OpenAI may retain by default, how no-training-by-default is preserved, and which production account controls are active.
```

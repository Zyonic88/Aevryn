# Aevryn AI Provider Disclosure Decision

> Built by **Aetherra Labs**

This document records the public-beta disclosure candidate for third-party AI provider use.

It does not approve public beta.

It does not approve any provider for public user manuscripts by itself.

---

# Status

```text
Decision: AI provider disclosure candidate
Status: Selected for owner/legal/provider review
Public beta: Blocked
```

Current internal-alpha provider candidate:

```text
Provider: OpenAI
Use: Evidence-bounded extraction
Approval: Internal alpha only
```

---

# Core Rule

```text
Users must know when story content leaves Aevryn-owned systems.
```

Provider-backed extraction must be visible, disclosed, and fail-closed.

Aevryn must not hide provider use behind generic AI wording.

---

# Candidate Public Disclosure

For public beta, Aevryn should publish this provider disclosure unless final provider review requires stricter wording:

```text
Aevryn may use third-party AI providers for evidence-bounded extraction when provider-backed processing is enabled. The current provider candidate is OpenAI.

When provider-backed extraction runs, Aevryn may send selected story excerpts, scene context, evidence anchors, extraction instructions, and structured-output requirements needed to identify candidate characters, world items, relationships, scenes, and state changes.

Aevryn does not send account passwords, session tokens, API keys, unrelated projects, unrelated stories, full product logs, support tickets, or local machine paths to AI providers.

Provider output is not Canon. Aevryn validates provider output against evidence from the uploaded story before accepting it into Canon-backed project state.

Aetherra Labs does not train on user stories without explicit opt-in. Provider-backed extraction must remain disabled for public beta unless provider data-use terms, retention behavior, abuse-monitoring behavior, and no-training posture are reviewed, documented, and disclosed accurately.
```

---

# Data Boundary

Provider-backed extraction may send:

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

# Provider Output Boundary

Provider responses may propose:

* entity candidates
* relationship candidates
* fact candidates
* state-change candidates
* confidence information
* evidence references
* provider error metadata

Provider output is never Canon by itself.

Canon acceptance remains owned by Aevryn's evidence and Canon validation pipeline.

---

# Training And Retention Boundary

Aevryn's required posture remains:

```text
No training on user stories without explicit opt-in.
```

Before public beta, Aetherra Labs must verify and record:

* whether the selected provider trains on submitted data
* whether submitted data is retained
* whether submitted data is used for abuse monitoring
* whether submitted data is logged
* whether submitted data is shared with subprocessors
* whether a no-training configuration or agreement is active
* how provider-submitted data ages out or is deleted

If this behavior cannot be verified and disclosed accurately, provider-backed extraction must remain disabled for public beta.

---

# Failure And Logging Boundary

Provider failures must be metadata-only.

Logs, monitoring, support messages, frontend errors, and audit records must not include:

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

User-facing errors should explain the workflow state and possible next action without exposing source prose or provider payloads.

---

# Public-Beta Blockers

Public beta remains blocked until:

* final provider list is selected
* final model configuration is recorded
* provider terms are reviewed
* provider retention behavior is documented
* provider training behavior is documented
* no-training posture is preserved or provider-backed extraction is disabled
* provider disclosure is published in public privacy/trust material
* provider failure logging remains metadata-only in release-candidate smoke
* provider-backed extraction is covered by final release gates

---

# Acceptance

This decision is accepted when:

```text
Aevryn can tell users which AI provider may receive story content, what content is sent, why it is sent, what the provider may do with it, and how Aevryn preserves no-training-by-default story privacy without treating provider output as Canon truth.
```

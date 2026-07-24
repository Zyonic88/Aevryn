# Aevryn AI Provider And Data Use Readiness

> Built by **Aetherra Labs**

This document tracks V2 Release Candidate Readiness Gate 6.

Gate 6 defines what must be true before Aevryn can publicly use third-party AI providers with user manuscripts.

---

# Status

```text
Gate: AI Provider And Data Use
Status: Started
Public beta: Blocked
```

Aevryn has provider-backed extraction support for internal alpha.

Public beta still requires production provider selection, data-use review, and user-facing disclosure.

The current public-beta disclosure candidate is recorded in
`docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md`.

---

# Core Rule

```text
Users must know when story content leaves Aevryn-owned systems.
```

Provider-backed extraction must never be hidden.

Users must be told which providers can receive story content, why content is sent, what is returned, what may be retained, and whether training is involved.

---

# Current Alpha Boundary

The current alpha provider boundary is documented in `docs/AEVRYN_AI_EXTRACTION_ALPHA.md`.

Provider-by-provider public-beta review is tracked in `docs/AEVRYN_AI_PROVIDER_REVIEW.md`.

Current posture:

* external AI extraction is not the default worker path
* provider-backed extraction must be explicitly configured
* missing provider key or model configuration fails closed
* provider configuration can be checked without printing provider keys
* provider smoke tests use synthetic text only
* provider failures must not log source prose or full provider responses
* provider extraction proposes candidates; it does not own Canon truth

This does not approve provider-backed extraction for public beta.

OpenAI is currently supported as an internal-alpha candidate provider only.

The 2026-07-24 provider review checked official OpenAI data-use and API
data-controls material and recorded the current review boundary in
`docs/AEVRYN_AI_PROVIDER_REVIEW.md` and
`docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md`.

Current verified posture:

* OpenAI API inputs and outputs are not used for model training by default
  unless an organization explicitly opts in.
* OpenAI abuse-monitoring logs may contain prompts and responses and are
  retained for up to 30 days by default unless a different approved retention
  control applies or law requires longer retention.
* The configured Aevryn provider path uses the OpenAI Responses API for
  extraction.
* Aevryn sends Responses API extraction requests with `store=false`.
* Provider configuration checks remain metadata-only and do not print provider
  keys.

The hosted production-like provider configuration gate passed on 2026-07-17
with metadata-only output:

```text
deployment_env=production
provider=openai
extraction_mode=openai
model=gpt-5.4-mini
timeout_seconds=90.0
max_response_bytes=1048576
request_storage=disabled
responses_store=false
provider_review=required
public_beta=blocked_until_provider_review
secrets_printed=0
ok=provider_config_contract_checked
```

This verifies configuration posture only. It does not replace owner, legal, or
provider review.

Remaining public-beta blockers:

* final model configuration must be recorded
* production OpenAI organization/project data-control settings must be reviewed
* provider retention behavior must be disclosed accurately
* Modified Abuse Monitoring, Zero Data Retention, and data residency posture
  must be recorded as unavailable, unapproved, approved, or enabled
* user-facing privacy/trust copy must be owner/legal reviewed
* release-candidate provider failure logging must remain metadata-only
* public-beta signoff must explicitly approve or disable provider-backed
  extraction

The disclosure candidate names OpenAI as the current provider candidate, explains the data boundary, and requires provider-backed extraction to remain disabled for public beta unless no-training posture and retention behavior can be verified and disclosed accurately.

Run this metadata-only configuration check before provider smoke or public-beta signoff:

```powershell
python -m aevryn.cli provider-config-check
```

The command verifies explicit provider mode, OpenAI key presence, model,
timeout, response-size boundary, and the metadata-only `request_storage=disabled`
/ `responses_store=false` posture without printing secrets. It does not approve
provider-backed extraction for public beta and does not replace owner, legal, or
provider review.

---

# Provider Selection

Before public beta, Aevryn must select and document:

* provider name
* model family or model configuration
* endpoint type
* region or residency posture if available
* data retention terms
* provider training behavior
* provider abuse-monitoring behavior
* provider logging behavior
* provider subprocessors if applicable
* provider outage and fallback posture

If multiple providers are supported, each provider needs a separate review.

---

# Data Sent To Providers

The public disclosure must explain what may be sent, including:

* selected source excerpts required for extraction
* scene context
* evidence anchors
* extraction instructions
* metadata required to validate provider output

Aevryn should send the smallest useful story context required for accurate extraction.

Provider requests must not include account passwords, session tokens, API keys, unrelated projects, unrelated stories, local machine paths, or full product logs.

---

# Data Returned By Providers

Provider responses may include:

* entity candidates
* relationship candidates
* state-change candidates
* extraction confidence
* evidence references
* provider error information

Provider output is not Canon.

Aevryn must validate provider output against evidence anchors before accepting it into Canon-backed state.

---

# Training Posture

Aevryn's default posture remains:

```text
No training on user stories without explicit opt-in.
```

Before public beta, Aevryn must verify whether selected providers train on submitted data, retain submitted data, or use submitted data for abuse monitoring.

If provider terms allow training by default, Aevryn must either:

* disable that provider for public beta
* obtain a no-training configuration or agreement
* or disclose the behavior clearly and require explicit opt-in before use

Hidden training is not acceptable.

---

# Logging And Failure Handling

Provider failure handling must remain metadata-only.

Logs, monitoring, audit records, support messages, and frontend errors must not contain:

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

Provider errors should use concise, stable machine-readable codes and user-actionable summaries.

---

# User-Facing Disclosure

Before public beta, Aevryn must provide plain-language disclosure covering:

* whether provider-backed extraction is enabled
* what story content may be sent
* which provider receives it
* why the provider receives it
* whether the provider may retain it
* whether the provider may train on it
* whether users can disable provider-backed extraction
* what happens when provider extraction fails
* how deletion interacts with provider-submitted content

The disclosure must align with `docs/AEVRYN_PRIVACY.md` and `docs/PRIVACY_POLICY.md`.

---

# Public Beta Blockers

Public beta remains blocked until:

* provider list is selected
* model configuration is documented
* provider retention terms are reviewed
* provider training behavior is documented
* opt-in training posture is preserved
* provider failure logging is verified metadata-only
* provider timeout behavior is documented
* provider data-use disclosure is added to public privacy material
* provider configuration is covered by release gates

Current implementation progress:

```text
docs/AEVRYN_AI_PROVIDER_REVIEW.md defines the provider review checklist, OpenAI alpha-candidate status, data-sent boundary, logging boundary, training/retention decision, disclosure requirements, and approval states.
docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md records the selected public-beta disclosure candidate.
`aevryn provider-config-check` verifies provider configuration metadata, including `request_storage=disabled` and `responses_store=false`, without printing provider keys.
OpenAI official data-use and API data-controls review was recorded on 2026-07-24.
docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md records official source links, reviewed facts, technical posture, disclosure candidate, and production account verification requirements.
Aevryn's Responses API extraction adapter now sends store=false.
Hosted production-like `aevryn provider-config-check` passed with metadata-only output on 2026-07-17.
OpenAI account/project data-control verification, owner/legal review, and public-beta approval remain open.
```

---

# Acceptance

Gate 6 is accepted when:

```text
Users can understand whether story content leaves Aevryn-owned systems, which providers may receive it, what providers may do with it, and how Aevryn preserves no-training-by-default story privacy.
```

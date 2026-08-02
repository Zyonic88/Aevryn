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
Status: Official sources, Aevryn technical controls, owner dashboard review, and owner product-truth provider wording approved; legal/final signoff pending
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

On 2026-08-01, the official OpenAI source posture was rechecked against:

* OpenAI API data controls:
  `https://platform.openai.com/docs/models/default-usage-policies-by-endpoint`
* OpenAI API reference overview/authentication:
  `https://platform.openai.com/docs/api-reference/introduction`
* OpenAI Help Center data-sharing controls:
  `https://help.openai.com/en/articles/10306912-sharing-feedback-and-api-inputs-and-outputs-with-openai`

The recheck confirmed the source-level public disclosure boundary still matches
the Aevryn candidate posture:

* API inputs and outputs are not used for model training by default unless the
  organization explicitly opts in.
* API input/output sharing and evaluation/fine-tuning data sharing are disabled
  by default and can be enabled by account owners.
* `/v1/responses` is listed as not used for training.
* `/v1/responses` abuse-monitoring retention is listed as 30 days by default.
* `/v1/responses` application state is listed as none except documented
  exceptions; Aevryn additionally sends `store=false`.
* Zero Data Retention and Modified Abuse Monitoring require approval and must
  be recorded separately if enabled.
* Data residency is configured per project and must be recorded separately if
  used.
* OpenAI API keys must stay server-side and must not be exposed in browser or
  client-side code.

On 2026-08-02, the Aetherra Labs owner completed the non-secret production
OpenAI dashboard review and reported:

* production OpenAI organization confirmed
* production OpenAI project confirmed
* API key is project-scoped
* API input/output sharing is disabled
* evaluation/fine-tuning sharing is disabled
* training on user stories by default is not enabled
* production model remains `gpt-5.4-mini`

The owner could not locate Modified Abuse Monitoring, Zero Data Retention, or
data residency controls in the dashboard. Those controls are recorded as
not found by owner review and must not be represented publicly as enabled.

On 2026-08-02, final owner product-truth wording approval for provider
disclosure was recorded in:

* `docs/AEVRYN_PROVIDER_DISCLOSURE_WORDING_APPROVAL_2026_08_02.md`

This approval does not replace attorney review and does not approve public beta.

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
| Production OpenAI organization identified | verified | verified | Owner confirmed production OpenAI organization on 2026-08-02 without sharing secrets. |
| Production OpenAI project identified | verified | verified | Owner confirmed production OpenAI project on 2026-08-02 without sharing secrets. |
| Final model configuration recorded | verified | verified | Hosted production-like `aevryn provider-config-check` recorded `model=gpt-5.4-mini` on 2026-07-17; owner selected gpt-5.4-mini for current extraction testing. |
| API inputs/outputs data sharing not opted in | verified | verified | Owner confirmed API input/output sharing disabled on 2026-08-02. |
| feedback/evaluation/fine-tuning data sharing disabled unless explicitly disclosed | verified | verified | Owner confirmed evaluation/fine-tuning sharing disabled on 2026-08-02. |
| Responses API extraction sends `store=false` | verified | verified | Hosted production-like `aevryn provider-config-check` recorded `responses_store=false` and `request_storage=disabled` on 2026-07-17; source review rechecked on 2026-08-01. |
| background mode disabled for extraction | verified | verified | Aevryn's public-beta extraction scope uses direct Responses API extraction and does not enable background mode; background mode remains separately review-gated. |
| Responses API endpoint scope confirmed | verified | verified | Aevryn provider review and hosted config evidence scope extraction to the OpenAI Responses API. |
| Conversations/Assistants/Threads/Vector Stores/Files/Batches/Evals/fine-tuning out of public-beta extraction scope | verified | verified | Public-beta provider review keeps these endpoints out of extraction scope unless separately reviewed. |
| abuse-monitoring retention disclosed accurately | verified | verified | Official source recheck on 2026-08-01 confirmed `/v1/responses` abuse-monitoring retention is listed as 30 days by default; disclosure candidate includes this boundary. |
| Modified Abuse Monitoring state recorded | verified, not_approved, or not_available | not_available | Owner could not locate MAM controls in dashboard on 2026-08-02; do not disclose as enabled. |
| Zero Data Retention state recorded | verified, not_approved, or not_available | not_available | Owner could not locate ZDR controls in dashboard on 2026-08-02; do not disclose as enabled. |
| data residency state recorded | verified, not_approved, or not_available | not_available | Owner could not locate data residency controls in dashboard on 2026-08-02; do not disclose as enabled. |
| public Privacy Policy matches verified account/project posture | verified | blocked | Owner product-truth wording approved on 2026-08-02; attorney review still blocked. |
| public Trust/User Rights pages match verified account/project posture | verified | verified | Public wording consistency review passed on 2026-08-02 and owner product-truth provider wording approval is recorded. |

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

The local developer shell check on 2026-08-01 failed closed because
`AEVRYN_DEPLOYMENT_ENV=production` was not set. That local failure is expected
outside the production-like environment and did not print secrets.

Before final public-beta provider approval, rerun this command in the hosted or
production-like provider environment after the final OpenAI account/project
settings are confirmed.

---

# Owner Dashboard Verification

The following items could not be verified from repository code or official
source review alone. The Aetherra Labs owner reviewed the production OpenAI
dashboard on 2026-08-02 and recorded non-secret results:

* production organization confirmed
* production project confirmed
* API inputs/outputs sharing disabled for the Aevryn production project
* evaluation/fine-tuning data sharing disabled unless separately disclosed
* Modified Abuse Monitoring controls were not found by owner review
* Zero Data Retention controls were not found by owner review
* data residency controls were not found by owner review
* selected production project uses the expected `gpt-5.4-mini` model

Provider billing/quota limits still require final public-beta owner review.

If any dashboard setting differs from the public disclosure candidate, public
provider-backed extraction must remain disabled until the public docs are
updated and reviewed.

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
OpenAI production account verification: Dashboard and owner product-truth wording verified; legal/final signoff pending
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

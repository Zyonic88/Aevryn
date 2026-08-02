# Aevryn Provider Disclosure Wording Approval

> Built by **Aetherra Labs**

This document records final owner product-truth approval for Aevryn's public
AI-provider disclosure wording.

It is not legal advice.

It does not approve public beta.

---

# Status

```text
Review: Final provider disclosure wording approval
Date: 2026-08-02
Status: Owner product-truth wording approved - attorney review still blocked
Public beta: Blocked
```

---

# Core Rule

```text
Users must know when story content leaves Aevryn-owned systems.
```

Aevryn must say plainly what provider may receive story content, why it is
sent, what is not sent, how provider output is treated, and which provider
controls are verified versus unavailable or unverified.

---

# Approved Product-Truth Wording

The following wording is approved as Aetherra Labs' product-truth position for
public-beta preparation:

```text
Aevryn uses OpenAI as the current AI provider candidate for evidence-bounded
extraction when provider-backed extraction is enabled.

When provider-backed extraction runs, Aevryn may send selected story excerpts,
scene context, evidence anchors, extraction instructions, and structured-output
requirements needed to identify candidate characters, world items,
relationships, scenes, and state changes.

Aevryn does not send account passwords, session tokens, API keys, unrelated
projects, unrelated stories, full product logs, support tickets, or local
machine paths to AI providers.

Provider output is not Canon. Aevryn validates provider output against story
evidence before accepting anything into Canon-backed project state.

Aetherra Labs does not train on user stories without explicit opt-in.

The current OpenAI review records that OpenAI API inputs and outputs are not
used for model training by default unless an organization explicitly opts in.
Aetherra Labs has verified that API input/output sharing and
evaluation/fine-tuning sharing are disabled for the production OpenAI project.

Aevryn's OpenAI Responses API extraction requests set store=false.

OpenAI abuse-monitoring logs may contain prompts and responses and are retained
for up to 30 days by default unless a different approved retention control
applies or law requires longer retention.

Modified Abuse Monitoring, Zero Data Retention, and data residency controls
are not enabled or not verified for Aevryn and must not be represented as
enabled.

Provider-backed extraction must remain blocked from public beta unless this
provider disclosure is published consistently, legal-sensitive wording is
reviewed, and final public-beta signoff is recorded.
```

---

# Evidence Reviewed

This approval is based on these non-secret records:

* `docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md`
* `docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md`
* `docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md`
* `docs/AEVRYN_PUBLIC_WORDING_CONSISTENCY_REVIEW_2026_08_02.md`
* hosted production-like `aevryn provider-config-check` output recorded on
  2026-07-17 with `model=gpt-5.4-mini`, `request_storage=disabled`,
  `responses_store=false`, and `secrets_printed=0`
* owner OpenAI dashboard review recorded on 2026-08-02

The official OpenAI source posture was rechecked on 2026-08-02 against:

* OpenAI API data controls:
  `https://platform.openai.com/docs/models/default-usage-policies-by-endpoint`
* OpenAI Help Center data-sharing controls:
  `https://help.openai.com/en/articles/10306912-sharing-feedback-and-api-inputs-and-outputs-with-openai`

The recheck supports the product-truth wording above:

* OpenAI states API inputs and outputs are not used for model training by
  default unless the organization opts in.
* OpenAI states API input/output sharing and evaluation/fine-tuning data
  sharing are disabled by default and owner-controlled.
* OpenAI lists `/v1/responses` as not used for training.
* OpenAI lists `/v1/responses` abuse-monitoring retention as 30 days by
  default.
* OpenAI documents Modified Abuse Monitoring, Zero Data Retention, and data
  residency as separate controls that require eligibility, approval, or project
  configuration.

---

# Stop Conditions

Do not publish or approve provider-backed public beta if:

* the provider changes
* the production model changes without a new provider review
* API input/output sharing or evaluation/fine-tuning sharing is enabled
* Aevryn cannot verify `store=false` for extraction requests
* public wording claims Modified Abuse Monitoring, Zero Data Retention, or data
  residency are enabled
* public wording implies provider output is Canon
* public wording implies no provider-side retention exists
* public wording implies full manuscripts are sent by default
* attorney review has not completed for legal-sensitive provider wording

---

# Remaining Blockers

This approval closes owner product-truth approval of the provider disclosure
wording.

It does not close:

* attorney review of legal-sensitive Privacy Policy, Terms, and provider
  disclosure wording
* backup retention owner/legal wording approval
* production Supabase plan retention verification
* production R2 lifecycle/deletion policy verification
* final public-beta signoff

---

# Acceptance

```text
provider_disclosure_product_truth=approved
provider_disclosure_legal_review=blocked
provider_backed_public_beta=blocked_until_final_signoff
public_beta=blocked_until_final_signoff
```

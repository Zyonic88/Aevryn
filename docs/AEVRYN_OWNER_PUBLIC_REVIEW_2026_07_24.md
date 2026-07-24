# Aevryn Owner Public Review - 2026-07-24

> Built by **Aetherra Labs**

This dated worksheet records owner review decisions for Aevryn's public-facing
V2 beta materials.

It is separate from attorney review.

It does not approve public beta by itself.

---

# Status

```text
Review: Owner public-facing review
Date: 2026-07-24
Status: Prepared; owner decisions pending
Public beta: Blocked
```

---

# Core Rule

```text
Approve only what is true today.
```

Owner review may approve Aetherra Labs' product intent, brand posture, public
truthfulness, support expectations, and user-facing promises.

Owner review must not approve legal language, attorney-controlled risk,
provider account posture, or backup behavior that has not been verified.

---

# Source Documents Reviewed

Owner review should use:

* `docs/AEVRYN_OWNER_PUBLIC_REVIEW_RECORD.md`
* `docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md`
* `docs/AEVRYN_PUBLIC_LEGAL_REVIEW_PACKET.md`
* `docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md`
* `docs/AEVRYN_PUBLIC_SITE_PUBLICATION_PLAN.md`
* `docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md`
* `docs/AEVRYN_PUBLIC_CONTACTS.md`
* `docs/AEVRYN_BACKUP_RETENTION_DECISION.md`
* `docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md`
* `docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md`
* `docs/TERMS_OF_SERVICE.md`
* `docs/PRIVACY_POLICY.md`
* `docs/ACCEPTABLE_USE_POLICY.md`
* `docs/SECURITY_DISCLOSURE.md`

---

# Decision States

Use one state per row:

```text
approved_by_owner
blocked_needs_revision
blocked_needs_attorney
blocked_needs_provider_verification
blocked_needs_backup_verification
accepted_residual_beta_risk
not_applicable
```

The default state is blocked or pending. Do not mark a row approved merely
because the page exists, deploys, or reads well.

---

# Owner Decision Table

| Area | Question | Current Decision | Required Follow-Up |
| --- | --- | --- | --- |
| Operator identity | Should public pages identify Aetherra Labs as the operator? | blocked_needs_owner_decision | Owner decision required |
| Product domain | Should `aevryn.ai` be the primary public product domain? | blocked_needs_owner_decision | Owner decision required |
| Contact aliases | Are `support@aevryn.ai`, `privacy@aevryn.ai`, `security@aevryn.ai`, and `abuse@aevryn.ai` correct for public pages? | blocked_needs_owner_decision | Owner decision required |
| Trust promise | Is "Your work belongs to you" acceptable as a public promise? | blocked_needs_owner_decision | Owner decision required |
| Story ownership | Should public pages state that uploaded stories, Canon, generated outputs, and exports belong to users? | blocked_needs_owner_decision | Owner decision required |
| AI training posture | Should public pages state that Aetherra Labs does not train on user stories without explicit opt-in? | blocked_needs_owner_decision | Owner decision required |
| Provider disclosure | Does the OpenAI provider disclosure candidate match owner intent? | blocked_needs_provider_verification | Complete production OpenAI account verification before approval |
| Backup/deletion wording | Does the backup/deletion wording match owner intent? | blocked_needs_backup_verification | Owner/legal review and production backup behavior verification required |
| Support procedure | Is metadata-first support with source-prose redaction guidance acceptable? | blocked_needs_owner_decision | Owner decision required |
| Content classification | Is General/Teen/Mature/Explicit classification acceptable as public posture? | blocked_needs_owner_decision | Owner decision required |
| Legal drafts | Are Terms, Privacy, AUP, and Security Disclosure ready for attorney review? | blocked_needs_attorney | Attorney review required before public beta |
| Public beta readiness | Are remaining public beta blockers acceptable or resolved? | blocked_needs_owner_decision | Final signoff required |

---

# Evidence Already Available

Implementation-backed evidence already recorded elsewhere:

* contact aliases are provisioned and tested
* public pages are implemented and production-reachable
* hosted production-like smoke passed
* final bounded hosted observability review passed
* restore/audit drill passed
* hosted audit append-only access verification passed
* official OpenAI source review is recorded
* OpenAI production account verification is not complete
* legal-sensitive pages remain drafts pending attorney review

---

# Stop Conditions

Do not mark this owner review complete if:

* any row remains `blocked_needs_owner_decision`
* provider disclosure remains `blocked_needs_provider_verification`
* backup/deletion wording remains `blocked_needs_backup_verification`
* legal drafts remain `blocked_needs_attorney`
* public pages imply attorney review, provider verification, or backup
  verification happened when it did not
* owner approval would cause public beta to look approved before final signoff

---

# Public-Beta Decision

```text
Owner public-facing review: Not complete
Public beta: Blocked
Reason: Owner decisions have not been recorded, attorney review remains open,
provider production account verification remains open, backup/deletion wording
verification remains open, and final public-beta signoff remains open.
```

---

# Acceptance

This dated owner review is accepted when:

```text
Every row has an explicit owner decision, legal/provider/backup dependencies
remain blocked unless actually verified, and the final release-candidate record
can cite this worksheet without implying attorney approval.
```

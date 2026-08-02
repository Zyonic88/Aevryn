# Aevryn Public Wording Consistency Review

> Built by **Aetherra Labs**

This review records an internal consistency pass across Aevryn's public-facing
trust, privacy, support, user-rights, security, content, terms, and acceptable
use wording.

It is not legal advice.

It does not approve public beta.

---

# Status

```text
Review: Public wording consistency review
Date: 2026-08-02
Status: Internal consistency review passed - legal-sensitive wording still blocked
Public beta: Blocked
```

---

# Core Rule

```text
Public copy must be true before it is polished.
```

Aevryn public pages must be understandable to creators, consistent across
pages, and careful around deletion, backups, provider-backed extraction,
employee access, support requests, and public-beta readiness.

---

# Scope Reviewed

Reviewed source documents:

* `docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md`
* `docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md`
* `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`
* `docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md`
* `docs/AEVRYN_PUBLIC_CONTACTS.md`
* `docs/AEVRYN_OWNER_PUBLIC_REVIEW_RECORD.md`
* `docs/AEVRYN_OWNER_PUBLIC_REVIEW_2026_07_24.md`
* `docs/AEVRYN_BACKUP_RETENTION_DECISION.md`
* `docs/AEVRYN_BACKUP_RETENTION_OWNER_REVIEW_2026_08_02.md`
* `docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md`
* `docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md`
* `docs/AEVRYN_PROVIDER_DISCLOSURE_WORDING_APPROVAL_2026_08_02.md`
* `docs/PRIVACY_POLICY.md`
* `docs/AEVRYN_USER_RIGHTS.md`
* `web/src/pages/PublicInfoPages.tsx`

---

# Consistency Decisions

| Area | Decision | Status |
| --- | --- | --- |
| Operator identity | Public pages identify Aetherra Labs as operator where company identity matters. | passed |
| Product domain | Public product identity remains `aevryn.ai`. | passed |
| Contact aliases | Support, privacy, security, and abuse aliases are the public product contacts. | passed |
| Story ownership | Uploaded stories, Canon, prompt packs, and exports remain user-owned. | passed |
| AI training posture | Aetherra Labs does not train on user stories without explicit opt-in. | passed |
| Provider-backed extraction | Public copy states provider output is not Canon; owner product-truth provider wording approval is recorded; attorney review and final signoff remain blocked. | passed_with_blocker |
| Backup/deletion wording | Public copy separates active deletion from bounded backup retention. | passed_with_blocker |
| Support privacy | Support copy tells users not to send full manuscripts, chapters, provider responses, credentials, tokens, private URLs, or private-story screenshots by default. | passed |
| Employee access | Public copy avoids claiming employees can never access data under any circumstance. | passed |
| Public-beta status | Public copy does not imply public beta is approved. | passed |
| Legal drafts | Legal-sensitive pages remain marked as drafts for attorney review. | passed_with_blocker |

---

# Live Page Alignment

The live public page implementation is aligned when it preserves these
plain-language messages:

* Trust page: "Your work belongs to you."
* Privacy page: stories are private by default, no training without opt-in,
  deletion removes active storage, backups may retain deleted data for a
  disclosed recovery window, and provider output is not Canon.
* User Rights page: users own stories, Canon, and exports; AI training is off
  by default; deletion removes active product data; backup wording remains
  review-gated.
* Support page: users can contact support, privacy, security, and abuse
  aliases without sending full manuscripts by default.
* Legal-sensitive pages: Terms, Privacy Policy, Acceptable Use, and Security
  Disclosure remain draft/review-gated until counsel review is complete.

---

# Open Blockers

This review does not close:

* attorney review of legal-sensitive pages
* provider disclosure legal review
* production Supabase plan retention verification
* production R2 lifecycle/deletion policy verification
* backup retention owner/legal wording approval
* final public-beta signoff

---

# Stop Conditions

Do not approve public beta if:

* public pages imply attorney review happened when it did not
* public pages imply provider-backed extraction is approved without attorney
  provider disclosure review and final public-beta signoff
* public pages imply deleted data disappears instantly from every backup
* public support copy asks users to send full manuscripts by default
* public copy claims employees can never access user data under any
  circumstance
* public copy says or implies public beta is approved before final signoff

---

# Acceptance

This consistency review is accepted when:

```text
public_wording_consistency_review=passed
legal_sensitive_wording=blocked_until_attorney_review
provider_disclosure_product_truth=approved
provider_disclosure_legal_review=blocked_until_attorney_review
backup_retention_wording=blocked_until_owner_legal_approval
public_beta=blocked_until_final_signoff
```

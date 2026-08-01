# Aevryn Owner Public Review Record

> Built by **Aetherra Labs**

This record tracks Aetherra Labs owner review of Aevryn's public-facing V2
beta materials.

It is separate from attorney review.

It does not approve public beta by itself.

---

# Status

```text
Review: Owner public-facing review
Status: Owner-controlled decisions recorded
Public beta: Blocked
```

---

# Core Rule

```text
The owner approves product truth; counsel approves legal language.
```

Owner review verifies that public pages, support procedures, provider
disclosures, backup wording, and trust promises match Aevryn's intended product
behavior and Aetherra Labs' public posture.

Attorney review still controls legal approval for Terms, Privacy Policy,
Acceptable Use, Security Disclosure, liability, warranty, governing law, and
safe-harbor wording.

---

# Required Source Documents

Owner review must check:

* `docs/AEVRYN_OWNER_PUBLIC_REVIEW_2026_07_24.md`
* `docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md`
* `docs/AEVRYN_PUBLIC_LEGAL_REVIEW_PACKET.md`
* `docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md`
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

# Review States

Use one of these states for each row:

```text
approved_by_owner
blocked_needs_revision
blocked_needs_attorney
blocked_needs_provider_verification
blocked_needs_backup_verification
not_applicable
```

---

# Owner Review Checklist

| Area | Required Owner Decision | Current State | Notes |
| --- | --- | --- | --- |
| Operator identity | Aetherra Labs is the public operator identity | approved_by_owner | Public pages should identify Aetherra Labs as Aevryn's operator. |
| Product domain | `aevryn.ai` is the primary product domain | approved_by_owner | `aevryn.ai` is approved as the primary Aevryn product domain. |
| Contact aliases | support/privacy/security/abuse aliases are correct | approved_by_owner | Contact verification exists and these aliases are approved for public pages. |
| Trust promise | "Your work belongs to you" is acceptable public posture | approved_by_owner | Approved as Aevryn's public trust promise. |
| Story ownership | uploaded stories, Canon, generated outputs, and exports belong to users | approved_by_owner | Approved as product posture; legal-sensitive wording still needs attorney review. |
| AI training posture | no training on user stories without explicit opt-in | approved_by_owner | Approved as product posture and public promise. |
| Provider disclosure | OpenAI provider wording matches owner intent | blocked_needs_provider_verification | Production account verification remains open |
| Backup/deletion wording | active deletion and backup retention language matches owner intent | blocked_needs_backup_verification | Owner/legal review remains open |
| Support procedure | metadata-first support and source-prose redaction guidance are acceptable | approved_by_owner | Approved as public-beta support posture; full manuscripts remain out of default support flow. |
| Content classification | General/Teen/Mature/Explicit posture matches product intent | approved_by_owner | Approved as content-aware, not content-opinionated posture. |
| Legal drafts | Terms/Privacy/AUP/Security Disclosure are ready for attorney review | blocked_needs_attorney | Owner agrees these are the correct legal drafts to send for attorney review; attorney must approve. |
| Public beta readiness | unresolved blockers are acceptable or must remain blocking | blocked_needs_revision | Final public-beta signoff not recorded. |

---

# Owner Review Questions

Before marking any row `approved_by_owner`, answer:

* Is the statement true for the current production-like implementation?
* Is the wording understandable to a non-technical creator?
* Does the wording avoid internal engineering jargon?
* Does the wording avoid promising behavior Aevryn cannot verify?
* Does the wording preserve Aetherra Labs' values around user ownership,
  privacy, and story safety?
* Does the row depend on attorney review, provider verification, or backup
  verification before public beta?

---

# Stop Conditions

Do not mark owner review complete if:

* the public pages use final-looking legal language before attorney review
* provider-backed extraction is enabled without verified provider disclosure
* deletion wording ignores backup retention
* support procedures invite users to send full manuscripts by default
* public copy implies public beta is approved before final signoff
* owner review silently accepts a blocker without recording residual risk

---

# Acceptance

This owner review is accepted when:

```text
Owner-controlled public-facing promises have explicit owner decisions,
remaining attorney/provider/backup blockers are still marked as blockers, and
no public-beta approval is implied before final signoff.
```

The current dated worksheet is:

* `docs/AEVRYN_OWNER_PUBLIC_REVIEW_2026_07_24.md`

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
Status: Not started
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
| Operator identity | Aetherra Labs is the public operator identity | blocked_needs_revision | Owner review not recorded |
| Product domain | `aevryn.ai` is the primary product domain | blocked_needs_revision | Owner review not recorded |
| Contact aliases | support/privacy/security/abuse aliases are correct | blocked_needs_revision | Contact verification exists; owner publication approval not recorded |
| Trust promise | "Your work belongs to you" is acceptable public posture | blocked_needs_revision | Owner review not recorded |
| Story ownership | uploaded stories, Canon, generated outputs, and exports belong to users | blocked_needs_revision | Owner review not recorded |
| AI training posture | no training on user stories without explicit opt-in | blocked_needs_revision | Owner review not recorded |
| Provider disclosure | OpenAI provider wording matches owner intent | blocked_needs_provider_verification | Production account verification remains open |
| Backup/deletion wording | active deletion and backup retention language matches owner intent | blocked_needs_backup_verification | Owner/legal review remains open |
| Support procedure | metadata-first support and source-prose redaction guidance are acceptable | blocked_needs_revision | Support procedure owner review remains open |
| Content classification | General/Teen/Mature/Explicit posture matches product intent | blocked_needs_revision | Owner review not recorded |
| Legal drafts | Terms/Privacy/AUP/Security Disclosure are ready for attorney review | blocked_needs_attorney | Owner can prepare; attorney must approve |
| Public beta readiness | unresolved blockers are acceptable or must remain blocking | blocked_needs_revision | Final signoff not recorded |

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
Every owner-controlled public-facing promise has an explicit owner decision,
remaining attorney/provider/backup blockers are still marked as blockers, and
no public-beta approval is implied before final signoff.
```

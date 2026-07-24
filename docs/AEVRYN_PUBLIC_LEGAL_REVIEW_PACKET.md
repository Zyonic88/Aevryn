# Aevryn Public Legal Review Packet

> Built by **Aetherra Labs**

This packet organizes the legal-sensitive documents and open decisions required
before Aevryn V2 public beta.

It is not legal advice.

It does not approve public beta.

---

# Status

```text
Review packet: Public legal review
Status: Prepared for owner and attorney review
Public beta: Blocked
```

---

# Core Rule

```text
Legal copy must match product behavior.
```

No legal, privacy, trust, support, or acceptable-use page may promise behavior
that Aevryn cannot verify through implementation, production configuration,
provider terms, or operations practice.

---

# Documents Requiring Attorney Review

| Document | Purpose | Required Decisions |
| --- | --- | --- |
| `docs/TERMS_OF_SERVICE.md` | User agreement | governing law, liability limitation, warranty language, termination, future payment language |
| `docs/PRIVACY_POLICY.md` | Legal privacy policy | processor list, cookies/analytics posture, user rights, backup retention, AI provider disclosure |
| `docs/ACCEPTABLE_USE_POLICY.md` | Platform use boundaries | prohibited content, mature/explicit content posture, enforcement language |
| `docs/SECURITY_DISCLOSURE.md` | Vulnerability reporting process | safe-harbor language, researcher scope, response commitments |

---

# Supporting Trust Documents

Counsel and owner review should also cross-check:

* `docs/AEVRYN_SECURITY.md`
* `docs/AEVRYN_PRIVACY.md`
* `docs/AEVRYN_USER_RIGHTS.md`
* `docs/AEVRYN_TRUST_MODEL.md`
* `docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md`
* `docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md`
* `docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md`
* `docs/AEVRYN_BACKUP_RETENTION_DECISION.md`
* `docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md`
* `docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md`
* `docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md`

---

# Non-Negotiable Product Promises

These promises should not be weakened accidentally:

* uploaded stories belong to their creators
* generated Canon and exports belong to the user
* Aetherra Labs does not train on user stories without explicit opt-in
* provider output is not Canon
* Aevryn validates provider output against story evidence before acceptance
* support is metadata-first and does not ask for full manuscripts by default
* deletion removes active product storage
* backup retention must be disclosed accurately
* employee access is limited and auditable, but the product must not claim
  employees can never access data under any circumstance

---

# Open Legal Decisions

Before public beta, record decisions for:

```text
governing_law=blocked
liability_limitation=blocked
warranty_disclaimer=blocked
payment_terms=not_applicable_until_paid_plans
refund_policy=not_applicable_until_paid_plans
privacy_processor_list=blocked
cookie_notice=blocked
analytics_posture=blocked
user_rights_jurisdiction_language=blocked
mature_content_policy=blocked
security_safe_harbor=blocked
provider_disclosure=blocked
backup_retention_wording=blocked
```

---

# Public Page Cross-Check

The public website must not publish final-looking legal pages unless:

* contact aliases are verified
* attorney review is complete or the page clearly remains draft/internal
* provider-backed extraction disclosure matches the verified provider posture
* backup/deletion wording matches the production backup retention decision
* acceptable-use language matches the content-classification posture
* security disclosure language does not overpromise safe harbor beyond what
  counsel approves

---

# Stop Conditions

Do not approve public beta if:

* legal-sensitive pages are still drafts
* governing law is not selected
* liability and warranty language is not reviewed
* privacy processor disclosures are incomplete
* provider-backed extraction is enabled without approved provider disclosure
* backup retention wording does not match production behavior
* public pages imply attorney review happened when it did not

---

# Acceptance

This packet is accepted when:

```text
The owner and attorney can review one consolidated packet and record every
legal-sensitive approval, blocker, and required public-page change before
public beta.
```

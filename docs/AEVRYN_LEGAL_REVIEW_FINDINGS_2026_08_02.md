# Aevryn Legal Review Findings

> Built by **Aetherra Labs**

This document records non-attorney compliance triage findings for Aevryn V2
public-beta legal drafts.

It is not legal advice.

It does not approve public beta.

---

# Status

```text
Review source: Justee.ai compliance review
Review type: Non-attorney draft triage
Date recorded: 2026-08-02
Status: Draft-hardening changes applied; attorney review still required
Public beta: Blocked
```

---

# Core Rule

```text
Compliance triage can improve drafts. It cannot approve legal launch.
```

The findings below were used to improve structure, clarity, definitions, and
product-truth disclosures in the draft legal documents. They do not replace
attorney review.

---

# Documents Reviewed

* `docs/TERMS_OF_SERVICE.md`
* `docs/PRIVACY_POLICY.md`
* `docs/ACCEPTABLE_USE_POLICY.md`
* `docs/SECURITY_DISCLOSURE.md`
* `docs/AEVRYN_PUBLIC_LEGAL_REVIEW_PACKET.md`

---

# Findings Applied

## Terms Of Service

Triage findings:

* limitation of liability was missing
* governing law and venue were missing
* warranty disclaimer was only a placeholder
* DMCA / copyright repeat-infringer language was missing
* service availability was too general

Draft-hardening changes:

* added clearer parties/service scope
* added eligibility and minor-use attorney-review gate
* expanded acceptable-use references
* clarified user responsibilities
* expanded intellectual-property and limited-license wording
* added AI/Canon boundaries
* added copyright and repeat-infringer draft section
* kept final DMCA, liability, warranty, dispute-resolution, and governing-law
  language explicitly attorney-controlled

## Privacy Policy

Triage findings:

* user rights process was incomplete
* processor disclosure was incomplete
* children's privacy language was missing
* sensitive-data posture was missing
* AI training language was too narrow when limited to uploaded stories
* retention wording relied too heavily on internal docs

Draft-hardening changes:

* expanded scope and information-collected sections
* stated uses of information directly
* broadened AI-training no-default-training language to uploaded, pasted,
  imported, and generated user story/project content
* added processor candidate list
* added direct backup-retention wording using verified production values
* added privacy request process and attorney-controlled jurisdiction checklist
* added sensitive-data, children's privacy, international/data-residency, and
  security sections

## Acceptable Use Policy

Triage findings:

* platform abuse was undefined
* enforcement process was too vague
* mature fiction handling was described as future-only
* copyright/reporting path needed more detail

Draft-hardening changes:

* defined platform abuse
* expanded prohibited uses
* clarified current mature/explicit fiction posture
* added rights/repeat-infringer draft language
* added security-research cross-reference
* added enforcement actions and appeal path
* kept age, explicit-content, notice, appeal, and repeat-violation language
  attorney-review gated

## Security Disclosure

Triage findings:

* safe harbor was aspirational and needed counsel review
* scope was initial rather than final
* response timelines were vague
* submission data-handling boundaries needed more detail

Draft-hardening changes:

* added initial in-scope systems
* added out-of-scope testing boundaries
* added researcher rules
* strengthened safe-harbor draft while keeping it attorney-controlled
* added response targets
* added coordinated disclosure, severity, and researcher privacy sections
* separated vulnerability reports from abuse/copyright reports

---

# Attorney-Controlled Decisions Still Blocked

The following decisions remain attorney-controlled:

```text
governing_law=blocked
venue=blocked
dispute_resolution=blocked
liability_limitation=blocked
warranty_disclaimer=blocked
dmca_agent_and_process=blocked
privacy_rights_jurisdiction_language=blocked
children_privacy_language=blocked
sensitive_data_language=blocked
processor_list_finalization=blocked
cookie_notice=blocked
analytics_posture=blocked
mature_explicit_content_policy=blocked
security_safe_harbor=blocked
researcher_response_commitments=blocked
provider_disclosure_legal_review=blocked
backup_retention_wording_legal_review=blocked
```

---

# Public Beta Decision

These draft-hardening changes reduce known gaps, but they do not approve public
beta.

Public beta remains blocked until:

* attorney review is complete for legal-sensitive pages
* attorney-controlled decisions are resolved or explicitly accepted in the
  release-candidate record
* approved attorney edits are reconciled back into canonical Markdown source
* DOCX review copies are regenerated from the approved Markdown source
* final public-beta signoff is recorded

---

# Acceptance

```text
legal_triage_findings_recorded=true
draft_hardening_applied=true
attorney_review_complete=false
public_beta=blocked
```

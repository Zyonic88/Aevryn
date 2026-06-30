# Aevryn Public Trust Readiness

> Built by **Aetherra Labs**

This document tracks V2 Release Candidate Readiness Gate 1.

Gate 1 turns Aevryn's trust, privacy, security, content, support, and disclosure drafts into public-facing material that users can understand before uploading unpublished work.

---

# Gate Status

```text
Gate: Public-Facing Trust Documentation
Status: Started
Public beta: Blocked
```

The source drafts exist, but they are not all public-page ready.

---

# Core Rule

```text
Public trust pages must be true, plain-language, and backed by implementation.
```

No public trust page may claim a production behavior that Aevryn has not implemented, selected, or disclosed.

---

# Required Public Pages

## Trust Model

Source:

* `docs/AEVRYN_TRUST_MODEL.md`

Readiness:

```text
Draft-ready.
```

Required before public beta:

* convert into website copy
* keep evidence-backed Canon and AI-never-owns-truth language
* avoid implying public-beta readiness before deployment decisions are complete

## User Rights

Source:

* `docs/AEVRYN_USER_RIGHTS.md`

Readiness:

```text
Draft-ready.
```

Required before public beta:

* convert into website copy
* preserve "Your work belongs to you"
* align deletion and backup language with final production retention windows

## Privacy Explanation

Source:

* `docs/AEVRYN_PRIVACY.md`
* `docs/PRIVACY_POLICY.md`

Readiness:

```text
Draft exists. Legal review required.
```

Required before public beta:

* attorney review
* production provider list
* data residency statement
* production retention windows
* public privacy contact

## Security Explanation

Source:

* `docs/AEVRYN_SECURITY.md`

Readiness:

```text
Draft exists. Production details required.
```

Required before public beta:

* production identity provider
* production secret manager
* hosted secret scanning and dependency alert posture
* production monitoring posture
* incident response contact path

## Content Classification Explanation

Source:

* `docs/AEVRYN_CONTENT_CLASSIFICATION.md`

Readiness:

```text
Draft-ready.
```

Required before public beta:

* decide whether project ratings are visible in the public-beta UI
* align Mature and Explicit language with legal review and provider policy
* avoid implying generation-module behavior exists in V2

## Security Disclosure

Source:

* `docs/SECURITY_DISCLOSURE.md`

Readiness:

```text
Target contact selected. Provisioning and testing required.
```

Required before public beta:

* security report email or intake form
* response expectations
* safe-harbor language reviewed by counsel
* public scope statement

## Support Contact

Source:

* `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`

Readiness:

```text
Started. Target contact paths selected; provisioning and testing required.
```

Required before public beta:

* support contact path
* bug-report instructions
* privacy-preserving report guidance
* abuse-report path
* account/project deletion request path

---

# Plain-Language Requirements

Every public trust page should avoid internal-only phrasing such as:

* "Phase 11"
* "local adapters"
* "release gate"
* "implementation gate"
* "metadata-only workflow observability"

Those concepts can remain in engineering docs. Public pages should explain the user-facing promise and any limitations in plain language.

---

# Truthfulness Requirements

Public pages must not claim:

* public beta is approved
* production backups have a selected retention window before one is chosen
* production identity/storage/secrets systems are selected before they are chosen
* employees can never access data under any circumstance
* deleted data disappears from all backups instantly unless production architecture makes that true
* AI providers never receive content unless provider-backed extraction is disabled or disclosed

---

# Gate 1 Acceptance

Gate 1 is accepted when:

* public-facing trust pages exist
* pages are written in plain language
* legal-sensitive pages are marked attorney-reviewed or blocked
* support and security contact paths exist
* claims match implementation and production deployment decisions
* no page overpromises deletion, provider retention, employee access, backups, or public-beta readiness

Current result:

```text
Not accepted.
```

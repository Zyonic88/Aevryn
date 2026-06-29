# Aevryn V2 Release Candidate Readiness

> Built by **Aetherra Labs**

This document defines the work required after V2 product development and before public beta.

---

# Decision

```text
V2 product development is complete.
V2 Release Candidate Readiness is the active work track.
Public beta is not approved yet.
```

Release Candidate Readiness is not Version 3.

It is the bridge between a working private-alpha product and a public-facing product that strangers can trust with unpublished creative work.

---

# Core Rule

```text
Public beta requires operational trust, not just passing product tests.
```

The platform must be ready for real users, real manuscripts, real accounts, real support requests, real legal obligations, and real security incidents.

---

# Scope

Release Candidate Readiness includes:

* production deployment architecture
* production storage decisions
* production identity/auth decisions
* secret management
* hosted monitoring and alerting
* hosted dependency and secret scanning
* CI release gates
* rate limiting
* HTTPS/HSTS edge policy
* backup and recovery windows
* audit storage and retention
* legal review
* public-facing trust pages
* support and security contact paths
* final alpha-to-beta manual test pass
* release candidate signoff

Release Candidate Readiness does not include:

* image generation
* video generation
* payments
* subscriptions
* teams
* collaboration
* publishing
* broad frontend redesign
* new creator workflow features

Those belong to Version 3 or later unless explicitly re-scoped.

---

# Gate 1 - Public-Facing Trust Documentation

Required before public beta:

* public-ready trust model
* user rights page
* privacy explanation
* security explanation
* content classification explanation
* support contact path
* security disclosure contact path

Source drafts:

* `docs/AEVRYN_TRUST_MODEL.md`
* `docs/AEVRYN_USER_RIGHTS.md`
* `docs/AEVRYN_SECURITY.md`
* `docs/AEVRYN_PRIVACY.md`
* `docs/AEVRYN_CONTENT_CLASSIFICATION.md`
* `docs/SECURITY_DISCLOSURE.md`

Gate tracking:

* `docs/AEVRYN_PUBLIC_TRUST_READINESS.md`
* `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`

Acceptance:

```text
Public-facing trust docs are accurate, plain-language, reviewed, and consistent with implementation.
```

---

# Gate 2 - Legal Review

Required before public beta:

* Terms of Service reviewed by attorney
* Privacy Policy reviewed by attorney
* Acceptable Use Policy reviewed by attorney
* Security Disclosure reviewed by attorney
* public contact information added
* governing law selected
* liability and warranty language finalized

Source drafts:

* `docs/TERMS_OF_SERVICE.md`
* `docs/PRIVACY_POLICY.md`
* `docs/ACCEPTABLE_USE_POLICY.md`
* `docs/SECURITY_DISCLOSURE.md`

Acceptance:

```text
Legal drafts are attorney-reviewed and approved for public beta use.
```

---

# Gate 3 - Production Infrastructure

Required before public beta:

* production database selected
* production object storage selected
* production import/export storage boundaries defined
* production identity provider selected
* production secret manager selected
* deployment environment separation defined
* HTTPS and HSTS policy defined
* domain and DNS strategy selected

Gate tracking:

* `docs/AEVRYN_PRODUCTION_INFRASTRUCTURE_READINESS.md`

Acceptance:

```text
Production architecture is documented, implemented, and tested without relying on local JSON/filesystem adapters.
```

---

# Gate 4 - Security Operations

Required before public beta:

* hosted repository secret scanning
* push protection
* hosted dependency alerts
* protected branch rules
* CI release gates
* production rate limiting
* production request-body limits
* production timeout limits
* security monitoring alerts
* incident response process

Gate tracking:

* `docs/AEVRYN_SECURITY_OPERATIONS_READINESS.md`

Acceptance:

```text
Security controls exist outside local developer machines and fail closed for public deployment.
```

---

# Gate 5 - Backup, Recovery, And Audit

Required before public beta:

* production backup frequency selected
* backup retention window selected
* backup encryption verified
* restore test completed
* disaster recovery procedure documented
* production audit storage selected
* audit retention selected
* audit access controls documented

Source docs:

* `docs/AEVRYN_BACKUP_RETENTION.md`
* `docs/BACKUP_AND_RECOVERY.md`
* `docs/AEVRYN_AUDIT_LEDGER.md`

Gate tracking:

* `docs/AEVRYN_BACKUP_RECOVERY_AUDIT_READINESS.md`

Acceptance:

```text
Deleted stories are removed from active storage, backup retention is disclosed, and recovery can be tested without hidden manuscript exposure.
```

---

# Gate 6 - AI Provider And Data Use

Required before public beta:

* provider list selected
* provider retention terms reviewed
* provider training behavior documented
* opt-in training posture preserved
* provider failure logging verified metadata-only
* model configuration documented

Gate tracking:

* `docs/AEVRYN_AI_PROVIDER_DATA_USE_READINESS.md`

Acceptance:

```text
Users can understand whether story content leaves Aevryn-owned systems and what providers may do with it.
```

---

# Gate 7 - Public Beta Support Readiness

Required before public beta:

* support contact path
* privacy contact path
* security contact path
* bug-report instructions
* source-prose redaction guidance
* abuse-report process
* account deletion request path
* project deletion support path

Gate tracking:

* `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`

Acceptance:

```text
Users have a clear way to get help without exposing manuscripts unnecessarily.
```

---

# Gate 8 - Release Candidate Test Pass

Required before public beta:

* backend gates pass
* frontend gates pass
* dependency audits pass
* secret scan passes
* static security scan passes
* performance regression check passes
* private alpha smoke path passes
* production-like deployment smoke test passes
* final manual alpha-to-beta pass is recorded

Gate tracking:

* `docs/AEVRYN_RELEASE_CANDIDATE_TEST_READINESS.md`

Acceptance:

```text
Release candidate behavior is repeatable and documented.
```

---

# Public Beta Decision

Public beta can be approved only when every gate above is complete or explicitly accepted by the project owner as a documented residual risk.

The default state is:

```text
Public beta blocked.
```

---

# Current Status

```text
Track: V2 Release Candidate Readiness
Status: Started
Public beta: Blocked
Version 3: Not started
```

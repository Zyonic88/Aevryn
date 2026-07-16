# Aevryn V2 Closeout

> Built by **Aetherra Labs**

This document records the Version 2 completion decision and the later alpha-testing decision that reopened V2 for language and identity quality gates.

---

# Decision

```text
Version 2 product development was previously complete for private/internal alpha.
Version 2 Phase 12 Language And Identity Understanding is accepted.
Version 2 is not public-beta approved yet.
```

V2 delivered the usable platform path:

```text
Register
-> Create Project
-> Upload Novel
-> Wait
-> View Character Cards
-> View World
-> View Timeline
-> View Scene Sheets
-> View Prompt Packs
-> Export
```

without touching the CLI.

Hosted alpha testing showed that two originally future-facing systems were required before V2 could close for release-candidate readiness:

* Translation Foundation
* Entity Resolution Foundation

Those systems are accepted in `docs/AEVRYN_V2_PHASE_12_ACCEPTANCE.md`.

---

# What Complete Means

V2 complete previously meant:

* all planned V2 phases are accepted
* the platform has an authenticated web/API workflow
* project and story state are durable in local adapters
* supported imports can be inspected, saved, processed, and reviewed
* processed output is available through workspace views
* monitoring is metadata-only
* performance budgets and regression checks exist
* private alpha recovery paths have been exercised
* Phase 11 security, privacy, dependency, secret-scan, static-scan, and trust-document gates are accepted

That decision was superseded by Phase 12 and then restored after Phase 12 acceptance.

V2 product scope is complete again for release-candidate readiness.

V2 complete still does not mean public launch.

---

# Public Beta Blockers

Public beta remains blocked until production-specific decisions and systems are selected, implemented, reviewed, and tested.

Required before public beta:

* production identity provider decision
* production database and storage adapters
* production object storage for uploaded manuscripts and exports
* production secret manager
* hosted repository secret scanning and push protection
* hosted dependency alerts
* protected branch and CI release gates
* rate limiting at the deployment edge or API gateway
* HTTPS/HSTS deployment policy
* production backup retention windows
* production audit storage and retention
* production log aggregation, retention, and access controls
* provider retention and AI data-use terms
* attorney-reviewed Terms of Service, Privacy Policy, Acceptable Use Policy, and Security Disclosure
* public support/security contact information

---

# Release Candidate Readiness

After Phase 12 is accepted, the next work track should return to:

```text
V2 Release Candidate Readiness
```

The readiness contract is defined in `docs/AEVRYN_V2_RELEASE_CANDIDATE_READINESS.md`.

That work is not V2 feature development. It is the active track after Phase 12 acceptance.

It is production readiness:

* deployment architecture
* production security configuration
* legal review
* infrastructure choices
* CI release gates
* public-beta operating procedures
* final alpha-to-beta manual test pass

---

# Version 3 Boundary

Version 3 must not begin by quietly expanding V2.

V3 begins after V2 Phase 12 and V2 release candidate readiness are understood and the team explicitly decides to start production expansion.

V3 candidate systems include media generation, publishing, payments, subscriptions, teams, and collaboration. Those systems are out of scope for V2 closeout.

---

# Final V2 Status

```text
V2 Platform: Product scope accepted after Phase 12 Language And Identity Understanding.
V2 Release Candidate Readiness: Active.
Public beta: Blocked pending production deployment/security/legal decisions.
Version 3: Not started.
```

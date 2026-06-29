# Aevryn V2 Closeout

> Built by **Aetherra Labs**

This document records the Version 2 completion decision.

---

# Decision

```text
Version 2 product development is complete for private/internal alpha.
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

---

# What Complete Means

V2 complete means:

* all planned V2 phases are accepted
* the platform has an authenticated web/API workflow
* project and story state are durable in local adapters
* supported imports can be inspected, saved, processed, and reviewed
* processed output is available through workspace views
* monitoring is metadata-only
* performance budgets and regression checks exist
* private alpha recovery paths have been exercised
* Phase 11 security, privacy, dependency, secret-scan, static-scan, and trust-document gates are accepted

V2 complete does not mean public launch.

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

The next work track should be named:

```text
V2 Release Candidate Readiness
```

That work is not V2 feature development.

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

V3 begins after V2 release candidate readiness is understood and the team explicitly decides to start production expansion.

V3 candidate systems include media generation, publishing, payments, subscriptions, teams, and collaboration. Those systems are out of scope for V2 closeout.

---

# Final V2 Status

```text
V2 Platform: Complete for private/internal alpha.
V2 Release Candidate Readiness: Next work track.
Public beta: Blocked pending production deployment/security/legal decisions.
Version 3: Not started.
```

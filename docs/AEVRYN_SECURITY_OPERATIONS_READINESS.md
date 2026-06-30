# Aevryn Security Operations Readiness

> Built by **Aetherra Labs**

This document tracks V2 Release Candidate Readiness Gate 4.

Gate 4 moves security controls from local developer checks into hosted, repeatable operations for public beta.

---

# Status

```text
Gate: Security Operations
Status: Started
Public beta: Blocked
```

Local security gates exist.

Public beta also needs hosted security controls that run outside a developer workstation.

Initial hosted workflow files now exist for backend gates, frontend gates, repository secret scanning, dependency auditing, and static security scanning.

Repo-side GitHub support files now also exist for CODEOWNERS, Dependabot updates, GitHub security reporting, and pull request verification.

These workflows and support files provide checks that branch protection can require, but public beta remains blocked until hosted branch protection, push protection, alert routing, rate limiting, and incident response are configured and verified.

---

# Core Rule

```text
Security controls must protect the release path, not just the local machine.
```

A public-beta release must not depend on one developer remembering to run local commands.

---

# Existing Local Gates

Existing local gates include:

* repository secret scanning in `docs/AEVRYN_REPOSITORY_SECRET_SCAN.md`
* dependency auditing in `docs/AEVRYN_DEPENDENCY_AUDIT.md`
* static security scanning in `docs/AEVRYN_STATIC_SECURITY_SCAN.md`
* API hardening in `docs/AEVRYN_API_SECURITY_HARDENING.md`
* Phase 11 gate tracking in `docs/AEVRYN_PHASE_11_SECURITY_GATES.md`
* hosted branch-protection runbook in `docs/AEVRYN_BRANCH_PROTECTION.md`
* hosted GitHub settings checklist in `docs/AEVRYN_GITHUB_HOSTED_CONTROLS.md`
* repo-side `CODEOWNERS`, `dependabot.yml`, `SECURITY.md`, and pull request template files under `.github/`

These gates are necessary, but they are not enough for public beta.

---

# Required Hosted Controls

Public beta remains blocked until hosted controls exist for:

* repository secret scanning
* push protection
* dependency alerts
* protected branch rules
* required CI release gates
* static security scan enforcement
* dependency audit enforcement
* frontend build and lint enforcement
* backend test enforcement
* security disclosure intake
* security monitoring alerts
* incident response routing

Hosted controls must fail closed for release branches.

---

# Protected Branch Rules

Protected branch rules must define:

* protected branches
* required status checks
* required review policy
* force-push policy
* deletion policy
* who can bypass checks
* how emergency fixes are handled

Bypass permissions must be narrow and auditable.

The concrete branch-protection runbook lives in `docs/AEVRYN_BRANCH_PROTECTION.md`.

---

# CI Release Gates

CI release gates should include:

* backend tests
* frontend tests
* backend lint
* frontend lint
* backend typing
* frontend build
* repository secret scan
* dependency audit
* static security scan
* release-readiness document tests

CI logs must not print secrets, full manuscripts, full chapters, full AI responses, provider payloads, or private machine paths.

---

# Hosted Dependency Alerts

Dependency alerts must cover:

* Python backend dependencies
* frontend dependencies
* transitive dependencies
* high-severity vulnerabilities
* critical vulnerabilities

High and critical vulnerabilities must block release unless the risk is documented and explicitly accepted.

---

# Hosted Secret Scanning

Hosted secret scanning must detect and block:

* provider API keys
* database credentials
* storage credentials
* session secrets
* worker credentials
* deployment tokens

If a secret is exposed, the incident response process must include immediate rotation and impact review.

---

# Production Rate Limits And Edge Controls

Security operations must define production controls for:

* login attempts
* password reset attempts
* import inspection
* import saving
* worker submission
* provider-backed extraction
* export generation
* monitoring reads

Rate-limit responses must use stable machine-readable error codes and must not expose source prose or full provider payloads.

---

# Security Monitoring Alerts

Security monitoring must alert on:

* repeated failed login attempts
* repeated API key failures
* cross-user authorization failures
* unusual import volume
* repeated provider failures
* repeated worker failures
* production configuration failures
* suspected secret exposure
* project or account deletion failures

Alerts must be metadata-only.

They must not include full manuscripts, full chapters, full AI responses, credentials, tokens, private URLs, hostnames, usernames, or machine-local paths.

---

# Incident Response Routing

Security operations must define:

* who receives vulnerability reports
* who receives production alerts
* who can rotate secrets
* who can disable provider-backed extraction
* who can pause public intake
* how users are notified if required
* where incident notes are stored
* how manuscript privacy is preserved during investigation

Incident response must protect user stories while still allowing containment and recovery.

---

# Public Beta Blockers

Public beta remains blocked until:

* hosted secret scanning is enabled and enforced
* push protection is enabled
* hosted dependency alerts are enabled
* protected branch rules are configured
* required CI release gates are configured as branch-protection requirements
* production rate limits are configured and tested
* production security monitoring alerts are configured
* incident response routing is documented
* security disclosure intake path is public
* hosted controls are verified on a release-candidate branch

Current implementation progress:

```text
.github/workflows/ci.yml defines backend and frontend release gates.
.github/workflows/security.yml defines repository secret scan, dependency audit, and static security scan gates.
.github/CODEOWNERS, .github/dependabot.yml, .github/SECURITY.md, and .github/PULL_REQUEST_TEMPLATE.md exist.
docs/AEVRYN_BRANCH_PROTECTION.md defines the protected branch posture and required hosted checks.
docs/AEVRYN_GITHUB_HOSTED_CONTROLS.md defines the exact GitHub hosted settings and protected-path drill.
Local repository secret scan, Ruff, and mypy passed before workflow creation.
GitHub branch protection is configured for master.
GitHub dependency graph, Dependabot alerts, Dependabot security updates, secret scanning, push protection, private vulnerability reporting, and default CodeQL are enabled.
Protected-path verification was exercised through PR #9: direct pushes to master were blocked, required hosted checks ran, hosted checks caught failures before merge, and final hosted checks passed after fixes.
Hosted alert routing remains open.
```

---

# Acceptance

Gate 4 is accepted when:

```text
Security checks, dependency alerts, branch protections, rate limits, monitoring alerts, and incident routing protect the hosted release path before public beta.
```

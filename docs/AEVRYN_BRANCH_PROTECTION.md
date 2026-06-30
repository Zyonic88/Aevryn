# Aevryn Branch Protection

> Built by **Aetherra Labs**

This document defines the hosted branch-protection posture required before public beta.

---

# Purpose

Branch protection turns Aevryn's local and hosted checks into a release boundary.

The goal is simple:

```text
Public-beta code must pass protected release gates before it can reach the protected branch.
```

This document is an operational runbook, not a product feature.

---

# Protected Branches

The protected branch set should include:

* `master`
* any future release-candidate branch used for public-beta signoff

If the repository later moves from `master` to `main`, the active default branch must receive the same protections.

---

# Required Status Checks

The protected branch should require these hosted checks:

* `Backend gates / Python 3.11`
* `Backend gates / Python 3.13`
* `Frontend gates`
* `Repository secret scan`
* `Dependency audit`
* `Static security scan`

These checks are defined by:

* `.github/workflows/ci.yml`
* `.github/workflows/security.yml`

Required checks must be kept in sync with workflow job names.

If a workflow job is renamed, branch protection must be updated in the same release-readiness slice.

The concrete hosted-settings checklist is tracked in `docs/AEVRYN_GITHUB_HOSTED_CONTROLS.md`.

---

# Required Pull Request Controls

Protected branches should require:

* pull request before merge
* required status checks before merge
* branches up to date before merge when practical
* conversation resolution before merge
* stale approval dismissal when important files change
* force pushes disabled
* branch deletion disabled

Bypass permissions must be narrow and auditable.

During early Aetherra Labs development, a single owner may hold multiple responsibilities, but the release record must still name the responsibility being accepted.

Repo-side support files:

* `.github/CODEOWNERS` defines current repository ownership.
* `.github/PULL_REQUEST_TEMPLATE.md` requires release-readiness and privacy notes on pull requests.

---

# Push Protection

Repository push protection should block committed secrets before they reach the protected branch.

Push protection must cover:

* provider API keys
* database credentials
* object-storage credentials
* session secrets
* worker credentials
* deployment tokens

If push protection blocks a commit, the secret must be rotated if it may have left the local machine or reached a remote.

---

# Dependency Alerts

Hosted dependency alerts should cover:

* Python dependencies
* frontend dependencies
* transitive dependencies
* high-severity vulnerabilities
* critical vulnerabilities

High and critical vulnerabilities must block public-beta release unless the project owner explicitly accepts the residual risk in the release-candidate record.

---

# Release Candidate Verification

Before public beta, a release-candidate branch or equivalent protected release path must prove:

* required checks run in GitHub
* required checks block merge on failure
* secret scanning runs without printing secrets
* dependency audits run without printing credentials
* static security scanning runs without source prose
* frontend build output is generated only as a CI artifact or ignored build output

This verification does not approve public beta by itself.

It only proves the release path is protected.

---

# Public Beta Blockers

Public beta remains blocked until:

* branch protection is enabled for the protected branch
* required checks above are configured in GitHub
* push protection is enabled
* dependency alerts are enabled
* bypass permissions are reviewed
* a protected release path has been exercised
* the release-candidate record confirms the controls worked

Current implementation progress:

```text
CI and security workflow files exist.
CODEOWNERS, Dependabot configuration, GitHub security policy, and pull request template exist.
Required hosted check names are documented.
GitHub hosted settings are not verified yet.
Protected-path verification drill remains open.
```

---

# Acceptance

Branch protection readiness is accepted when:

```text
Hosted checks and repository protections prevent unverified code from reaching the protected release branch.
```

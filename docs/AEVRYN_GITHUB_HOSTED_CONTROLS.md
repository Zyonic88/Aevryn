# Aevryn GitHub Hosted Controls

> Built by **Aetherra Labs**

This document tracks the GitHub-hosted controls required before Aevryn public beta.

The repository already defines CI and security workflows. GitHub still needs hosted repository settings that enforce those workflows before code can reach the protected branch.

---

# Status

```text
Gate: GitHub hosted controls
Status: Repo workflows ready; GitHub settings not verified
Public beta: Blocked
```

This gate is external because GitHub repository settings live outside source control.

---

# Core Rule

```text
Hosted controls must block unsafe release changes before they reach the protected branch.
```

Local checks are useful. Hosted checks are the release boundary.

---

# Required Workflow Checks

These job names must be configured as required status checks for `master`:

| Workflow | Required Check |
| --- | --- |
| `.github/workflows/ci.yml` | `Backend gates / Python 3.11` |
| `.github/workflows/ci.yml` | `Backend gates / Python 3.13` |
| `.github/workflows/ci.yml` | `Frontend gates` |
| `.github/workflows/security.yml` | `Repository secret scan` |
| `.github/workflows/security.yml` | `Dependency audit` |
| `.github/workflows/security.yml` | `Static security scan` |

If any workflow job is renamed, the GitHub branch protection rule must be updated in the same release-readiness slice.

---

# Branch Protection Settings

Configure the default branch protection rule for:

```text
master
```

Required settings:

| Setting | Required Value | Verification |
| --- | --- | --- |
| Require a pull request before merging | Enabled | Not verified |
| Require approvals | Enabled | Not verified |
| Dismiss stale approvals when new commits are pushed | Enabled where practical | Not verified |
| Require review from code owners | Optional until CODEOWNERS exists | Not applicable |
| Require status checks to pass before merging | Enabled | Not verified |
| Require branches to be up to date before merging | Enabled where practical | Not verified |
| Required status checks | Six checks listed above | Not verified |
| Require conversation resolution before merging | Enabled | Not verified |
| Lock branch | Disabled unless emergency freeze is needed | Not verified |
| Do not allow bypassing the above settings | Enabled where practical | Not verified |
| Restrict who can push to matching branches | Enabled if team membership is stable | Not verified |
| Allow force pushes | Disabled | Not verified |
| Allow deletions | Disabled | Not verified |

Bypass permissions must be narrow and auditable.

---

# Repository Security Settings

Required repository security posture:

| Setting | Required Value | Verification |
| --- | --- | --- |
| Secret scanning | Enabled | Not verified |
| Push protection | Enabled | Not verified |
| Dependabot alerts | Enabled | Not verified |
| Dependabot security updates | Enabled where practical | Not verified |
| Code scanning alerts | Enabled if GitHub Advanced Security or compatible scanner is available | Not verified |
| Private vulnerability reporting | Enabled if available | Not verified |

If a secret is blocked, rotate it if it may have left the local machine or reached a remote.

---

# Verification Drill

Before public beta, run a protected-path drill:

1. Create a release-candidate branch or pull request that targets `master`.
2. Confirm all six required status checks appear.
3. Confirm the pull request cannot merge while checks are pending.
4. Confirm a failing required check blocks merge.
5. Confirm conversation resolution is required.
6. Confirm direct pushes to `master` are blocked for non-bypass users.
7. Confirm force-push and branch deletion controls are disabled.
8. Record evidence links in `docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md`.

Do not include secrets, provider tokens, private URLs, full manuscripts, full chapters, full AI responses, or machine-local paths in evidence notes.

---

# Current Progress

```text
CI workflow exists.
Security workflow exists.
Required job names are documented.
GitHub branch protection settings remain unverified.
GitHub secret scanning, push protection, dependency alerts, and bypass permissions remain unverified.
Protected-path verification drill remains open.
```

---

# Acceptance

This gate is accepted when:

```text
GitHub hosted settings require the documented CI and security checks before code can reach the protected branch, and the protected-path drill proves those controls work.
```

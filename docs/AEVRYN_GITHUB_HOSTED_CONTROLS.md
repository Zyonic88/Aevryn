# Aevryn GitHub Hosted Controls

> Built by **Aetherra Labs**

This document tracks the GitHub-hosted controls required before Aevryn public beta.

The repository already defines CI and security workflows. GitHub still needs hosted repository settings that enforce those workflows before code can reach the protected branch.

---

# Status

```text
Gate: GitHub hosted controls
Status: GitHub branch and security settings configured; protected-path drill exercised
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
| Require a pull request before merging | Enabled | Configured |
| Require approvals | Enabled | Configured with 1 required approval |
| Dismiss stale approvals when new commits are pushed | Enabled where practical | Configured |
| Require review from code owners | Enabled once branch protection is configured | Configured |
| Require status checks to pass before merging | Enabled | Configured |
| Require branches to be up to date before merging | Enabled where practical | Configured |
| Required status checks | Six checks listed above | Configured |
| Require conversation resolution before merging | Enabled | Configured |
| Lock branch | Disabled unless emergency freeze is needed | Not verified |
| Do not allow bypassing the above settings | Enabled where practical | Not exposed in current GitHub branch-rule UI |
| Restrict who can push to matching branches | Enabled if team membership is stable | Not verified |
| Allow force pushes | Disabled | No allow-force-push option shown; protected branch defaults apply |
| Allow deletions | Disabled | Restrict deletions enabled |

Bypass permissions must be narrow and auditable.

---

# Repository Security Settings

Required repository security posture:

| Setting | Required Value | Verification |
| --- | --- | --- |
| Secret scanning | Enabled | Configured |
| Push protection | Enabled | Configured |
| Dependency graph | Enabled | Configured |
| Dependabot alerts | Enabled | Configured |
| Dependabot security updates | Enabled where practical | Configured |
| Code scanning alerts | Enabled if GitHub Advanced Security or compatible scanner is available | CodeQL default setup configured |
| Private vulnerability reporting | Enabled if available | Configured |

If a secret is blocked, rotate it if it may have left the local machine or reached a remote.

Repo-side support files now exist:

| File | Purpose |
| --- | --- |
| `.github/CODEOWNERS` | Names release ownership for code-owner review. |
| `.github/dependabot.yml` | Schedules Python, frontend, and GitHub Actions dependency update checks. |
| `.github/SECURITY.md` | Exposes security reporting guidance in GitHub. |
| `.github/PULL_REQUEST_TEMPLATE.md` | Keeps PR verification and release-readiness notes explicit. |

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

# Protected-Path Drill Record

Protected-path drill:

```text
Pull request: https://github.com/Zyonic88/Aevryn/pull/9
Target branch: master
Result: Required hosted checks passed after hosted-only failures were fixed.
```

Verified behavior:

* Direct push to `master` was blocked by GitHub branch protection.
* The pull request exposed all required hosted checks.
* Required backend gates failed when the hosted runner found CI workspace and compatibility issues.
* Static security scanning failed when the hosted runner found a `urlopen` review issue.
* Fixes were made on the pull request branch and rechecked by GitHub.
* Final hosted checks passed:
  * `Backend gates / Python 3.11`
  * `Backend gates / Python 3.13`
  * `Frontend gates`
  * `Repository secret scan`
  * `Dependency audit`
  * `Static security scan`
  * CodeQL default setup checks

Notes:

* Conversation resolution is configured in branch protection.
* Restricted deletions are configured.
* GitHub did not expose a separate bypass-control option in the current branch-rule UI.
* GitHub did not show an allow-force-push option in the current branch-rule UI.
* Require signed commits was disabled during the drill because local commit signing is not yet configured.

---

# Current Progress

```text
CI workflow exists.
Security workflow exists.
CODEOWNERS exists.
Dependabot configuration exists for Python, frontend, and GitHub Actions.
GitHub security policy exists and points to security@aevryn.ai.
Pull request template exists with verification and privacy checklist items.
Required job names are documented.
GitHub branch protection settings are configured for master.
GitHub secret scanning, push protection, dependency graph, Dependabot alerts, Dependabot security updates, private vulnerability reporting, and default CodeQL are enabled.
Bypass controls were not exposed in the current GitHub branch-rule UI.
Protected-path verification drill exercised through PR #9.
```

---

# Acceptance

This gate is accepted when:

```text
GitHub hosted settings require the documented CI and security checks before code can reach the protected branch, and the protected-path drill proves those controls work.
```

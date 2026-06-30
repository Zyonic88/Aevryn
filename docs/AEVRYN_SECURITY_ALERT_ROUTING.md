# Aevryn Security Alert Routing

> Built by **Aetherra Labs**

This document defines how Aevryn security, quality, and operational alerts are routed before public beta.

It is an operational runbook, not a product feature.

---

# Status

```text
Gate: Security Alert Routing
Status: Routing runbook documented; hosted delivery verification pending
Public beta: Blocked
```

Public beta remains blocked until hosted alert delivery is tested and recorded.

---

# Core Rule

```text
Alerts must route to a responsible human without exposing private user stories.
```

Alert routing must preserve Aevryn's privacy posture:

* no full manuscripts
* no full chapters
* no full AI responses
* no credentials
* no provider payloads
* no private URLs
* no machine-local paths

---

# Contact Channels

Primary public aliases:

* `support@aevryn.ai`
* `privacy@aevryn.ai`
* `security@aevryn.ai`
* `abuse@aevryn.ai`

Operational routing:

| Alert Type | Primary Route | Secondary Route | Notes |
| --- | --- | --- | --- |
| Security vulnerability report | `security@aevryn.ai` | `privacy@aevryn.ai` if user data may be involved | Preserve reporter context without requesting source prose. |
| Secret scanning alert | `security@aevryn.ai` | Project owner | Rotate exposed secret before investigation notes expand. |
| Code scanning high severity | `security@aevryn.ai` | Project owner | Treat as release-blocking until fixed or explicitly accepted. |
| Dependabot critical or high alert | `security@aevryn.ai` | Project owner | Release-blocking unless residual risk is accepted. |
| Repeated auth failures | `security@aevryn.ai` | `support@aevryn.ai` | Do not include passwords, tokens, or full request bodies. |
| Cross-user authorization failure | `security@aevryn.ai` | `privacy@aevryn.ai` | Treat as possible privacy incident until disproven. |
| Project or account deletion failure | `privacy@aevryn.ai` | `security@aevryn.ai` | Deletion failure is privacy-sensitive. |
| Production config failure | `security@aevryn.ai` | Project owner | Production should fail closed. |
| Repeated provider failures | `support@aevryn.ai` | `privacy@aevryn.ai` if payload handling is implicated | No full provider payloads in alerts. |
| Repeated worker failures | `support@aevryn.ai` | Project owner | Metadata-only workflow details. |
| Abuse report | `abuse@aevryn.ai` | `security@aevryn.ai` if platform attack is suspected | Do not request private manuscripts by default. |

If a report arrives at the wrong alias, Aetherra Labs routes it internally.

Users should not be asked to resend private story material.

---

# Severity Levels

## Critical

Examples:

* exposed production secret
* confirmed cross-user project access
* deletion failure involving active user data
* public exploit against authentication or authorization
* production configuration starts in an unsafe state

Required action:

```text
Triage immediately.
Contain before root-cause analysis.
Block public beta or pause public intake until resolved.
```

## High

Examples:

* high-severity CodeQL alert
* high or critical dependency alert
* repeated authorization failures
* suspected provider payload logging
* restore process exposes deleted active data

Required action:

```text
Triage same day.
Block release unless fixed or explicitly accepted as residual risk.
```

## Medium

Examples:

* repeated worker failures
* repeated provider timeouts
* import failures above normal user-error baseline
* monitoring data missing expected workflow state

Required action:

```text
Triage before release-candidate signoff.
Document user impact and mitigation.
```

## Low

Examples:

* documentation typo in public support guidance
* non-sensitive alert routing mismatch
* noisy but non-security operational warning

Required action:

```text
Resolve during normal readiness work.
Do not let low-severity alert noise hide higher-severity alerts.
```

---

# Alert Sources

Hosted sources expected before public beta:

* GitHub secret scanning
* GitHub push protection
* GitHub Dependabot alerts
* GitHub CodeQL code scanning
* GitHub Actions release gates
* production API logs
* production monitoring events
* worker failure metrics
* provider failure metrics
* support/security/privacy/abuse inboxes

Current repository-controlled sources:

* `.github/workflows/ci.yml`
* `.github/workflows/security.yml`
* `.github/dependabot.yml`
* `.github/SECURITY.md`
* `.github/CODEOWNERS`
* `aevryn.security.secret_scan`
* `aevryn production-config-check`

---

# Metadata-Only Alert Payloads

Allowed alert fields:

* alert type
* severity
* stable machine code
* request ID
* project ID when required for triage
* user ID when required for authorization or deletion triage
* timestamp
* route or subsystem
* concise failure summary
* affected dependency or rule ID
* GitHub alert URL
* workflow run URL

Disallowed alert fields:

* full uploaded story text
* full chapter text
* full AI response
* full provider prompt
* passwords
* API keys
* session tokens
* storage credentials
* private URLs
* hostnames
* usernames
* machine-local paths

---

# Triage Procedure

1. Classify severity.
2. Confirm whether user data, story privacy, deletion, authentication, authorization, or credentials are involved.
3. Contain first when the alert is critical.
4. Preserve only metadata needed to investigate.
5. Rotate secrets immediately if exposure is plausible.
6. Disable provider-backed extraction if provider payload privacy is implicated.
7. Pause public intake if users could be harmed.
8. Record the outcome in the release-candidate record or incident notes.
9. Update public/user communication only when required and only with privacy-preserving language.

---

# Incident Notes

Incident notes must be metadata-only.

They may include:

* timeline
* affected subsystem
* alert links
* stable IDs
* containment actions
* user impact category
* resolution
* residual risk decision

They must not include:

* source prose
* full AI payloads
* credentials
* tokens
* private support screenshots containing story text

Before public beta, incident notes may live in the release-candidate run record.

Before broader public launch, Aetherra Labs should choose a dedicated incident log system with access controls and retention rules.

---

# Verification Checklist

Before public beta:

* GitHub security alerts are visible to the project owner.
* CodeQL alerts are reviewed or fixed.
* Dependabot alerts are visible.
* Secret scanning and push protection are enabled.
* Security disclosure intake reaches `security@aevryn.ai`.
* Privacy/deletion reports reach `privacy@aevryn.ai`.
* Abuse reports reach `abuse@aevryn.ai`.
* Support reports reach `support@aevryn.ai`.
* At least one synthetic hosted alert or equivalent notification path is tested.
* Alert evidence is recorded without secrets or source prose.
* The release-candidate run record links this routing document.

---

# Current Progress

```text
Public aliases are provisioned and tested for inbound and outbound mail.
GitHub branch protection, secret scanning, push protection, Dependabot alerts, private vulnerability reporting, and default CodeQL are enabled.
Repository CI/security gates are configured and required on master.
Protected-path drill was exercised through PR #9.
Routing matrix is documented.
Hosted alert notification delivery test remains open.
```

---

# Acceptance

Security alert routing readiness is accepted when:

```text
Security, privacy, abuse, support, dependency, secret, code-scanning, CI, and production alerts route to a responsible human with metadata-only evidence and a tested escalation path.
```

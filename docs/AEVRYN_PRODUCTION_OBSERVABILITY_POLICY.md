# Aevryn Production Observability Policy

> Built by **Aetherra Labs**

This document defines the public-beta observability policy candidate for hosted Aevryn.

It does not approve public beta.

It turns the previous "broader observability policy" blocker into a concrete policy that can be verified against the hosted deployment.

---

# Status

```text
Decision: Production observability policy candidate
Status: Selected for owner/security review
Public beta: Blocked
```

---

# Core Rule

```text
Observability explains workflows without preserving user stories.
```

Logs, monitoring, traces, alerts, audit notes, and support diagnostics must remain metadata-only.

Observability must help Aevryn answer:

* what workflow ran
* which authenticated project boundary was involved
* whether the workflow succeeded, failed, or timed out
* what stable error code or summary explains the outcome
* whether storage, worker, provider, or API dependencies were reachable

Observability must not become a hidden copy of user manuscripts, provider payloads, exports, credentials, or local developer environment data.

---

# Allowed Hosted Observability Fields

Hosted logs, monitoring, traces, alerts, and release-candidate smoke records may contain:

* request ID
* route template
* HTTP method
* response status code
* elapsed milliseconds
* workflow kind
* stable machine error code
* concise user-safe failure summary
* project ID
* story ID
* import ID
* run ID
* snapshot ID
* export ID
* source format
* safe filename or user-visible import label
* source byte count
* chapter count
* scene count
* evidence-anchor count
* worker state
* queue depth
* retry count
* provider mode name
* provider timeout category
* storage adapter status
* deployment environment name

IDs and counts are operational metadata. They are allowed only inside authenticated ownership boundaries or operator-only hosted observability systems.

---

# Forbidden Hosted Observability Data

Hosted observability must not contain:

* full manuscripts
* full chapters
* private story prose
* full AI provider prompts
* full AI provider responses
* generated exports unless explicitly user-triggered in the product
* passwords
* password hashes
* session tokens
* bearer tokens
* API keys
* provider keys
* database URLs
* storage credentials
* private signed URLs
* unrelated project data
* support ticket bodies containing private story text
* hostnames from local developer machines
* usernames from local developer machines
* machine-local paths

Short evidence excerpts may exist in Canon-owned project data only where the Canon/evidence system explicitly preserves them. They must not be copied into logs or provider failure messages.

---

# Retention Candidate

For public beta, Aevryn should use this hosted observability retention posture unless final provider tooling requires a stricter window:

```text
Operational logs and traces: retain up to 30 days.
Security alerts and incident notes: retain up to 1 year.
Release-candidate smoke records: retain as engineering records without source prose.
Audit-ledger records: retain according to the audit policy, metadata-only.
```

The 30-day operational window is a maximum candidate, not a minimum. If hosted tooling safely supports shorter operational retention, Aevryn may choose a shorter disclosed or internal window.

---

# Access Boundary

Production observability access must be:

* limited to authorized operators
* protected by MFA on provider accounts
* used for debugging, security response, support escalation, reliability, and release verification
* reviewed during public-beta readiness
* revoked when no longer needed

Support workflows should start from redacted user reports and metadata-only status. Support must not ask users for full manuscripts unless a narrow excerpt is explicitly needed and the user chooses to provide it.

---

# Alerts

Alerts should route only metadata needed for triage.

Allowed alert examples:

* `provider_timeout` for extraction timeouts
* `storage_unavailable` for R2 failures
* `database_unavailable` for PostgreSQL failures
* `auth_invalid_token` for authentication failures
* `rate_limit_exceeded` for abuse controls
* `secret_scan_failure` for repository secret findings
* `dependency_vulnerability` for dependency alerts

Forbidden alert examples:

* full request bodies
* full manuscript excerpts
* full provider prompts
* full provider responses
* access tokens
* private signed URLs

---

# Smoke Verification

Before public beta, hosted observability must be checked with a bounded log review that records:

* environment
* revision or deployment identifier
* time window
* sampled line count or query boundary
* workflows exercised
* prohibited data checked
* result

The review must include at least:

* login or authenticated API protection
* import inspect
* save import
* processing run
* monitoring/status
* export creation if exports are enabled
* project deletion if deletion is in scope

Sampling does not prove every future log line is safe, so application-level metadata-only tests remain required.

Before the bounded hosted log review, run:

```powershell
python -m aevryn.cli observability-config-check
```

This command verifies the hosted log and monitoring destinations, operational
retention window, security alert flag, and metadata-only logging flag without
printing secrets. It does not inspect hosted log contents and does not replace
the bounded hosted log review.

The hosted production-like observability configuration gate passed on
2026-07-17 with metadata-only output:

```text
deployment_env=production
log_destination=hosted
monitoring_destination=hosted
log_retention_days=30
monitoring_retention_days=30
security_alerts_enabled=true
metadata_only_logging=true
bounded_hosted_log_review=required
public_beta=blocked_until_bounded_hosted_log_review
secrets_printed=0
ok=observability_config_contract_checked
```

This verifies configuration posture only. It does not replace the bounded hosted
log review.

The final bounded hosted observability review passed on 2026-07-24 against
Google Cloud Run service-log samples for `aevryn-api` in `us-central1`.

The sampled windows covered health checks, authenticated project reads, import
metadata, workflow status, export metadata, auth-denial metadata, worker/job
metadata, and project deletion metadata. The review found zero bearer tokens,
JWT-like tokens, provider keys, Cloudflare tokens, database URLs, R2
credentials, storage references, signed URLs, local machine paths, provider
payload terms, or source-story terms.

---

# Public-Beta Blockers

Public beta remains blocked until:

* this policy is reviewed by the owner/security role
* hosted log retention is configured or documented
* hosted monitoring retention is configured or documented
* security alert routing is confirmed
* bounded hosted log review evidence remains current after the final public-beta deployment
* application tests continue proving no source prose, full provider payloads, or secrets enter logs
* support procedure remains aligned with metadata-only diagnostics

---

# Acceptance

This policy is accepted when:

```text
Aevryn can observe production workflows, debug failures, and route alerts without preserving user stories, full provider payloads, generated exports, credentials, or local developer environment data in hosted observability systems.
```

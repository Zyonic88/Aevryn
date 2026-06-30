# Aevryn Release Candidate Run Record

> Built by **Aetherra Labs**

Use this document to record the final V2 release-candidate pass before public beta.

This is a template until a real run is completed.

---

# Run Status

```text
Record type: Release Candidate Run Template
Status: Not run
Public beta: Blocked
```

Public beta is approved only after this record is completed, reviewed, and signed off.

---

# Run Metadata

Release Candidate Run ID:

```text
rc-v2-YYYY-MM-DD-001
```

Date:

```text
TBD
```

Tester:

```text
TBD
```

Commit:

```text
TBD
```

Environment:

```text
TBD - staging, release-candidate, or other production-like environment.
```

Provider mode:

```text
TBD - deterministic, openai, or disabled.
```

Imported content:

```text
TBD - synthetic, owner-approved test chapters, or other approved test source.
```

Result:

```text
Not run.
```

Public beta decision:

```text
Blocked.
```

---

# Automated Gate Record

Record each command or hosted check with result, run location, and evidence link if available.

| Gate | Required Result | Actual Result | Evidence |
| --- | --- | --- | --- |
| Backend tests | Pass | TBD | TBD |
| Backend lint | Pass | TBD | TBD |
| Backend typing | Pass | TBD | TBD |
| Frontend tests | Pass | TBD | TBD |
| Frontend lint | Pass | TBD | TBD |
| Frontend production build | Pass | TBD | TBD |
| Repository secret scan | Pass | TBD | TBD |
| Dependency audit | Pass or accepted residual risk | TBD | TBD |
| Static security scan | Pass or accepted residual risk | TBD | TBD |
| Performance regression check | Pass or accepted residual risk | TBD | TBD |
| Release-readiness document tests | Pass | TBD | TBD |
| Production config check | `startup_contract=ready`, `secrets_printed=0` | TBD | TBD |

Failures block public beta unless an owner-approved residual risk is recorded below.

---

# Product Smoke Record

| Step | Required Result | Actual Result | Notes |
| --- | --- | --- | --- |
| Register or log in | User reaches dashboard | TBD | TBD |
| Create project | Project opens in workspace | TBD | TBD |
| Create or select story | Story context is usable | TBD | TBD |
| Upload supported files | Upload succeeds without source-prose leakage | TBD | TBD |
| Inspect import | Structure preview is readable | TBD | TBD |
| Save import | Import persists | TBD | TBD |
| Submit processing | Run is queued once | TBD | TBD |
| Observe run state | Status is API-provided | TBD | TBD |
| Process queued work | Worker completes or fails clearly | TBD | TBD |
| Observe snapshot availability | Snapshot state is visible | TBD | TBD |
| Review Characters | Human-readable output appears | TBD | TBD |
| Review World | Human-readable output appears | TBD | TBD |
| Review Timeline | Chapter changes are understandable | TBD | TBD |
| Review Scenes | Scene sheets are understandable | TBD | TBD |
| Review Continuity | Continuity view is understandable | TBD | TBD |
| Review Prompt Packs | Prompt output is usable or limitation is documented | TBD | TBD |
| Review Exports | Export options are visible | TBD | TBD |
| Create export preview | Preview is generated intentionally | TBD | TBD |
| Delete project | Project data is removed from active product surfaces | TBD | TBD |

The smoke path must not require CLI knowledge from the tester.

---

# Recovery Record

| Check | Required Result | Actual Result | Notes |
| --- | --- | --- | --- |
| Browser refresh | Workspace restores from API-backed state | TBD | TBD |
| Session expiry | User can log in again without corrupting workspace | TBD | TBD |
| API outage messaging | User sees actionable error state | TBD | TBD |
| Failed run visibility | Failure summary is concise and useful | TBD | TBD |
| Retry after failed run | User can continue or limitation is explicit | TBD | TBD |
| Stale worker/job handling | State is observable and not blocking forever | TBD | TBD |
| Import retry after failure | User can retry without duplicate stuck state | TBD | TBD |
| Project deletion completion | Deleted project is unavailable | TBD | TBD |
| Monitoring accuracy | Frontend displays API-provided state only | TBD | TBD |
| No frontend-inferred workflow state | No client-side invented backend state | TBD | TBD |

For each recovery check, answer:

```text
Can the user continue?
```

---

# Privacy And Trust Record

Verify no test output exposes:

* full manuscripts
* full chapters
* full AI responses
* full provider prompts
* full export content unless explicitly previewed
* credentials
* tokens
* private URLs
* hostnames
* usernames
* machine-local paths

| Surface | Required Result | Actual Result | Notes |
| --- | --- | --- | --- |
| Logs | Metadata-only | TBD | TBD |
| Monitoring | Metadata-only | TBD | TBD |
| Audit records | Metadata-only | TBD | TBD |
| Error messages | Concise and source-prose-free | TBD | TBD |
| Support guidance | Redaction guidance present | TBD | TBD |
| Browser UI | No unnecessary machine noise | TBD | TBD |
| Export preview | User-triggered only | TBD | TBD |
| Provider failures | No full provider payloads | TBD | TBD |

---

# Production-Like Smoke Record

| Check | Required Result | Actual Result | Notes |
| --- | --- | --- | --- |
| Production config fails closed | Missing required settings block startup | TBD | TBD |
| CORS origins | Explicit HTTPS origins only | TBD | TBD |
| HTTPS behavior | Edge behavior documented and tested | TBD | TBD |
| Protected workflow routes | Unauthorized requests fail closed | TBD | TBD |
| Storage references | Resolve inside project ownership boundaries | TBD | TBD |
| Worker processing | Completes in production-like environment | TBD | TBD |
| Monitoring | Observes workflow state | TBD | TBD |
| Export preview | Works with production storage boundary | TBD | TBD |
| Logs | Metadata-only | TBD | TBD |

This does not require public launch, but it must run outside the purely local private-alpha path.

---

# Known Limitations

Record every limitation discovered during the release-candidate pass.

```text
TBD
```

---

# Accepted Residual Risks

Public beta may proceed only if each residual risk is explicit and accepted by the project owner.

| Risk | Impact | Mitigation | Owner Decision |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

If a risk touches story privacy, deletion, account security, provider training, or data ownership, the default decision should be block.

---

# Signoff

| Responsibility | Decision | Signoff | Date |
| --- | --- | --- | --- |
| Product | TBD | TBD | TBD |
| Security | TBD | TBD | TBD |
| Privacy | TBD | TBD | TBD |
| Legal | TBD | TBD | TBD |
| Operations | TBD | TBD | TBD |
| Support | TBD | TBD | TBD |

If one person holds multiple responsibilities, each responsibility must still be explicitly accepted.

---

# Final Decision

```text
Public beta: Blocked
Reason: Release candidate run has not been completed.
```

---

# Acceptance

This run record is accepted when:

```text
The release-candidate pass is complete, privacy-preserving, repeatable, and signed off with all residual risks resolved or explicitly accepted.
```

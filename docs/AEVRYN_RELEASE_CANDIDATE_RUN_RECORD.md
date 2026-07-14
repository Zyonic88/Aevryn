# Aevryn Release Candidate Run Record

> Built by **Aetherra Labs**

Use this document to record the final V2 release-candidate pass before public beta.

This record captures the July 14, 2026 internal release-candidate signoff.

---

# Run Status

```text
Record type: Release Candidate Run Record
Status: Completed
Internal release candidate: Signed off
Public beta: Blocked
```

The internal V2 release-candidate pass is complete.

Public beta is not approved by this record. Public beta still requires the remaining public-launch, legal, observability, and external-readiness work documented below.

---

# Run Metadata

Release Candidate Run ID:

```text
rc-v2-2026-07-14-001
```

Date:

```text
2026-07-14
```

Tester:

```text
Aetherra Labs project owner with Codex-assisted verification.
```

Commit:

```text
f5c19d7e9fc6a7d25139b453590b09dbf48108bd
```

Environment:

```text
Hosted production-like environment:
Frontend: https://app.aevryn.ai
API: https://api.aevryn.ai
API runtime: Google Cloud Run
Frontend runtime: Cloudflare Pages
Database: PostgreSQL
Storage: private Cloudflare R2
Identity: Supabase managed identity
```

Provider mode:

```text
Hosted configured provider mode using OpenAI extraction.
```

Imported content:

```text
Owner-approved internal test chapters.
10 TXT chapters.
82,024 bytes.
```

Result:

```text
Internal release-candidate pass completed.
Public beta remains blocked.
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
| Backend tests | Pass | Passed | GitHub PR #74 and PR #75 backend matrix checks passed for Python 3.11 and Python 3.13 |
| Backend lint | Pass | Passed | `python -m ruff check .` passed locally and in PR #74/#75 backend checks |
| Backend typing | Pass | Passed | Backend CI gates passed in PR #74 and PR #75 |
| Frontend tests | Pass | Passed | Frontend gates passed in PR #74 and PR #75 |
| Frontend lint | Pass | Passed | Frontend gates passed in PR #74 and PR #75 |
| Frontend production build | Pass | Passed | Cloudflare Pages build passed in PR #74 and PR #75 |
| Repository secret scan | Pass | Passed | Repository secret scan passed in PR #74 and PR #75 |
| Dependency audit | Pass or accepted residual risk | Passed | Dependency audit passed in PR #74 and PR #75 |
| Static security scan | Pass or accepted residual risk | Passed | Static security scan passed in PR #74 and PR #75 |
| Performance regression check | Pass or accepted residual risk | Accepted residual risk | No new performance code changed in final signoff records; hosted ten-chapter workflow completed |
| Release-readiness document tests | Pass | Passed | `python -m pytest tests/test_trust_documents.py -q` passed |
| Production config check | `startup_contract=ready`, `secrets_printed=0` | Passed previously | Recorded in `docs/AEVRYN_PRODUCTION_LIKE_SMOKE_RECORD.md` |

Failures block public beta unless an owner-approved residual risk is recorded below.

---

# Product Smoke Record

| Step | Required Result | Actual Result | Notes |
| --- | --- | --- | --- |
| Register or log in | User reaches dashboard | Passed | Managed identity login completed |
| Create project | Project opens in workspace | Passed | Smoke project created and opened |
| Create or select story | Story context is usable | Passed | Story context selected |
| Upload supported files | Upload succeeds without source-prose leakage | Passed | 10 owner-approved TXT chapters selected |
| Inspect import | Structure preview is readable | Passed | 10 chapters, 19 scenes, 327 paragraphs, 1,296 evidence anchors |
| Save import | Import persists | Passed | Saved as `Chapter import` |
| Submit processing | Run is queued once | Passed | One processing run created from one submit action |
| Observe run state | Status is API-provided | Passed | Run stepper and Monitoring reflected API state |
| Process queued work | Worker completes or fails clearly | Passed | Retry run succeeded after timeout hardening |
| Observe snapshot availability | Snapshot state is visible | Passed | Canon snapshot ready |
| Review Characters | Human-readable output appears | Passed with limitation | Character output appears; identity-review summaries remain repetitive |
| Review World | Human-readable output appears | Passed with limitation | World output appears; some Unknown/No-data states remain evidence-driven |
| Review Timeline | Chapter changes are understandable | Passed with limitation | Timeline output appears; polish remains future UX work |
| Review Scenes | Scene sheets are understandable | Passed with limitation | Scene output appears; some incomplete evidence states remain |
| Review Continuity | Continuity view is understandable | Passed with limitation | Continuity output appears; layout polish remains future UX work |
| Review Prompt Packs | Prompt output is usable or limitation is documented | Passed with limitation | Prompt Packs load; prompt richness remains active product-hardening work |
| Review Exports | Export options are visible | Passed | `Create snapshot export` action visible |
| Create export preview | Preview is generated intentionally | Passed | JSON canon snapshot export created with download action |
| Delete project | Project data is removed from active product surfaces | Passed | Smoke project deleted; dashboard showed 2 projects and direct project URL returned dashboard |

The smoke path must not require CLI knowledge from the tester.

---

# Recovery Record

| Check | Required Result | Actual Result | Notes |
| --- | --- | --- | --- |
| Browser refresh | Workspace restores from API-backed state | Passed | Monitoring restored succeeded state after refresh |
| Session expiry | User can log in again without corrupting workspace | Passed | Managed identity login was used repeatedly during hosted testing |
| API outage messaging | User sees actionable error state | Passed with limitation | Previous hosted-safe API wording was hardened; no outage appeared in final smoke |
| Failed run visibility | Failure summary is concise and useful | Passed | Earlier timeout failure produced concise retry guidance |
| Retry after failed run | User can continue or limitation is explicit | Passed | Retry succeeded after timeout hardening |
| Stale worker/job handling | State is observable and not blocking forever | Passed | Final run completed; worker idle in Monitoring |
| Import retry after failure | User can retry without duplicate stuck state | Passed | One run appeared from one submit action |
| Project deletion completion | Deleted project is unavailable | Passed | Deleted smoke project no longer appeared; direct URL returned dashboard |
| Monitoring accuracy | Frontend displays API-provided state only | Passed | Monitoring showed status, worker, snapshot, export, and events from API |
| No frontend-inferred workflow state | No client-side invented backend state | Passed | No browser-side worker draining was used in hosted flow |

For each recovery check, answer:

```text
Can the user continue? Yes for the checked release-candidate path.
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
| Logs | Metadata-only | Passed | Bounded Cloud Run log review found route-level metadata only |
| Monitoring | Metadata-only | Passed | Monitoring exposed status, counts, events, and summaries only |
| Audit records | Metadata-only | Passed with limitation | Workflow events were metadata-only; broader audit-storage policy remains public-beta work |
| Error messages | Concise and source-prose-free | Passed | Timeout failure summary was concise and source-prose-free |
| Support guidance | Redaction guidance present | Passed with limitation | Public support page is published; support procedure owner review remains open |
| Browser UI | No unnecessary machine noise | Passed with limitation | Known internal IDs and bundle names absent; some repetitive identity-review metadata remains |
| Export preview | User-triggered only | Passed | Export was created only after explicit user-authorized click |
| Provider failures | No full provider payloads | Passed | No full provider payload surfaced in UI or sampled logs |

---

# Production-Like Smoke Record

| Check | Required Result | Actual Result | Notes |
| --- | --- | --- | --- |
| Production config fails closed | Missing required settings block startup | Passed | Recorded in production-like smoke record |
| CORS origins | Explicit HTTPS origins only | Passed | API CORS allowed `https://app.aevryn.ai` |
| HTTPS behavior | Edge behavior documented and tested | Passed | `app.aevryn.ai` and `api.aevryn.ai` returned HTTPS OK |
| Protected workflow routes | Unauthorized requests fail closed | Passed | Unauthenticated API project route returned `401 session_required` |
| Storage references | Resolve inside project ownership boundaries | Passed | R2 smoke and hosted export creation used storage boundaries |
| Worker processing | Completes in production-like environment | Passed | Hosted ten-chapter retry succeeded |
| Monitoring | Observes workflow state | Passed | Status, snapshot, export, failure, and workflow events were visible |
| Export preview | Works with production storage boundary | Passed | Hosted JSON snapshot export created |
| Logs | Metadata-only | Passed with limitation | Route-level metadata appears in access logs; no prose, payloads, secrets, or local paths found |

This does not require public launch, but it must run outside the purely local private-alpha path.

---

# Known Limitations

```text
Prompt Packs load and are usable for alpha/RC verification, but prompt richness still needs product hardening before public beta positioning.
Identity review summaries appear across several output tabs and should be condensed in UX hardening.
Some Unknown/No-data states remain where accepted canon evidence is incomplete.
Settings and broader user profile preferences remain intentionally minimal.
Initial public trust/legal/support pages are published; owner/legal review and final public-beta approval remain incomplete.
Production observability policy candidate is selected, but hosted retention configuration and final bounded log review remain incomplete before public beta.
AI provider disclosure candidate is selected, but provider terms, final model configuration, and public-beta provider verification remain incomplete.
```

---

# Accepted Residual Risks

Public beta may proceed only if each residual risk is explicit and accepted by the project owner.

| Risk | Impact | Mitigation | Owner Decision |
| --- | --- | --- | --- |
| Prompt richness is still below final product ambition | Generated image/video prompts may need user editing | Continue prompt-pack hardening before beta marketing claims | Accepted for internal RC only; blocks public-beta positioning if not improved |
| Output UX polish remains alpha-grade in some tabs | Users may find repeated summaries or dense cards tiring | Continue UX hardening before broad public beta | Accepted for internal RC only |
| Public legal/trust/support pages need owner and legal review | Public users may see draft wording that is not public-beta approved | Review public-facing site/legal docs before public beta | Blocks public beta |
| Production observability policy needs hosted verification | Hosted logging and monitoring retention need final public-beta verification | Verify hosted retention, alert routing, and bounded log review against the selected production observability policy | Blocks public beta |
| Backup retention wording needs production verification | Users need accurate deletion and backup expectations | Verify the selected public-beta backup wording against final production backup behavior | Blocks public beta |
| AI provider disclosure needs provider verification | Users need accurate expectations for when story excerpts leave Aevryn-owned systems | Verify provider terms, retention, training behavior, abuse monitoring, and final model configuration against the selected disclosure candidate | Blocks public beta |
| Restore/audit drill has not run | Recovery confidence is incomplete for public users | Complete a dated restore/audit drill record proving ownership, deletion, audit integrity, and metadata-only restore logs | Blocks public beta |
| Audit-storage policy is selected but not implemented or verified | Audit confidence is incomplete for public users | Implement the production audit adapter, wire API/worker events, verify retention and access controls, add release-gate integrity verification, and complete the restore/audit drill | Blocks public beta |

If a risk touches story privacy, deletion, account security, provider training, or data ownership, the default decision should be block.

---

# Signoff

| Responsibility | Decision | Signoff | Date |
| --- | --- | --- | --- |
| Product | Accepted for internal V2 release-candidate checkpoint; public beta blocked by listed product polish and public-surface work | Aetherra Labs project owner | 2026-07-14 |
| Security | Accepted for internal V2 release-candidate checkpoint; public beta blocked by hosted observability verification and operations policy | Aetherra Labs project owner | 2026-07-14 |
| Privacy | Accepted for internal V2 release-candidate checkpoint; public beta blocked until public trust/legal/support review is complete | Aetherra Labs project owner | 2026-07-14 |
| Legal | Not approved for public beta; legal documents require owner and attorney review before public launch | Aetherra Labs project owner | 2026-07-14 |
| Operations | Accepted for internal V2 release-candidate checkpoint; public beta blocked by backup verification, restore/audit, and hosted observability follow-up | Aetherra Labs project owner | 2026-07-14 |
| Support | Accepted for internal V2 release-candidate checkpoint; public beta blocked until public support procedure owner review is complete | Aetherra Labs project owner | 2026-07-14 |

If one person holds multiple responsibilities, each responsibility must still be explicitly accepted.

---

# Final Decision

```text
Internal V2 release candidate: Signed off
Public beta: Blocked
Reason: The hosted release-candidate smoke path, monitoring, export creation, deletion cleanup, CI/security gates, bounded log review, and initial public page publication passed. Public beta remains blocked by public-facing legal/trust/support review, hosted observability verification, backup retention verification, AI provider verification, restore/audit readiness, prompt-pack polish, and final public-beta approval.
```

---

# Acceptance

This run record is accepted when:

```text
The release-candidate pass is complete, privacy-preserving, repeatable, and signed off with all residual risks resolved or explicitly accepted.
```

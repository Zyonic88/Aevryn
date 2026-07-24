# Aevryn V2 Remaining Work

> Built by **Aetherra Labs**

This document is the working backlog for finishing Aevryn Version 2 release readiness.

It separates:

* public beta blockers
* engineering hardening
* product polish
* owner/legal/external verification
* work that should stay out of V2

---

# Status

```text
V2 product scope: Accepted for release-candidate readiness
Internal release candidate: Signed off
Public beta: Blocked
Version 3: Not started
```

V2 is not done until Aevryn is feature-complete, fully functional within beta parameters, and a product Aetherra Labs can stand behind.

---

# Core Rule

```text
Public beta requires verified trust, not optimistic intent.
```

Every remaining item must end in one of three states:

* done and verified
* explicitly accepted as residual beta risk
* moved out of V2 with a documented reason

Silent assumptions are not acceptable.

---

# Public Beta Blockers

These block public beta unless resolved or explicitly accepted as residual risk.

## 1. Public Legal Review

Status:

```text
Open
```

Required:

* review Terms of Service
* review Privacy Policy
* review Acceptable Use Policy
* review Security Disclosure
* add final contact/legal information
* select and confirm governing-law language
* confirm warranty/liability language

Tracking:

* `docs/TERMS_OF_SERVICE.md`
* `docs/PRIVACY_POLICY.md`
* `docs/ACCEPTABLE_USE_POLICY.md`
* `docs/SECURITY_DISCLOSURE.md`
* `docs/AEVRYN_PUBLIC_BETA_SETUP_CHECKLIST.md`

Acceptance:

```text
Public legal pages are owner-reviewed and attorney-reviewed, or public beta remains blocked.
```

## 2. Public Trust And Support Review

Status:

```text
Open
```

Required:

* confirm public trust page wording
* confirm privacy/user-rights wording
* confirm support procedure
* confirm source-prose redaction guidance
* confirm abuse-report path
* confirm account/project deletion support language
* verify contact aliases still work

Tracking:

* `docs/AEVRYN_PUBLIC_TRUST_READINESS.md`
* `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`
* `docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md`
* `docs/AEVRYN_PUBLIC_CONTACTS.md`
* `docs/AEVRYN_PUBLIC_BETA_SETUP_CHECKLIST.md`

Acceptance:

```text
Users can understand their rights, get help, report abuse, and contact Aetherra Labs without exposing manuscripts unnecessarily.
```

## 3. AI Provider Review

Status:

```text
Open
```

Required:

* verify final model configuration
* verify provider data-retention behavior
* verify provider training behavior
* verify abuse-monitoring behavior
* verify response-storage/request-storage posture
* confirm no-training-by-default public language
* rerun provider config check after final provider settings

Tracking:

* `docs/AEVRYN_AI_PROVIDER_REVIEW.md`
* `docs/AEVRYN_AI_PROVIDER_DATA_USE_READINESS.md`
* `docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md`

Acceptance:

```text
Users can understand when story excerpts leave Aevryn-owned systems and what the selected provider may do with them.
```

## 4. Hosted Observability Review

Status:

```text
Open
```

Required:

* final bounded hosted log review
* confirm metadata-only logs
* confirm no manuscripts, chapters, AI payloads, tokens, private URLs, hostnames, usernames, or machine-local paths
* confirm monitoring remains workflow-observation only
* record final hosted evidence

Tracking:

* `docs/AEVRYN_PRODUCTION_OBSERVABILITY_POLICY.md`
* `docs/AEVRYN_PRODUCTION_LIKE_SMOKE_RECORD.md`
* `docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md`

Acceptance:

```text
Hosted logs and monitoring are metadata-only and safe for public-beta operations.
```

## 5. Backup Retention Public Wording

Status:

```text
Open
```

Required:

* confirm final production backup behavior
* confirm backup retention window
* confirm what project deletion removes immediately
* confirm what may remain temporarily in backups
* align public privacy/user-rights wording with actual behavior

Tracking:

* `docs/AEVRYN_BACKUP_RETENTION.md`
* `docs/AEVRYN_BACKUP_RETENTION_DECISION.md`
* `docs/AEVRYN_BACKUP_RECOVERY_AUDIT_READINESS.md`
* `docs/DATA_RETENTION_POLICY.md`

Acceptance:

```text
Deletion and backup language is truthful, conservative, and consistent across public documents.
```

## 6. Final Public Beta Signoff

Status:

```text
Open
```

Required:

* final automated gates pass
* final hosted smoke pass
* final manual browser pass
* final residual risks accepted or resolved
* product/security/privacy/legal/operations/support signoff updated

Tracking:

* `docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md`
* `docs/AEVRYN_RELEASE_CANDIDATE_TEST_READINESS.md`

Acceptance:

```text
The release record truthfully says Public beta: Approved.
```

---

# Engineering Hardening Backlog

These are practical code/docs hardening items still worth doing before public beta.

## A. Prompt Packs

Status:

```text
In progress
```

Remaining hardening:

* run hosted browser validation against the current prompt-pack output
* ~~confirm prompts include enough scene-specific action, setting, character, and object context~~
* ~~ensure normal prompt-pack presentation does not include raw manuscript prose~~
* ~~ensure normal prompt-pack presentation does not expose evidence anchors, import bundle IDs, source IDs, or internal placeholders~~
* ~~keep prompt bodies collapsed by default~~
* ~~make copy/export affordances obvious~~
* ~~keep production-batching out of V2 unless explicitly re-scoped~~

Verified hardening:

* production prompts include compact accepted character-card identity references
  such as aliases, titles, roles, professions, and descriptions when Canon has them
* identity references are treated as identity aids only and explicitly must not create
  extra characters
* verified with prompt-builder, prompt-engine, scene-context, presentation, and
  project-runner tests
* prompt sections expose visible copy and local text-download actions for each
  prompt body without calling a backend export path
* verified with prompt-download unit tests, focused prompt workspace test, full
  frontend test suite, lint, and production build
* prompt bodies are collapsed by default and expose bounded previews before expansion
* verified with focused prompt scene-picker test and prompt-download/readable-output
  unit tests
* browser-facing snapshot prompt items exclude exact imported sentences, source IDs,
  chapter/scene ID fragments, evidence-anchor labels, and short provider entity IDs
* verified with background-worker presentation payload tests and presentation-engine tests
* prompt-builder regression coverage requires every prompt type to preserve scene
  production brief, current action beats, character presence, setting, and
  scene-relevant object/world context when Canon provides it
* prompt workspace regression coverage verifies V2 does not expose batch-generation,
  credits, subscription, or paid production controls in Prompt Packs
* narration prompts now carry the same per-character known/missing visual identity
  boundary as visual prompt types, keeping cross-prompt character appearance
  handling Canon-bounded instead of inferred
* frontend prompt rendering filters internal source IDs, import IDs, evidence
  anchors, bundle IDs, and chapter/scene machine tokens before display, copy,
  or local text download while preserving human Canon prompt details
* verified with readable-output unit tests and focused Prompt Packs workspace
  tests

Acceptance:

```text
Prompt Packs are useful for beta without promising one-click perfect image/video generation.
```

## B. Continuity Readability

Status:

```text
Improved; final browser validation remains
```

Verified evidence:

* collapsed scene summaries now include the first visible change before detail expansion
* normal output uses "retained canon" instead of "still known" wording
* continuity details remain collapsed and paginated
* normal continuity output hides source IDs, chapter/scene ID fragments,
  evidence-anchor IDs, fact record IDs, and raw source identifiers
* verified with the frontend alpha smoke test across workspace surfaces

Remaining hardening:

* ~~keep scene-level continuity highlights scannable~~
* keep large buckets collapsed during hosted browser validation
* continue reducing repeated or low-value retained-canon noise when new examples appear
* ~~verify no raw IDs appear in normal user view~~
* verify continuity remains Canon-backed and does not invent explanations

Verified hardening:

* normal continuity output shows scene-level summaries with the first visible
  new/changed Canon highlight before expansion
* continuity preview keeps full change buckets collapsed and retained-canon
  detail nested, while retained-canon Markdown examples remain bounded
* processed-output and preview continuity buckets cap retained-record detail
  lists and show hidden-record counts, so large projects stay readable without
  pretending overflow does not exist

Acceptance:

```text
Continuity answers "What changed?" without forcing users to read machine-like lists.
```

## C. Character And Entity Resolution Output

Status:

```text
Improved; final browser validation remains
```

Verified evidence:

* character card bodies remain collapsed with neutral placeholder portraits
* Recent Changes no longer repeats identity/profile facts already represented in card sections
* identity/profile facts remain visible in their dedicated sections instead of being hidden

Remaining hardening:

* continue reducing duplicate character cards caused by aliases/titles/descriptions
* keep ambiguous identity references visible for review instead of force-merging
* ensure race/gender remain Canon-truthful and not story-specific guesses
* ~~keep character card sections collapsed and readable~~
* ~~ensure character portraits remain neutral placeholders until a real portrait/reference system exists~~
* ~~verify no source-backed placeholder text leaks into user output~~

Verified hardening:

* processed character panels hide the source-backed evidence placeholder from
  normal user output
* identity review hides evidence anchors and raw scene IDs while keeping ambiguous
  and unresolved references visible for review
* character cards and developer-preview cards use neutral initials placeholders
  without rendering fake portrait images before a real portrait/reference system
  exists
* extraction rejects plural race/gender group phrases as character cards while
  preserving singular unnamed character candidates when evidence supports them
* entity resolution keeps pronouns, shared honorifics, near-tied matches, and
  low-confidence descriptions ambiguous instead of force-merging identities
* entity resolution and project-runner tests resolve title-plus-name references
  such as General Charlotte to the existing Canon identity when the title/name
  support is explicit, while keeping shared titles ambiguous
* project-runner identity profiles preserve explicit relationship labels such as
  "sister of Zhao Chen," allowing possessive references like "Zhao Chen's sister"
  to resolve to an existing identity without creating duplicate character cards
* project-runner gender-support terms recognize accented fiancee/fiance
  spellings the same way as unaccented spellings, so translated or polished
  prose does not lose conservative pronoun support
* character profiles and stored snapshot API output hide contradictory
  Human-plus-non-human race/species values instead of displaying both as Canon
* verified with the focused processed-character-panel frontend test

Acceptance:

```text
Characters are readable and honest even when identity resolution is uncertain.
```

## D. World Classification

Status:

```text
In progress
```

Remaining hardening:

* reduce incorrect item/skill/location/organization categorization where evidence supports a better class
* avoid tailoring classification to one novel
* ~~preserve uncertain classifications as reviewable instead of pretending certainty~~
* ~~use sentence-level meaning signals as routing metadata without making them Canon truth~~
* ~~keep world cards collapsed and searchable/scannable~~

Verified hardening:

* deterministic extraction guard rejects quests, rewards, points, ranks, titles, roles,
  professions, and similar non-capability story concepts when they are incorrectly
  proposed as skills without explicit ability language
* verified with extraction, evidence-bounded extraction, world, and project-runner tests
* frontend readable-output formatter strips every supported Canon entity-type prefix
  from relationship and accepted-entity text, including system, weapon, armor,
  creature, vehicle, and timeline-event IDs
* normal World output is searchable, keeps world cards collapsed, and hides raw
  source IDs, entity IDs, chapter-scene fragments, and evidence anchors in the
  frontend alpha smoke path
* verified with readable-output frontend unit test, lint, and production build
* sentence understanding routes item, skill, system, location, and organization
  cues as metadata-only guidance; mixed or ambiguous cues remain reviewable
  instead of becoming Canon truth
* system reward, mission, quest, and points language is treated as system context
  rather than a usable skill unless the evidence explicitly describes an ability
* system UI plus skill/ability cues are marked reviewable instead of being treated
  as settled meaning
* system-created physical objects such as technical blueprints remain item
  candidates when evidence supports a concrete object classification
* physical skill-source phrases such as skill book, spell book, skill manual, and
  technique manual route as item context instead of automatically becoming usable
  skills, while separate skill cues in the same sentence remain reviewable
* system-resource phrases such as skill points and experience points route as
  system context rather than usable skills, while separate ability cues in the
  same sentence remain visible and reviewable
* physical skill-source scrolls route as item context rather than automatically
  becoming usable skills
* verified with sentence-understanding, extraction, and evidence-bounded AI
  extraction tests

Acceptance:

```text
World output is story-neutral, Canon-truthful, and useful for beta review.
```

## E. Import And Processing UX

Status:

```text
Mostly hardened
```

Remaining hardening:

* ~~verify multi-file import remains stable with 10-chapter and larger imports~~
* ~~verify duplicate processing submissions are blocked~~
* ~~verify stuck jobs do not block future imports forever~~
* ~~keep progress stepper accurate and API-provided~~
* ~~avoid fake percentages when exact progress is unavailable~~
* ~~keep import warnings human-readable~~

Verified hardening:

* hosted browser sessions submit processing to the API and do not drain worker
  jobs locally
* saved import processing state remains scoped to the submitted import row, so
  one stuck/submitting import does not make every saved import look active
* missing or stale queue jobs are marked failed with retryable, human-readable
  summaries instead of leaving durable runs pending forever
* active processing displays API-backed states such as Queued, Processing,
  Snapshot, and Output ready without fake percentages
* deferred source formats, source-format API failures, oversized pasted imports,
  and failed re-inspection paths show user-facing explanations and avoid stale
  import-structure output
* synthetic 10-chapter browser-style import bundles inspect and persist
  metadata counts and stored source bytes without leaking source sentences in
  the inspect response
* uploaded filenames are normalized to basename-only across temp import paths,
  saved import metadata, and workflow log metadata so user machine paths do not
  survive into hosted import logs

Acceptance:

```text
Users know whether Aevryn is inspecting, saving, queued, processing, succeeded, failed, or recoverable.
```

## F. Session And Account Recovery

Status:

```text
In progress
```

Remaining hardening:

* hosted browser validation for password recovery
* hosted browser validation for expired-session recovery
* ~~ensure recovery errors remain human-readable~~
* ~~ensure token/session details are never displayed~~
* ~~verify login always lands on Dashboard~~

Verified hardening:

* password-recovery completion returns users to Login with a human-readable success
  message, clears any stored session, and does not render the recovery token
* verified with focused recovery UI test, managed-identity auth tests, session tests,
  full App test suite, lint, and production build
* expired sessions from deep project routes return to Login and then land on
  Dashboard after successful login instead of reopening the stale route
* invalid authenticated API sessions show a human-readable expired-session message
  and clear stored session data without displaying token/JWT internals
* verified with focused session-recovery frontend tests

Acceptance:

```text
Users can recover from expired sessions and forgotten passwords without CLI intervention.
```

## G. Settings And User Preferences

Status:

```text
Verified for V2; hosted browser validation remains
```

Remaining hardening:

* ~~project settings remain the only editable V2 settings surface~~
* ~~workspace, account, privacy, and diagnostics sections are read-only/contextual in V2~~
* ~~broad profile personalization remains V3+ unless explicitly re-scoped~~
* ~~current Settings page must not imply nonexistent personalization or workflow controls~~
* run hosted browser validation against the current Settings page

Verified hardening:

* Settings page separates editable project defaults from read-only workspace,
  account, privacy, and diagnostics context
* Account settings identify the managed identity provider and keep broad profile
  editing on the finished website account surface
* Privacy settings state that uploaded stories remain creator-owned and AI
  training is off by default with no live training pipeline active
* diagnostics remain collapsed and token/session details are not rendered
* verified with focused Settings workspace test, lint, and production build

Acceptance:

```text
Settings are honest, useful, and not misleading for beta.
```

## H. Exports

Status:

```text
Baseline verified; final pass remains
```

Verified evidence:

* hosted snapshot export creation passed in `docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md`
* owner export metadata visibility passed in `docs/AEVRYN_RESTORE_AUDIT_DRILL_2026_07_17.md`
* owner export download availability passed in `docs/AEVRYN_RESTORE_AUDIT_DRILL_2026_07_17.md`
* cross-user export access and download were denied in `docs/AEVRYN_RESTORE_AUDIT_DRILL_2026_07_17.md`
* export limitations are documented in `docs/AEVRYN_EXPORT_ENGINE.md`
* API export creation/listing returns metadata only and does not expose
  `storage_ref` or private storage paths
* frontend stored-export cards display download availability while explicitly
  hiding private storage references
* export API and database tests keep metadata and download routes project-owner
  scoped after the storage/database hardening
* export creation normalizes submitted path-like filenames to basename-only
  metadata before writing storage-backed exports, while storage still rejects
  path-shaped filenames as a lower-level guard

Remaining hardening:

* rerun export creation and download in the final hosted browser pass
* ~~keep export metadata visible without exposing private storage references~~
* ~~keep exports project-owner scoped after any storage or database changes~~
* ~~keep export download requests authenticated and timestamped from the frontend client~~
* ~~keep export filenames from shaping storage paths or download headers~~

Acceptance:

```text
Users can create and download allowed beta exports without storage leakage.
```

## I. Browser Alpha Pass

Status:

```text
Repeat before public beta
```

Required pass:

* login
* dashboard landing
* create project
* create/select story
* import 10 chapters
* inspect import
* save import
* submit processing once
* observe progress
* verify Characters
* verify World
* verify Timeline
* verify Scenes
* verify Continuity
* verify Prompt Packs
* verify Exports
* verify Settings
* delete project
* relogin/session recovery

Acceptance:

```text
The full beta path works in browser without CLI knowledge.
```

---

# Operational Hardening Backlog

## 1. Hosted CI And GitHub Hygiene

Remaining hardening:

* keep all open PR checks green
* keep branch protection enforceable without trapping owner-only PRs forever
* keep Dependabot and CodeQL useful without noisy blockers
* verify recent commits reach GitHub
* avoid lingering unmerged branches where possible

Acceptance:

```text
Repository status is understandable, current, and mergeable.
```

## 2. Cloud Run And Cloudflare Deployment

Remaining hardening:

* confirm latest API revision is serving intended image
* confirm Cloudflare Pages environment variables are correct
* confirm app.aevryn.ai and api.aevryn.ai health
* confirm CORS stays explicit
* confirm frontend deploys from the intended branch

Acceptance:

```text
Hosted beta environment reflects the repository state being tested.
```

## 3. Database Runtime Role

Remaining hardening:

* preserve restricted runtime role
* rerun audit access verification after infrastructure changes
* keep schema bootstrap disabled in production runtime
* keep migration ownership separate from app runtime

Acceptance:

```text
Runtime app can use product tables but cannot rewrite audit history.
```

## 4. Restore/Audit Drill Maintenance

Remaining hardening:

* keep the dated restore/audit drill record
* rerun before material infrastructure changes
* keep restore logs metadata-only
* do not attach restore drill environment to production traffic

Acceptance:

```text
Recovery evidence remains current and isolated.
```

---

# Keep Out Of V2 Unless Re-Scoped

These ideas are valuable, but should not delay V2 public beta unless deliberately pulled in.

* image generation
* video generation
* production batching
* payments
* subscriptions
* credits
* teams/collaboration
* public publishing
* full profile personalization
* character portrait generation
* asset manager
* storyboard engine
* broad frontend redesign

Track future ideas in:

* `docs/AEVRYN_FUTURE_IDEAS.md`
* `docs/AEVRYN_ROADMAP.md`

---

# Recommended Execution Order

1. Finish engineering-owned UI hardening:
   * Continuity readability
   * Prompt Pack hosted validation and polish
   * Character/entity review readability
   * Settings honesty pass

2. Run full local gates:
   * backend tests
   * backend lint
   * backend typing
   * frontend lint
   * frontend tests
   * frontend build
   * release-readiness document tests

3. Push and settle GitHub:
   * all branches/PRs understandable
   * required checks green
   * no stale blocking branches

4. Run hosted browser pass:
   * 10-chapter canonical beta path
   * confirm export/download still works
   * deletion
   * session recovery

5. Complete external reviews:
   * legal
   * provider
   * backup wording
   * support/trust pages
   * observability logs

6. Update release-candidate record:
   * final results
   * final residual risks
   * public-beta decision

---

# Stop Conditions

Stop and do not approve public beta if any of the following are true:

* a feature succeeds without doing real work
* tests pass because they were weakened
* source prose appears in logs, monitoring, support artifacts, or hidden diagnostics
* full AI payloads are logged
* deleted project/story data remains visible in active product surfaces
* cross-user project access succeeds
* provider terms are not reviewed
* public legal pages are not reviewed
* hosted logs cannot be verified as metadata-only
* the browser beta path requires CLI knowledge

---

# Current Next Slice

Recommended next engineering slice:

```text
Continue UX hardening on the processed-output surfaces, then commit each completed slice before moving on.
```

The next best target is:

```text
Prompt Pack hosted validation and prompt readability polish.
```

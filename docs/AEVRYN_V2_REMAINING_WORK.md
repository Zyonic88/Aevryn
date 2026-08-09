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

# Product Standard

```text
Aevryn is a Canon IDE, not a generic dashboard with dark styling.
```

V2 public beta must feel and behave like an IDE-style creative workspace:

* navigation should be compact, stable, and fast to scan
* workers must be observable, reliable, retryable, and never appear stuck without explanation
* wasted space should be converted into useful context or removed
* panels should not be stacked inside panels as decorative structure
* every visible surface should help the creator understand Canon, workflow state, or next action
* fewer clicks are better when they do not remove necessary review or safety
* UI polish matters, but Canon accuracy matters more

The accuracy standard is:

```text
Canon truth is the product.
```

The pipeline standard is:

```text
Every downstream system should receive more structured information than the
system before it.
```

V2 now treats this as the Structured Certainty Pipeline:

```text
Story Import
-> Sentence Understanding
-> Translation / Normalization
-> Entity Extraction
-> Entity Resolution
-> Canon Updating / Canon
-> Scene, Character, World, Timeline, Continuity
-> Prompt Engine
```

The required identity boundary is:

```text
Extraction proposes.
Resolution consolidates.
Canon decides truth.
```

Tracking:

* `docs/AEVRYN_STRUCTURED_CERTAINTY_PIPELINE.md`

If Aevryn cannot reliably understand characters, world objects, skills, systems,
scene state, and story changes, the frontend polish does not matter. Remaining V2
hardening should prioritize story-neutral accuracy, evidence-backed presentation,
and workflow clarity over decorative redesign.

Prompt Packs are especially important because they are the first production-facing
output creators may reuse outside Aevryn. A V2 prompt does not need to promise
one-click perfect generation, but it must be materially better than manually
pasting chapter text into a generic AI tool.

Multiple prompts per chapter remain future production-batching scope unless
explicitly re-scoped. V2 should still preserve the architecture needed for
scene-level prompt expansion later by keeping prompts scene-bound, Canon-bound,
and grounded in current character/world state.

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
* `docs/AEVRYN_PUBLIC_LEGAL_REVIEW_PACKET.md`
* `docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md`
* `docs/AEVRYN_PUBLIC_BETA_SETUP_CHECKLIST.md`

Acceptance:

```text
Public legal pages are owner-reviewed and attorney-reviewed, or public beta remains blocked.
```

## 2. Public Trust And Support Review

Status:

```text
Public wording consistency review passed; public beta still blocked by
legal-sensitive wording, provider disclosure, backup wording, and final signoff
```

Required:

* ~~confirm public trust page wording~~
* ~~confirm privacy/user-rights wording~~
* ~~confirm support procedure~~
* ~~confirm source-prose redaction guidance~~
* ~~confirm abuse-report path~~
* ~~confirm account/project deletion support language~~
* verify contact aliases still work

Tracking:

* `docs/AEVRYN_PUBLIC_TRUST_READINESS.md`
* `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`
* `docs/AEVRYN_PUBLIC_SUPPORT_PROCEDURE.md`
* `docs/AEVRYN_PUBLIC_CONTACTS.md`
* `docs/AEVRYN_OWNER_PUBLIC_REVIEW_RECORD.md`
* `docs/AEVRYN_OWNER_PUBLIC_REVIEW_2026_07_24.md`
* `docs/AEVRYN_PUBLIC_WORDING_CONSISTENCY_REVIEW_2026_08_02.md`
* `docs/AEVRYN_PUBLIC_REVIEW_MATRIX.md`
* `docs/AEVRYN_PUBLIC_BETA_SETUP_CHECKLIST.md`

Acceptance:

```text
Users can understand their rights, get help, report abuse, and contact Aetherra Labs without exposing manuscripts unnecessarily.
```

Verified evidence:

* `docs/AEVRYN_OWNER_PUBLIC_REVIEW_2026_07_24.md` records owner-controlled
  decisions approving Aetherra Labs as operator, `aevryn.ai` as the product
  domain, support/privacy/security/abuse aliases, "Your work belongs to you,"
  user ownership posture, no-training-without-opt-in posture, metadata-first
  support, and General/Teen/Mature/Explicit content classification.
* Public beta remains blocked until legal-sensitive wording, provider
  disclosure, backup wording, and final public-beta signoff are completed or
  explicitly accepted in the release-candidate record.
* `docs/AEVRYN_PUBLIC_WORDING_CONSISTENCY_REVIEW_2026_08_02.md` records that
  public wording consistency passed without approving legal-sensitive wording
  or public beta.

## 3. AI Provider Review

Status:

```text
Aevryn technical/source posture and owner dashboard review verified;
legal-sensitive wording and final public-beta approval remain open
```

Required:

* ~~verify final model configuration~~
* verify provider data-retention behavior - official OpenAI source review
  recorded and rechecked; owner dashboard review completed
* verify provider training behavior - official OpenAI source review recorded
  and rechecked; owner confirmed API input/output and evaluation/fine-tuning
  sharing are disabled
* verify abuse-monitoring behavior - official OpenAI source review recorded; public disclosure and account controls still open
* ~~verify response-storage/request-storage posture~~
* confirm no-training-by-default public language
* rerun provider config check after final provider settings

Tracking:

* `docs/AEVRYN_AI_PROVIDER_REVIEW.md`
* `docs/AEVRYN_AI_PROVIDER_DATA_USE_READINESS.md`
* `docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md`
* `docs/AEVRYN_OPENAI_PROVIDER_REVIEW_2026_07_24.md`
* `docs/AEVRYN_OPENAI_PRODUCTION_ACCOUNT_VERIFICATION.md`

Acceptance:

```text
Users can understand when story excerpts leave Aevryn-owned systems and what the selected provider may do with them.
```

Verified evidence:

* Hosted production-like `aevryn provider-config-check` passed on 2026-07-17
  with `model=gpt-5.4-mini`, `request_storage=disabled`,
  `responses_store=false`, and `secrets_printed=0`.
* Official OpenAI source posture was rechecked on 2026-08-01 against API data
  controls, API authentication, and data-sharing controls; the current source
  boundary still supports Aevryn's disclosure candidate.
* Aevryn-side technical controls for model, Responses API scope, `store=false`,
  no background mode, and out-of-scope provider endpoints are verified for the
  current public-beta candidate.
* Owner verified the production OpenAI organization/project dashboard posture
  on 2026-08-02: production org confirmed, production project confirmed,
  project-scoped key confirmed, API input/output sharing disabled,
  evaluation/fine-tuning sharing disabled, no default training on user stories,
  and production model `gpt-5.4-mini`.
* Modified Abuse Monitoring, Zero Data Retention, and data residency controls
  were not found by owner review and must not be represented as enabled.
* Final owner product-truth provider disclosure wording approval was recorded
  on 2026-08-02 in
  `docs/AEVRYN_PROVIDER_DISCLOSURE_WORDING_APPROVAL_2026_08_02.md`.

Remaining blockers:

* attorney review of legal-sensitive provider wording
* final release-candidate provider approval or explicit provider-disable
  decision

## 4. Hosted Observability Review

Status:

```text
Passed
```

Required:

* final bounded hosted log review - complete
* confirm metadata-only logs - complete
* confirm no manuscripts, chapters, AI payloads, tokens, private URLs, hostnames, usernames, or machine-local paths - complete
* confirm monitoring remains workflow-observation only - complete
* record final hosted evidence - complete

Tracking:

* `docs/AEVRYN_PRODUCTION_OBSERVABILITY_POLICY.md`
* `docs/AEVRYN_PRODUCTION_LIKE_SMOKE_RECORD.md`
* `docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md`

Acceptance:

```text
Hosted logs and monitoring are metadata-only and safe for public-beta operations.
```

Final evidence:

```text
2026-07-24 final bounded hosted observability review passed against Google Cloud Run service-log samples.
Samples covered health, project reads, import metadata, status, exports, auth-denial metadata, worker/job metadata, and project deletion metadata.
Forbidden-data scans found zero bearer tokens, JWT-like tokens, provider keys, Cloudflare tokens, database URLs, R2 credentials, storage references, signed URLs, local machine paths, provider payload terms, or source-story terms.
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
* `docs/AEVRYN_BACKUP_RETENTION_OWNER_REVIEW_2026_08_02.md`
* `docs/AEVRYN_BACKUP_RETENTION_PRODUCTION_VERIFICATION.md`
* `docs/AEVRYN_BACKUP_RECOVERY_AUDIT_READINESS.md`
* `docs/DATA_RETENTION_POLICY.md`

Verified evidence:

* isolated restore drill passed
* deleted story absence from product surfaces passed
* restored source and export boundaries remained owner-scoped
* audit ledger integrity passed after restore
* hosted restore logs remained metadata-only
* official Supabase and Cloudflare R2 source facts were rechecked on 2026-08-02
* production backup retention verification tooling is implemented through
  `aevryn backup-retention-config-check`
* production Supabase backup retention was verified on 2026-08-02 as Pro with
  a 7-day daily backup window
* production R2 deletion behavior was verified on 2026-08-02 as direct delete,
  with lifecycle expiration not applicable

Remaining blockers:

* backup retention owner/legal approval

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

## 7. Public Apex Website Routing

Status:

```text
Open
```

Required:

* deploy the repo-owned static public website from `website/`
* route `https://aevryn.ai` to that deployed static site
* keep `https://app.aevryn.ai` as the authenticated application domain
* verify the Cloudflare Pages project uses root `website`, no build command,
  static root output, production branch `master`, and the expected custom domain
* confirm the public apex site does not collect manuscripts, imply public beta
  approval before signoff, or contradict legal/trust wording

Tracking:

* `website/README.md`
* `docs/AEVRYN_PUBLIC_SITE_PUBLICATION_PLAN.md`
* `docs/AEVRYN_PUBLIC_BETA_SETUP_CHECKLIST.md`

Verified evidence:

* 2026-08-08 browser review found `https://aevryn.ai` serving a generic
  placeholder/contact page rather than the repo-owned static website.
* `aevryn public-website-config-check` now exists to verify the static website
  Pages project contract with metadata-only output.

Acceptance:

```text
https://aevryn.ai serves the approved static Aevryn website from website/, and
aevryn public-website-config-check returns ok=public_website_config_contract_checked.
```

---

# Engineering Hardening Backlog

These are practical code/docs hardening items still worth doing before public beta.

## A. Prompt Packs

Status:

```text
Verified for V2
```

Remaining hardening:

* ~~verify Prompt Packs consume Character, World, Scene, Timeline, and Continuity
  presentation state when building prompt context, not just scene summary text~~
* ~~keep prompts Canon-bound enough to preserve known character appearance,
  setting, scene action, world objects, systems, skills, and current story state~~
* ~~improve Prompt Packs layout so chapter/scene prompts are easy to follow without
  endless scrolling~~
* ~~preserve scene-level prompt architecture so future multi-prompt-per-chapter and
  production batching can be added without rewriting Canon or extraction~~
* ~~run hosted browser validation against the current prompt-pack output~~
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
* hosted browser sweep verified current Prompt Packs output exposes collapsed,
  copyable prompt bodies without source text, source IDs, evidence anchors,
  import bundle IDs, machine chapter/scene fragments, or placeholder noise
* prompt bodies now include a compact `Canon inputs` checklist that exposes
  which prompt inputs were available from character sheets, world facts,
  relationships, scene beats, visual anchors, and continuity notes without
  printing source prose or internal IDs
* verified with focused Canon Prompt Builder tests, presentation-engine tests,
  and background-worker prompt-presentation tests
* system and skill mechanics now remain prompt-visible as non-visual Canon
  constraints instead of being treated as image props, scenery, or required
  visual references unless Canon explicitly marks them visible
* verified with focused Canon Prompt Builder tests
* large prompt-pack outputs remain bounded at first render but expose a
  user-controlled "show more scenes" path, so later prompt scenes from large
  imports are reachable without dumping every prompt card onto the page
* verified with focused Prompt Packs workspace test, full frontend test suite,
  lint, and production build
* Prompt Packs now include scene search by chapter, scene, character, setting,
  visual detail, and environment so large projects can reach specific prompt
  scenes without manual scrolling
* verified with focused Prompt Packs workspace test, full frontend test suite,
  lint, and production build
* prompt-pack detail cards now show available/missing Canon input status for
  characters, setting, visuals, continuity, and constraints with compact preview
  details so users can judge prompt grounding without opening every prompt body
* verified with focused Prompt Packs workspace test, full frontend test suite,
  lint, and production build
* prompt-builder and presentation tests verify prompt text and prompt metadata
  consume character cards, accepted character facts, world facts, relationships,
  scene visual anchors, scene action beats, continuity notes, and missing-input
  status instead of relying only on scene summary text
* verified with focused Canon Prompt Builder, Prompt Engine, and Presentation
  Engine tests
* Prompt Packs selected-scene detail now includes previous/next scene navigation
  and a filtered scene-position counter, reducing list-hopping while reviewing
  production prompts scene by scene
* verified with focused Prompt Packs workspace test, full frontend test suite,
  lint, and production build
* project output prompt packs now append visible `User Edited Canon corrections`
  context to image, narration, camera, and animation prompts when user-authored
  Character or World corrections exist, without mutating extracted Canon or
  exposing internal target IDs
* verified with project output API regression coverage and the full Python test
  suite
* Prompt Packs selected-scene detail now shows a compact production-focus strip
  for scene priority, generation guardrails, and missing-input neutrality before
  the prompt bodies, making prompt readiness scannable without opening every
  collapsed prompt
* prompt scene search now includes continuity-change text, so creators can find
  prompt scenes by accepted scene state as well as chapter, scene, character,
  setting, visual detail, and environment
* verified with focused Prompt Packs workspace test, full frontend test suite,
  lint, and production build
* image prompts now include a compact `Image generation handoff` that summarizes
  the current render moment, confirmed subjects, visible objects/details,
  preservation rules, and neutral handling for unspecified traits before the
  longer Canon context sections
* narration, camera, and animation prompts now include matching compact
  generation handoffs that declare the immediate task, confirmed subjects,
  relevant details, and prompt-type guardrails before the longer Canon context
  sections
* current-scene visual anchors remain ahead of retained/background object facts
  in all prompt generation handoffs, preserving the current-scene-first rule for
  generation tools
* verified with focused Canon Prompt Builder regression tests
* Prompt Packs selected-scene detail now surfaces compact image, narration,
  camera, and animation handoff summaries before the longer collapsed prompt
  bodies, so creators can scan each generation target without opening every
  prompt
* verified with focused Prompt Packs workspace regression coverage
* compact prompt handoffs now include an `Appearance lock` / `Description
  boundary` line sourced from accepted character-card appearance facts, or an
  explicit neutral-unknown instruction when no appearance facts are confirmed
* verified with focused Canon Prompt Builder regression tests
* Prompt Packs UI handoff summaries now display the compact task and
  appearance/boundary line together, so collapsed prompt cards still expose the
  Canon-backed visual identity constraint before users open full prompt text
* verified with focused Prompt Packs workspace regression coverage
* Prompt Packs UI handoff summaries now also expose generator-specific detail
  lines such as visible objects/details, camera-visible details, narration
  details, and motion-relevant details when the backend prompt provides them,
  making Canon grounding easier to verify before expanding full prompt bodies
* verified with focused Prompt Packs workspace regression coverage, lint, and
  production build
* V2 Prompt Packs remain scene-bound and Canon-bound while explicitly preserving
  future multi-prompt-per-chapter and production-batching architecture as later
  scope, not hidden V2 behavior
* Prompt Packs are accepted for V2 beta readiness with the residual product risk
  that AI image/video generators may still need iteration; Aevryn's V2 duty is
  Canon-grounded production context, not one-click perfect generation

Acceptance:

```text
Prompt Packs are Canon-bound, scene-aware, and useful for beta without promising
one-click perfect image/video generation.
```

## B. Continuity Readability

Status:

```text
Verified for V2
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
* ~~keep large buckets collapsed during hosted browser validation~~
* continue reducing repeated or low-value retained-canon noise when new examples appear
* ~~verify no raw IDs appear in normal user view~~
* ~~verify continuity remains Canon-backed and does not invent explanations~~

Verified hardening:

* normal continuity output shows scene-level summaries with the first visible
  new/changed Canon highlight before expansion
* continuity preview keeps full change buckets collapsed and retained-canon
  detail nested, while retained-canon Markdown examples remain bounded
* processed-output and preview continuity buckets cap retained-record detail
  lists and show hidden-record counts, so large projects stay readable without
  pretending overflow does not exist
* continuity buckets filter internal-only records before choosing visible rows,
  so hidden source IDs do not consume the visible detail budget or render as
  `Unknown` noise
* hosted Continuity validation confirmed production `app.aevryn.ai` renders
  "retained canon" wording, keeps all 38 continuity disclosures collapsed by
  default, exposes compact scene-level change summaries, and does not expose
  source IDs, evidence anchors, fact IDs, import bundle IDs, storage references,
  token/JWT fragments, or placeholder values in normal output
* production deployment alignment was verified after PR #120 merged to `master`;
  `app.aevryn.ai` moved from the older Continuity bundle to the current
  production bundle before final Continuity validation

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
* expanded character cards span the workspace row and use readable inspector
  sections instead of cramped narrow text columns

Remaining hardening:

* continue hosted duplicate-card review for title/name/alias/description cases
  observed in alpha runs
* ensure entity-resolution improvements remain story-neutral and never hardcoded
  to a specific character name, title, or source novel
* continue reducing duplicate character cards caused by aliases/titles/descriptions
* keep ambiguous identity references visible for review instead of force-merging
* ensure race/gender remain Canon-truthful and not story-specific guesses
* run hosted browser validation that user-authored corrections show in Character
  and World output panels with a visible `User Edited` label
* ~~run isolated local browser validation that Character corrections save,
  refresh, stay collapsed until opened, and show a visible `User Edited` label~~
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
* local browser validation confirmed collapsed correction editors do not leak
  hidden form controls, saved Character corrections refresh output, and singular
  profile counts render correctly
* extraction rejects plural race/gender group phrases as character cards while
  preserving singular unnamed character candidates when evidence supports them
* entity resolution keeps pronouns, shared honorifics, near-tied matches, and
  low-confidence descriptions ambiguous instead of force-merging identities
* entity resolution and project-runner tests resolve title-plus-name references
  such as General Charlotte to the existing Canon identity when the title/name
  support is explicit, while keeping shared titles ambiguous
* entity resolution and project-runner tests resolve conservative rank/title
  prefixes such as Captain Mira to a known Canon identity even before the title
  has been stored as a prior fact, while rejecting ordinary descriptors such as
  Wounded Mira
* entity-resolution tests now cover punctuation, articles, hyphenation, and
  possessive suffixes around supported title/name references so variants such
  as "Captain Mira's" and "Captain-Mira" do not fragment identities
* entity-resolution and project-runner tests now resolve conservative title
  suffix variants such as "Mira, Captain" and "Mira the Captain" to the known
  identity while leaving generic suffix descriptors unresolved
* project-runner tests now verify same-scene title/name duplicate candidates
  rewrite to the named Canon identity instead of producing an extra character
  card
* project-runner tests now verify same-scene exact visible-surface duplicates
  collapse to the highest-confidence entity, preserving attached facts/state
  changes under one Canon identity instead of creating duplicate cards
* project-runner identity rewrites now flatten chained duplicate resolutions
  before Canon update, so a descriptive duplicate that resolves to a title/name
  duplicate still lands on the final Canon identity instead of leaving facts or
  state changes attached to a removed intermediate character
* project-runner identity profiles preserve explicit relationship labels such as
  "sister of Zhao Chen," allowing possessive references like "Zhao Chen's sister"
  to resolve to an existing identity without creating duplicate character cards
* project-runner gender-support terms recognize accented fiancee/fiance
  spellings the same way as unaccented spellings, so translated or polished
  prose does not lose conservative pronoun support
* project-runner gender-support terms ignore explicitly negated gender phrases
  with short descriptive bridges such as "not a young woman," "not an adult man,"
  and "without any male heir," so pronoun resolution does not infer gender from
  denied identity language
* character-sheet presentation recognizes accented fiancee/fiance spellings in
  evidence-linked gender support, so accepted direct gender facts do not display
  as Unknown only because prose used diacritics
* character profiles and stored snapshot API output hide contradictory
  Human-plus-non-human race/species values instead of displaying both as Canon
* character profiles reject explicitly negated race/species support such as
  "not a Half-Beastman" and "without any human ancestry," while preserving the
  surrounding context as readable relationship/origin information
* prompt packs omit negated visual identity facts from character detail lines
  and visual identity coverage, preventing denied race/species/gender evidence
  from becoming positive image or narration guidance
* prompt packs add a bounded character-continuity lock when aliases, titles,
  descriptions, or relationship labels are present, telling generation tools to
  keep those surfaces attached to the same Canon identity instead of creating
  extra people
* entity resolution now supports conservative composite visual-description
  matching from accepted visible traits, such as gender plus hair color, so
  later references like "white-haired woman" can resolve to a unique prior
  identity without making gender-only merges
* entity resolution now resolves embedded known-name references only when the
  surrounding title/description words are explicitly backed by that identity,
  preventing duplicate cards such as "Female General Charlotte" while rejecting
  unsupported descriptors around a known name
* entity-resolution validation now covers alias-plus-supported-context surfaces
  such as "Captain Mark the engineer" so known aliases with backed roles do not
  create duplicate cards, while unsupported extra descriptors still remain
  unresolved
* title/name matching was tightened so extra unsupported words no longer resolve
  just because a known title and name both appear in the same surface reference
* backend persistence and API now define project-scoped user correction records
  with a fixed `User Edited` source label, ownership checks, metadata-only audit
  events, JSON/PostgreSQL schema support, and project-delete cleanup
* project outputs now apply user-authored corrections to Character sections and
  append World correction sections with a visible `User Edited` label instead
  of pretending edited values are extracted evidence
* frontend Character and World cards now expose compact user correction editors
  for approved fields; saves round-trip through the correction API and refresh
  processed outputs instead of rendering optimistic fake Canon
* frontend character-detail sections automatically widen for appearance,
  descriptions, relationships, timeline, evidence, recent changes, and other
  long accepted facts, preserving detail without turning prose into vertical
  text
* verified with the focused processed-character-panel frontend test
* verified with the focused entity-resolution test suite and Ruff

Acceptance:

```text
Characters are readable, Canon-truthful, and honest even when identity
resolution is uncertain.
```

## D. World Classification

Status:

```text
In progress
```

Remaining hardening:

* continue sentence-understanding hardening for item/skill/system boundaries
  without over-tightening valid genre-specific world facts
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
* production sentence-understanding cues were scanned for alpha-story proper
  nouns and genericized, so world-routing metadata relies on reusable concepts
  such as academy, department, empire, fleet, star system, and training room
  instead of names from the "Sorry, my starfleet only recruits female soldiers"
  test corpus
* production AI extraction prompt wording was hardened to describe gender/race
  rules generically instead of priming the model with alpha-story phrases such
  as "Half-Beastman," "female soldiers," or "male recruits"
  instead of becoming Canon truth
* sentence understanding flags genre power-system/body terms such as dantian,
  meridian, qi, and spiritual root as translation-review metadata without
  turning them into skills, items, or Canon facts
* system reward, mission, quest, and points language is treated as system context
  rather than a usable skill unless the evidence explicitly describes an ability
* system UI plus skill/ability cues are marked reviewable instead of being treated
  as settled meaning
* system UI phrases such as system window, status screen, and quest notification
  route as system metadata; plain literal windows remain ordinary world context
  unless a system UI phrase is present
* extraction validation rejects system UI phrases when proposed as physical items
  while accepting them as system entities when evidence supports that type
* system-created physical objects such as technical blueprints remain item
  candidates when evidence supports a concrete object classification
* physical skill-source phrases such as skill book, spell book, skill manual, and
  technique manual route as item context instead of automatically becoming usable
  skills, while separate skill cues in the same sentence remain reviewable
* physical skill-card and ability-token phrases route as item context instead of
  automatically becoming usable skills; separate skill evidence in the same
  sentence remains visible and reviewable
* deterministic extraction guards reject provider candidates that classify
  physical skill containers such as skill cards as usable skills while accepting
  the same containers as physical items when evidence supports them
* system-resource phrases such as skill points and experience points route as
  system context rather than usable skills, while separate ability cues in the
  same sentence remain visible and reviewable
* physical skill-source scrolls route as item context rather than automatically
  becoming usable skills
* physical knowledge/resource containers such as jade slips, cultivation manuals,
  ability crystals, skill crystals, and source crystals route as item context,
  while obvious AI attempts to classify crystals or slips as usable skills are
  rejected by deterministic extraction guards
* physical spell/knowledge containers such as spell tomes, spell grimoires,
  magic tomes, and technique books route as item context, while separate spell
  or ability cues in the same sentence remain visible and reviewable
* deterministic extraction guards reject provider candidates that classify
  physical spell/knowledge containers such as grimoires as usable skills
* visual and technical documents such as star maps, charts, schematics, and
  spell or formation diagrams route as item context instead of becoming
  locations or usable skills; separate spell/ability evidence in the same
  sentence remains visible and reviewable
* deterministic extraction guards reject provider candidates that classify
  physical diagrams as usable skills
* physical-core phrases such as energy core, beast core, and reactor core route
  as item context and are rejected when a provider tries to classify them as
  usable skills or governing systems, while bare/genre core terms remain
  translation-review metadata until evidence resolves meaning
* the evidence-bounded AI extraction prompt tells the provider that manuals,
  scrolls, jade slips, crystals, maps, charts, diagrams, and schematics are
  physical item containers unless evidence explicitly states a usable ability
* deterministic extraction guards reject obvious place or institution heads such
  as academy, department, empire, room, and station when a provider tries to
  classify them as physical items or usable skills
* deterministic extraction guards reject obvious physical-object heads such as
  blueprint, sword, uniform, crystal, and manual when a provider tries to
  classify them as places or organizations
* deterministic extraction guards reject obvious role/title concepts such as
  captain commander and chief engineer when a provider tries to classify them
  as places or organizations, while preserving actual place/organization heads
* regression tests verify role-bearing real place/organization names such as
  Captain Department and Officer Training Room remain accepted, preventing
  over-hardening from erasing valid world structure
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
* dashboard project deletion removes the deleted project from the visible project
  list immediately after the confirmed API delete succeeds, even if a follow-up
  project-list refetch briefly returns stale data
* saved import processing state remains scoped to the submitted import row, so
  one stuck/submitting import does not make every saved import look active
* missing or stale queue jobs are marked failed with retryable, human-readable
  summaries instead of leaving durable runs pending forever
* active processing displays API-backed states such as Queued, Processing,
  Snapshot, and Output ready without fake percentages
* project run history now renders as a compact activity log with duration,
  snapshot state, current state, and concise failure summaries, while the
  detailed processing stepper stays reserved for the active run
* source intake now labels the fast path as "Process chapters" and explains
  that it inspects, saves, and submits processing, while keeping "Inspect only"
  available for manual review without removing review/safety controls
* source intake now keeps filename, title, import reference, and source
  reference controls inside collapsible import details so the main path stays
  focused on choosing source material and starting Canon processing
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

* hosted browser validation for password recovery email delivery and callback
* hosted browser validation for expired-session recovery
* ~~ensure recovery errors remain human-readable~~
* ~~ensure token/session details are never displayed~~
* ~~verify login always lands on Dashboard~~

Verified hardening:

* password recovery request form accepts valid Aevryn-hosted email addresses and
  shows an account-enumeration-safe confirmation even if the managed identity
  provider rejects the reset request
* managed identity provider password-recovery rejection text is not rendered to
  users on the request form
* password-recovery completion returns users to Login with a human-readable success
  message, clears any stored session, and does not render the recovery token
* verified with focused recovery UI tests, managed-identity auth tests, session tests,
  lint, and production build
* expired sessions from deep project routes return to Login and then land on
  Dashboard after successful login instead of reopening the stale route
* invalid authenticated API sessions show a human-readable expired-session message
  and clear stored session data without displaying token/JWT internals
* verified with focused session-recovery frontend tests
* browser sessions now clear local session state after 30 minutes of inactivity,
  show a human-readable login message, and do not render raw session tokens
* verified with focused AuthProvider inactivity tests, backend authentication
  tests, frontend lint, and production build

Acceptance:

```text
Users can recover from expired sessions and forgotten passwords without CLI intervention.
```

## G. Settings And User Preferences

Status:

```text
Verified for V2
```

Remaining hardening:

* ~~project settings remain the only editable V2 settings surface~~
* ~~workspace, account, privacy, and diagnostics sections are read-only/contextual in V2~~
* ~~broad profile personalization remains V3+ unless explicitly re-scoped~~
* ~~current Settings page must not imply nonexistent personalization or workflow controls~~
* ~~run hosted browser validation against the current Settings page~~

Verified hardening:

* Settings page separates editable project defaults from read-only workspace,
  account, privacy, and diagnostics context
* Account settings identify the managed identity provider and keep broad profile
  editing on the finished website account surface
* Privacy settings state that uploaded stories remain creator-owned and AI
  training is off by default with no live training pipeline active
* diagnostics remain collapsed and token/session details are not rendered
* verified with focused Settings workspace test, lint, and production build
* hosted Settings page validation confirmed Dashboard login destination,
  managed identity wording, support-owned account deletion language,
  collapsed diagnostics, and no visible or hidden token/session/storage/internal
  strings in normal page output

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
* export creation sanitizes quote, delimiter, control, and filesystem-reserved
  filename characters before metadata is stored, preventing submitted filenames
  from shaping storage paths or download headers
* stored export creation appears in the Exports workspace immediately from the
  API response while the export list refreshes in the background, so beta users
  are not left wondering whether the export actually completed
* hosted Exports pass created a Canon Snapshot / JSON export from the latest
  accepted snapshot, showed it immediately with human filename/kind/size/date,
  kept private storage references hidden, and the download action now confirms
  the prepared file without exposing bytes or storage paths

Remaining hardening:

* ~~rerun export creation and download in the final hosted browser pass~~
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

## J. Canon IDE Workspace UX

Status:

```text
In progress
```

Remaining hardening:

* keep workspace navigation compact and IDE-like instead of repeating equivalent
  sidebar labels
* reduce wasted workspace chrome while preserving orientation and readability
* keep quick actions and command surfaces scannable at realistic desktop widths
* continue hosted browser validation for visual noise, overlap, and cramped text

Verified hardening:

* overview quick-action tiles now preserve whole-word labels and no-wrap command
  badges, wrapping cards before labels collapse into vertical text
* import run history no longer repeats full processing steppers on every stored
  run, reducing wasted vertical space while preserving the monitoring signal
* workspace command strip now behaves like a compact IDE command bar: project
  context, active section, and diagnostics access without repeating the old
  label-heavy sidebar layout
* import intake now presents the one-pass processing path as the recommended
  action while preserving the explicit review-only path for scene-map inspection
  before processing
* import intake polish verified with focused import workspace tests, frontend
  lint, and production build
* selected Prompt Pack scenes can now copy the full scene prompt bundle in one
  action while preserving individual Image/Narration/Camera/Animation prompt
  controls
* prompt-pack bundle copy verified with focused prompt scene picker tests
* character cards now surface accepted Appearance in the at-a-glance strip so
  visual continuity data is visible without opening the full details panel
* appearance-at-a-glance presentation verified with focused processed character
  panel tests
* User Edited character Appearance corrections now apply back onto character
  profiles and appear in Prompt Pack correction context alongside other
  user-authored Canon corrections
* appearance correction propagation verified with focused authenticated project
  output API tests and Ruff
* Character Cards now surface possible duplicate-card review items when accepted
  Canon output contains title/name or alias overlap, while refusing to merge
  uncertain identities automatically
* duplicate-card validation verified with focused character workspace tests,
  frontend lint, and production build
* verified with the full frontend test suite, lint, and production build

Acceptance:

```text
Aevryn feels like a focused Canon IDE, not a generic dashboard with panels.
```

---

# Operational Hardening Backlog

## 1. Hosted CI And GitHub Hygiene

Remaining hardening:

* ~~keep all open PR checks green~~
* keep branch protection enforceable without trapping owner-only PRs forever
* keep Dependabot and CodeQL useful without noisy blockers
* ~~verify recent commits reach GitHub~~
* avoid lingering unmerged branches where possible

Verified hardening:

* PR #120 was merged to `master` after all PR checks passed, local `master`
  fast-forwarded to `origin/master`, and post-merge master CI, security, CodeQL,
  and Cloudflare Pages deployment completed successfully

Acceptance:

```text
Repository status is understandable, current, and mergeable.
```

## 2. Cloud Run And Cloudflare Deployment

Remaining hardening:

* ~~confirm app.aevryn.ai and api.aevryn.ai health~~
* ~~confirm CORS stays explicit~~
* ~~confirm frontend deploys from the intended branch~~
* update production CORS deliberately before public beta if browser clients
  must access the API from additional public origins such as `https://aevryn.ai`
  or `https://www.aevryn.ai`

Verified hardening:

* `hosted-deployment-smoke` now verifies the public frontend is reachable, the
  public API health endpoint returns `ok`, CORS allows the configured frontend
  origin explicitly instead of using a wildcard, `X-Request-ID` is present, and
  the command prints metadata only
* `cloud-run-deployment-check` verifies that the latest ready Cloud Run API
  revision is serving 100 percent of traffic and that the serving container
  image matches the expected release-candidate image without printing project
  IDs, image URLs, secrets, storage references, source prose, or provider
  payloads
* `cloudflare-pages-config-check` verified the hosted Cloudflare Pages
  production config gate for branch, build settings, browser-safe API/Supabase
  variables, and Supabase anon key secret typing with metadata-only output
* hosted deployment smoke coverage rejects non-HTTPS/non-origin frontend values
  and wildcard API CORS responses before public-beta signoff
* production startup rejects wildcard, non-HTTPS, and non-origin-shaped CORS
  values such as origins with trailing slashes, paths, query strings,
  fragments, or credentials, so deployment mistakes fail closed before browser
  testing.
* production startup rejects non-origin-shaped public frontend/API base URLs
  such as URLs with paths, query strings, fragments, or credentials, while
  leaving provider-specific HTTPS URLs such as JWKS endpoints free to use
  required paths.
* `app.aevryn.ai` production deployment updated after PR #120 merged to
  `master`, and hosted Continuity validation confirmed the production domain was
  serving the current frontend bundle rather than the older pre-merge bundle

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

1. Finish Canon IDE hardening:
   * compact IDE navigation and workspace density
   * remove or reuse wasted space
   * avoid panels stacked inside panels unless the nested panel is a real tool
   * keep worker state visible and API-backed
   * reduce clicks in import and processing workflows where review/safety is preserved

2. Finish accuracy hardening:
   * duplicate character-card reduction for aliases, titles, and descriptions
   * conservative race/gender handling backed by explicit Canon evidence
   * item/skill/system/world classification backed by sentence understanding
   * Prompt Packs grounded in Character, World, Scene, Timeline, and Continuity state

3. Finish output UX hardening:
   * Prompt Pack chapter/scene layout
   * Continuity readability
   * Character/entity review readability
   * Settings honesty pass
   * Exports clarity

4. Run full local gates:
   * backend tests
   * backend lint
   * backend typing
   * frontend lint
   * frontend tests
   * frontend build
   * release-readiness document tests

5. Push and settle GitHub:
   * all branches/PRs understandable
   * required checks green
   * no stale blocking branches

6. Run hosted browser pass:
   * 10-chapter canonical beta path
   * confirm export/download still works
   * deletion
   * session recovery

7. Complete external reviews:
   * legal
   * provider
   * backup wording
   * support/trust pages
   * observability logs

8. Update release-candidate record:
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
* duplicate character-card behavior remains common enough to undermine Canon trust
* Prompt Packs do not materially use accepted Canon state
* worker state can appear stuck without API-backed explanation or recovery path
* provider terms are not reviewed
* public legal pages are not reviewed
* the browser beta path requires CLI knowledge

---

# Current Next Slice

Recommended next engineering slice:

```text
Continue Canon IDE hardening one slice at a time, then commit each completed
slice before moving on.
```

The next best target is:

```text
Prompt Pack Canon-context verification and layout hardening, followed by
Character/entity duplicate-card hardening and a browser pass against the
10-chapter canonical beta path.
```

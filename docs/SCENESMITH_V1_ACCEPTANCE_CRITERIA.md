# SceneSmith V1 Acceptance Criteria

> Built by **Aetherra Labs**

This document defines what **V1 Complete** means for SceneSmith.

No subsystem is V1 complete until every required checklist item is satisfied.

If one required box is unchecked, the subsystem is not complete.

---

# Universal V1 Checklist

Every V1 subsystem must satisfy:

* Purpose is clearly defined
* Authority is clearly defined
* Boundaries are enforced
* Unit tests pass
* Integration tests pass when the subsystem participates in a workflow
* No TODO placeholders
* Proper documentation
* Stable interfaces
* Deterministic behavior
* Failure modes handled
* Logging for meaningful operational events or failures
* Type safety
* Non-string required text fails with clear validation errors
* No unnecessary complexity

---

# Story Import

V1 complete means Story Import:

* Imports plain text
* Preserves source order
* Rejects out-of-order explicit multi-chapter imports
* Rejects boolean source indexes
* Parses chapters
* Parses scenes
* Creates stable chapter IDs
* Creates stable scene IDs
* Creates paragraph IDs
* Creates sentence IDs
* Creates evidence anchors
* Requires sentence text to be traceable to paragraph text
* Requires paragraph indexes to be unique inside each scene
* Derives readable paragraphs from oversized unspaced source blocks
* Does not split sentences inside decimals, titles, or numbered names
* Validates evidence anchors against known chapters, scenes, paragraphs, and sentences
* Requires evidence anchor scenes to belong to referenced chapters
* Requires evidence anchor indexes to match referenced paragraphs and sentences
* Requires evidence anchor quotes to match source sentence text
* Preserves source quotes
* Handles common text encoding artifacts
* Rejects empty or invalid input
* Does not extract entities
* Does not change Canon

---

# Web Import

V1 complete means Web Import:

* Is documented as a boundary system
* Does not bypass site terms
* Does not bypass robots.txt
* Does not bypass paywalls or login walls
* Does not present scraped copyrighted text as SceneSmith-owned content
* Keeps manual upload and paste as the primary V1 path

For V1, Web Import may remain documented only.

It is not required for the core continuity proof.

---

# Translation Engine

V1 complete means Translation Engine:

* Is documented as an optional normalization boundary
* Preserves meaning
* Preserves names
* Preserves titles and honorifics
* Preserves power systems
* Preserves item names
* Preserves faction names
* Preserves source evidence links
* Never changes story facts
* Does not own Canon truth

For V1, Translation Engine may remain foundation-only.

It is not required for the core continuity proof.

---

# Entity Extraction

V1 complete means Entity Extraction:

* Accepts one scene at a time
* Receives paragraph and sentence evidence anchors
* Proposes candidate entities
* Proposes candidate facts
* Proposes candidate relationships
* Proposes candidate state changes
* Requires evidence anchors for every candidate
* Requires scene input anchor IDs and evidence anchor objects to match
* Requires confidence for every candidate
* Rejects boolean or out-of-range confidence
* Rejects duplicate scene evidence anchors
* Rejects duplicate candidate identities at the model boundary
* Rejects unsupported claims
* Normalizes human-readable candidate text
* Preserves source scene text and evidence quotes
* Preserves Unknown when evidence is missing
* Does not update Canon directly
* Does not remember story state

---

# Canon Updating

V1 complete means Canon Updating:

* Accepts extraction candidates only through validation
* Requires known evidence anchors
* Rejects duplicate evidence anchors
* Requires minimum confidence
* Requires known or newly accepted entities
* Rejects replacement facts that do not have later paragraph/sentence evidence
* Stores accepted entities
* Stores accepted facts
* Stores accepted relationships
* Stores state changes
* Reports only stored state changes as accepted
* Keeps accepted and rejected summary IDs mutually exclusive
* Rejects unsupported candidates
* Records rejected candidates
* Never lets AI own truth
* Never updates Canon without evidence

---

# Canon Engine

V1 complete means Canon Engine:

* Stores entities
* Stores characters
* Stores facts
* Stores relationships
* Stores evidence
* Validates evidence against registered chapter and scene structure when available
* Stores timeline events
* Requires timeline events to match evidence chapter and scene
* Requires facts to reference known entities
* Requires relationships to reference known source and target entities
* Stores state changes
* Supports permanent IDs
* Supports generic non-character entities
* Supports version history
* Orders same-scene state changes by paragraph and sentence evidence
* Supports current state lookup
* Supports state lookup at chapter X
* Supports state lookup at scene X
* Rejects boolean lookup indexes
* Supports relationship lookup
* Supports relationship lookup at scene X
* Detects duplicate relationships
* Rejects zero-length same-position state windows
* Preserves history instead of overwriting it
* Keeps Unknown as Unknown when evidence is missing

---

# Timeline Engine

V1 complete means Timeline Engine:

* Stores chapters
* Stores scenes
* Stores events
* Stores state changes
* Tracks current story position
* Supports valid_from
* Supports valid_until
* Supports history reconstruction
* Supports current state lookup
* Validates ordering
* Requires state-change events to match valid_from position
* Rejects boolean story positions
* Rejects duplicate chapters
* Rejects duplicate scenes
* Rejects duplicate events
* Rejects invalid timeline positions

---

# Character Engine

V1 complete means Character Engine:

* Builds living character cards
* Reads from Canon
* Is timeline-aware
* Supports scene-position cards
* Rejects boolean card lookup positions
* Shows current state
* Shows previous values
* Shows valid-from references
* Shows evidence
* Tracks relationships when available
* Handles unknown characters
* Normalizes visible character card text
* Does not mutate Canon
* Does not generate story facts

---

# World Engine

V1 complete means World Engine:

* Builds world state from Canon
* Supports locations
* Supports buildings
* Supports organizations
* Supports items
* Supports vehicles and creatures as generic entities
* Shows current world facts
* Shows connected relationships
* Shows evidence
* Is timeline-aware through chapter lookup
* Supports scene-position world state
* Rejects boolean world lookup positions
* Filters later same-chapter world facts and relationships
* Handles unknown world entities
* Normalizes visible world-state text
* Does not mutate Canon
* Does not generate world facts

---

# Scene Engine

V1 complete means Scene Engine:

* Builds scene context from Canon and Timeline state
* Includes characters present
* Includes active facts
* Includes relationships
* Filters later same-chapter facts and relationships
* Builds embedded character cards at the requested scene position
* Includes current equipment
* Includes relevant world state when available
* Produces scene snapshots
* Rejects duplicate scene snapshot reference IDs
* Handles unknown scenes
* Handles unknown characters
* Does not mutate Canon
* Does not analyze story meaning
* Does not generate prompts

---

# Scene Analyzer

V1 complete means Scene Analyzer:

* Reads scene context
* Produces scene summary
* Produces purpose
* Produces conflict
* Produces mood
* Produces visual highlights
* Produces character goals
* Produces character emotions
* Produces important objects
* Produces environment summary
* Produces changes introduced
* Produces continuity notes
* Normalizes analysis row whitespace
* Rejects blank or duplicate analysis rows
* Does not mutate Canon
* Does not generate final prompts

---

# Prompt Engine

V1 complete means Prompt Engine:

* Reads Scene Engine output
* Reads Scene Analyzer output
* Builds image prompts
* Builds narration prompts
* Builds camera prompts
* Builds animation prompts
* Builds production packs
* Uses accepted Canon only
* Includes continuity notes
* Includes forbidden elements
* Avoids raw chapter dumps
* Normalizes production-pack list row whitespace
* Rejects blank or duplicate production-pack rows
* Does not invent missing canon

---

# Presentation Engine

V1 complete means Presentation Engine:

* Converts machine truth into human-readable views
* Builds character profiles
* Builds scene sheets
* Builds world sheets
* Builds prompt pack views
* Builds continuity report views when available
* Keeps evidence visible or reachable
* Optimizes for fast human scanning
* Removes prompt placeholders that are useful internally but noisy for users
* Normalizes visible section whitespace
* Rejects blank or duplicate visible rows
* Does not mutate Canon
* Does not write files
* Does not simplify machine truth

---

# Export Engine

V1 complete means Export Engine:

* Exports JSON
* Exports Markdown
* Exports CSV where applicable
* Exports character sheets
* Exports scene sheets
* Exports world sheets
* Exports machine-readable world state
* Exports prompt sheets
* Exports production packs
* Preserves evidence references
* Keeps Markdown presentation-first
* Keeps JSON and CSV machine-readable
* Normalizes Markdown list whitespace
* Rejects blank Markdown list rows
* Does not mutate Canon
* Does not create presentation view models

---

# Project Manager

V1 complete means Project Manager:

* Coordinates Story Import
* Coordinates Entity Extraction
* Coordinates Canon Updating
* Coordinates Character Engine
* Coordinates World Engine
* Coordinates Scene Engine
* Coordinates Prompt Engine
* Coordinates Export-ready outputs
* Builds scene-position character cards
* Builds scene-position world state
* Rejects unknown scene-position view requests
* Does not own subsystem logic
* Does not own Canon truth
* Provides stable proof workflow methods

---

# CLI Proof Workflow

V1 complete means the CLI can:

* Import a chapter
* Show imported chapter and scene IDs
* Show bounded evidence-anchor previews without dumping source text
* Build an extraction prompt
* Apply evidence-bounded AI JSON
* Apply multi-scene evidence-bounded AI JSON envelopes
* Reject non-string or malformed multi-scene AI envelope scene IDs
* Show a character sheet
* Show a scene sheet
* Show a world sheet
* Show machine-readable world state JSON
* Default scene and prompt character context to accepted characters in the selected scene
* Use scene IDs for scene-position character and world sheets
* Show a prompt sheet
* Show a continuity report
* Explain Markdown versus JSON/CSV output intent in command help
* Show command defaults in subcommand help
* Run deterministically
* Fail clearly on invalid input
* Provide actionable hints for common unknown scene, character, and world entity selections
* Return a nonzero exit code for expected workflow errors
* Print expected workflow errors to stderr
* Avoid duplicating repeated selected IDs

The CLI proves the engine before a website exists.

---

# The Canon Test

After every subsystem reaches V1 complete, SceneSmith must pass the Canon Test.

Run:

```text
Chapter 1
-> Chapter 2
-> Chapter 3
-> Chapter 4
```

The goal is not to test extraction.

The goal is to test continuity.

SceneSmith must answer:

* What is new?
* What changed?
* What stayed known?
* What became invalid?
* What evidence supports each change?
* What chapter and scene introduced the change?

Example:

```text
Chapter 2

NEW
Eye of Insight
Fleet Luck Bonus
Baron
Jiang Shasha
Academy Cafeteria

UPDATED
Current Objective
Relationships

KNOWN
Profession
Location
Student
Captain Department
```

This is the first real product demo.

Upload Chapter 1.

Upload Chapter 2.

SceneSmith answers:

```text
Here is everything that changed.
```

If SceneSmith can do that with evidence, it is proving the product.

---

# Canon Rebuild Test

The Canon Test proves continuity.

The Canon Rebuild Test proves deterministic behavior.

Run:

```text
Empty Project
-> Import Chapter 1
-> Import Chapter 2
-> Import Chapter 3
-> Import Chapter 4
-> Generate Character Cards
-> Generate World Sheets
-> Generate Scene Sheets
-> Generate Continuity Report
-> Generate Prompt Packs
-> Save Outputs
-> Delete Project
-> Repeat
-> Byte Compare
```

SceneSmith must compare:

* Output bytes
* Character count
* Fact count
* Relationship count
* State-change count
* Evidence count
* Prompt count
* Continuity report counts
* Warnings
* Errors

If the outputs or counts differ between rebuilds, V1 is not complete.

The automated Canon Rebuild ladder must also verify:

* Incremental imports converge with full empty-project rebuilds
* Out-of-order explicit chapters are rejected or require an explicit rebuild path
* Saved outputs remain byte-stable across repeated rebuilds
* Passing validation case results include actual metrics and no errors
* Validation totals reconcile passed and failed case counts
* Validation suite results cannot be empty
* Validation suite results cannot contain duplicate case IDs

---

# SceneSmith V1 RC1

SceneSmith reaches Release Candidate 1 only when:

* Architecture is frozen
* No new V1 core systems are being added
* All implemented V1 systems satisfy the universal checklist
* All required subsystem acceptance criteria pass
* Canon Rebuild Test passes
* 10-chapter continuity test passes
* No known critical bugs remain
* Documentation is complete enough for another engineer to inherit the project

Allowed work after RC1:

* Bug fixes
* Performance improvements
* UX improvements
* Test coverage
* Documentation corrections

Not allowed after RC1:

* New core systems
* New architecture
* Major redesigns
* Scope expansion disguised as polish

RC1 is a confidence milestone.

It means SceneSmith is stable enough to prepare for Version 1 release validation.

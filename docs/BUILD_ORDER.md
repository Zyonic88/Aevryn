# SceneSmith Build Order

SceneSmith is built documentation-first.

No subsystem should be implemented until its purpose, authority, boundaries, failure modes, and tests are understood.

The product must be proven in the terminal before any website, user account system, payment system, subscription system, AI chat, or image generation work begins.

## Phase 0: Project Foundation

* Repository structure
* Development rules
* Architecture outline
* Python project configuration
* Test package scaffold

## Phase 1: Core Data Model

This is the first real code.

Not AI.

Not extraction.

Just data.

Define:

* Story
* Chapter
* Scene
* Entity
* Character
* Location
* Item
* Relationship
* Fact
* Evidence
* TimelineEvent
* StateChange
* SceneSnapshot

Nothing else.

No application logic.

## Phase 2: Canon Database

Not AI.

Just storage.

It must answer:

* Store Character
* Retrieve Character
* Update Character
* Version Character
* Retrieve State at Chapter X

If it can answer those questions, move on.

## Phase 3: Story Import

Build source structure before extraction.

Order:

* Import TXT
* Import Markdown
* Import HTML
* Import FB2
* Import DOCX
* Import ODT
* Import EPUB
* Fail clearly for deferred PDF, MOBI, and AZW3 support
* Split Chapters
* Split Scenes
* Paragraph IDs
* Sentence IDs
* Evidence anchors

Nothing extracted yet.

## Phase 3A: Web Import Boundary

Web Import is documented as a source-intake boundary.

For V1, it should not replace manual upload or pasted chapters.

It may later support:

* URL intake
* Metadata preview
* Chapter list preview
* Import permission checks
* Source attribution

It must respect site terms, robots.txt, login and paywall rules, and rate limits.

It must never present scraped copyrighted text as SceneSmith-owned content.

## Phase 3B: Translation Engine Boundary

Translation is documented as an optional source-normalization boundary.

It may run after Story Import and before Entity Extraction:

```text
Import Source
-> Translate / Normalize
-> Extract Entities
-> Update Canon
```

It should preserve:

* Meaning
* Tone
* Names
* Titles
* Power systems
* Item names
* Faction names
* Dialogue intent
* Story continuity

It must translate for meaning, preserve canon, and never change story facts.

For V1, Translation must not block the core continuity loop.

## Phase 4: Entity Extraction

AI enters here.

Not before.

Feed the AI a Scene.

Extract:

* Characters
* Locations
* Items
* Facts
* Relationships
* State changes

The AI is not responsible for remembering.

Only extracting.

First proof:

```text
Upload or paste one real chapter
-> SceneSmith extracts candidates
-> Canon accepts or rejects
-> Character card updates
-> Prompt updates
```

## Phase 5: Canon Updating

The AI may say:

```text
Mark now owns Iron Sword.
```

SceneSmith asks:

* Evidence?
* Confidence?
* Current Canon?
* Version Update?

Only then does Canon change.

## Phase 6: Timeline Engine

Timeline Engine asks:

* What chapter is this?
* What scene is this?
* What changed here?
* When is this fact valid?
* What is the current story position?

It owns chapter order, scene order, events, state-change validity, and history reconstruction.

It does not extract entities, own canon truth, or generate prompts.

Canon stores truth.

Timeline tells SceneSmith when that truth is valid.

## Phase 7: Character Cards

Character Engine asks Canon.

Character cards should show:

* Current state
* Previous state
* Valid From
* Evidence

## Phase 8: World Engine

World Engine asks Canon and Timeline.

It reconstructs the current state of the story world.

It should show:

* Locations
* Buildings
* Vehicles
* Organizations
* Items
* Creatures
* Regions
* Weather
* Environmental conditions
* Ownership
* Damage
* Resources
* Infrastructure

World Engine is a read layer.

World changes.

Characters move through it.

Relationships connect them.

## Phase 9: Scene Context

Scene Engine asks:

* Canon
* Timeline
* Character Engine
* World Engine

It reconstructs what is true at a scene.

## Phase 10: Scene Analyzer

Scene Analyzer asks:

* What happened?
* Why does it matter?
* What changed?
* What is the mood?
* What should production focus on?

It outputs:

* Scene Summary
* Purpose
* Conflict
* Mood
* Visual Highlights
* Character Goals
* Important Objects
* Environment Summary
* Changes Introduced
* Continuity Notes

Prompt Engine should use Scene Analyzer output instead of raw chapter text.

## Phase 11: Prompt Generation

Prompt Engine asks Scene Engine.

No guessing.

No AI ownership of truth.

## Phase 12: Presentation Engine

Presentation Engine turns backend truth into human-readable views.

It outputs:

* Character Profiles
* Scene Sheets
* Continuity Notes
* Prompt Pack Views
* Timeline Views
* Relationship Maps
* World State

Backend preserves truth.

Frontend presents clarity.

## Phase 13: Export

Export Engine writes portable outputs:

* JSON
* Markdown
* CSV
* Character Sheets
* Scene Sheets
* Prompt Sheets

## What We Do Not Build Yet

* Website
* Login
* Payments
* Subscriptions
* AI chat
* Image generation

None of these prove the product.

## CLI First

The first proof should be ugly and useful.

Example:

```text
scenesmith import chapter_001.txt
scenesmith extract
scenesmith character Mark
scenesmith scene 42
scenesmith prompt scene 42
```

If the CLI works, the website becomes a presentation layer.

## Project Manager

The CLI should not own workflow logic.

Project Manager coordinates the proof workflow:

```text
Import
-> Extract Candidates
-> Canon Update
-> Character Cards
-> Scene Context
-> Prompt Bundle
-> Export
```

It coordinates existing systems only.

It does not own canon truth.

## V1 RC1 Status

SceneSmith has reached V1 RC1 for the implemented continuity engine.

Implemented RC1 systems:

* Story Import
* Entity Extraction
* Canon Updating
* Canon Engine
* Timeline Engine
* Character Engine
* World Engine
* Scene Engine
* Scene Analyzer
* Prompt Engine
* Presentation Engine
* Export Engine
* Project Manager
* CLI Proof Workflow

Boundary systems:

* Translation Engine is foundation-only.
* Web Import is documented-only.

Current validation:

```text
cases=8 passed=8 failed=0
files=80
chapters=80
scenes=80
anchors=8828
Validation Score: 100%
digest=b911bda5279c30ead1830f58efa640d83bc66e41f3a50e96846804b428dec9d1
```

## Architecture Freeze

After Story Import, Core Data Model, Canon, Timeline, Character, World, Scene, Scene Analyzer, Prompt, Presentation, Export, and CLI proof are working, the architecture is considered complete.

No new systems should be added without a deliberate architecture review.

Future work should focus on implementation, tests, and refinement inside the existing systems.

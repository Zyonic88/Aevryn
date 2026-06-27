# Aevryn Presentation Engine

## What Is It?

The Presentation Engine converts internal Aevryn truth into clean human-readable views.

It does not store truth.

It does not export files.

It prepares view models for people.

## Why Does It Exist?

Aevryn internally works like a compiler:

```text
Evidence
-> Facts
-> Relationships
-> State Changes
-> Canon
```

That structure is excellent for machines.

Humans need clarity.

Creators need character profiles, scene sheets, continuity notes, prompt packs, timeline views, and relationship maps that can be scanned quickly.

## What Authority Does It Own?

The Presentation Engine owns:

* Character Profile views
* Scene Sheet views
* World Sheet views
* Timeline View models
* Relationship Graph view models
* Continuity Report views
* Prompt Pack views
* Human-readable grouping
* Human-readable section labels
* Human scan order

It turns internal truth into clean structured views.

## V1 Rules

Presentation Engine is deterministic.

It creates view models only.

It never writes files.

It never changes Canon meaning.

Scene sheets must use analysis for the same scene.

Production pack views must use packs and scene sheets for the same scene.

Visible presentation sections must not contain blank titles or blank items.

Visible presentation sections must not contain duplicate items.

Visible presentation section titles and items are whitespace-normalized before rendering.

Multi-section presentation views must not repeat visible section titles.

Repeated display items are deduplicated.

Long prompt lines are shortened for scan-friendly views.

Prompt pack views must remove raw structural placeholders such as empty section labels, Unknown-only entries, and duplicated Markdown bullet markers.

Character profile grouping must use genre-neutral attribute categories such as goals, tasks, plans, equipment, abilities, assets, relationships, and limitations.

It must not depend on one test story's names, factions, power systems, vehicles, or item labels.

Unknown information remains Unknown.

## What Does It NOT Own?

The Presentation Engine does not own:

* Canon truth
* Evidence
* Fact storage
* Relationship storage
* State changes
* Timeline validity
* Scene analysis
* Prompt text generation
* File export
* Frontend rendering

Presentation is not Export.

Presentation creates the pretty object.

Export writes it.

## How Does It Fail?

Presentation Engine can fail if:

* It hides important continuity state.
* It changes the meaning of facts.
* It invents summaries not supported by Canon or Scene Analyzer.
* It exposes raw machine data by default.
* It creates walls of text.
* It makes evidence impossible to inspect.
* It optimizes for AI instead of users.
* It presents analysis for the wrong scene.
* It presents a production pack under the wrong scene sheet.
* It emits blank visible rows.
* It emits duplicate section headings inside one view.
* It repeats the same fact until the view becomes noisy.

The core question:

```text
Could a tired creator understand this in five seconds?
```

If not, the presentation view needs work.

## How Does It Interact With Other Systems?

Canon, Timeline, and Scene Analyzer provide backend truth and meaning.

Presentation Engine prepares clean structured view models.

Frontend components render those view models.

Export Engine serializes those view models.

Raw machine files remain available for advanced details and evidence inspection.

## Core Rule

Backend preserves truth.

Frontend presents clarity.

Presentation Engine is the bridge.

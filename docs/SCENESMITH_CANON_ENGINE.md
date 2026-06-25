# SceneSmith Canon Engine

## What Is It?

The Canon Engine is SceneSmith's source of truth for the current state of a story.

It has one responsibility:

Maintain the current truth of the story.

Not generate.

Not infer wildly.

Not create.

Simply remember.

## Why Does It Exist?

Long-form stories change over time.

Characters gain weapons.

Locations are damaged.

Relationships shift.

Organizations rise and fall.

The Canon Engine exists so SceneSmith can remember those changes without asking AI to reconstruct the whole story from scratch every time.

## What Authority Does It Own?

The Canon Engine owns the canonical state of:

* Characters
* Locations
* Items
* Weapons
* Armor
* Skills
* Organizations
* Relationships
* Buildings
* Vehicles
* Creatures
* Timeline Events

Every entity gets evidence-backed treatment.

Example:

```text
Mark

Current Weapon:
Steel Sword

Previous:
Rusty Dagger

Chapter Changed:
14

Confidence:
High

Evidence:
Chapter 14 paragraph 6
```

## What Does It NOT Own?

The Canon Engine does not own:

* Source document parsing
* AI extraction logic
* Prompt generation
* Export formatting
* User interface behavior
* Project file management
* Story generation
* Image generation

Other systems may read from canon or submit evidence to canon, but the Canon Engine alone decides how canonical state is stored, versioned, and retrieved.

AI extraction may propose facts, but it never owns truth.

The Canon Engine owns truth.

## How Does It Fail?

The Canon Engine can fail if:

* A fact has no evidence.
* A fact points to the wrong chapter or scene.
* A new value overwrites old state instead of creating version history.
* Two facts conflict and the conflict is not preserved.
* An entity receives a new ID when it should keep the same permanent ID.
* Unknown information is treated as known.

When the Canon Engine cannot prove a fact, the correct state is Unknown.

## How Does It Interact With Other Systems?

Story Import provides ordered source material.

Extraction systems eventually submit evidence-backed facts.

The Timeline Engine uses canon history to reconstruct state at a specific chapter or scene.

The Character Engine reads and organizes character-specific canon.

The World Engine reads and organizes location, building, and environment canon.

The Scene Engine reads canon to assemble accurate scene context.

The Prompt Engine reads canon-backed scene context to produce prompts.

The Export Engine formats canon data for external tools.

## The Canon Rule

Every fact must have evidence.

Every record contains:

* Current Value
* Confidence
* Evidence
* Chapter
* Scene
* Last Updated

Example:

```text
Character:
Mark

Weapon:
Steel Sword

Confidence:
1.0

Evidence:
Chapter 27
Scene 3

Previous:
Iron Sword

Updated:
Chapter 27
```

## Version History

This is critical.

Never overwrite.

Always version.

Instead of:

```text
Weapon = Steel Sword
```

Store:

```text
Chapter 1
Rusty Dagger

v

Chapter 8
Iron Sword

v

Chapter 27
Steel Sword
```

Now Scene 12 can still render correctly.

## Entity IDs

Every object gets a permanent ID.

Example:

```text
character_mark
location_northern_forest
weapon_rusty_dagger
```

The name can change.

The ID never changes.

## Relationships

Everything becomes connected.

Example:

```text
Mark

owns

Steel Sword

located_at

Northern Fortress

travels_with

Luna
```

Eventually SceneSmith will have a graph.

## One Database

Everything should live in one logical model.

Not:

```text
character database
weapon database
location database
```

Instead:

```text
Canon Database
+-- Characters
+-- Items
+-- Locations
+-- Events
+-- Relationships
```

## The Biggest Design Rule

The Canon Engine never asks:

What do I think?

It asks:

What does the story currently say?

That is a huge distinction.

The AI may help find evidence.

The Canon Engine decides what becomes canon.

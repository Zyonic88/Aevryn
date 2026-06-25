# SceneSmith Data Model

## Purpose

This document defines the core concepts that all SceneSmith systems share.

It is conceptual, not implementation-specific.

Everything in SceneSmith should eventually map to one of these concepts.

## Story

A Story is the top-level imported work.

It contains Chapters.

It is the root container for source structure, canon, timeline, scene context, prompts, and exports.

## Chapter

A Chapter is an ordered section of a Story.

It contains Scenes.

It has a stable chapter ID and chapter index.

## Scene

A Scene is an ordered unit inside a Chapter.

It contains source paragraphs and sentences.

It has a stable scene ID and scene index.

## Entity

An Entity is a permanent thing in the story.

Examples:

* Character
* Location
* Item
* Weapon
* Building
* Organization
* Creature

An Entity has a permanent ID.

The name can change.

The ID never changes.

## Character

A Character is an Entity that represents a person or person-like actor in the story.

Character-specific state belongs in Canon and is presented by the Character Engine.

## Location

A Location is an Entity that represents a place in the story.

Locations may have changing ownership, damage, weather, and environment state.

## Item

An Item is an Entity that can be owned, carried, lost, damaged, upgraded, or moved.

Weapons and armor are specialized items.

## Fact

A Fact is a claim about an Entity.

Examples:

* Mark has an Iron Sword.
* Luna is injured.
* The Northern Fortress is damaged.

A Fact must have Evidence.

If there is no evidence, the value is Unknown.

AI may extract or propose a Fact, but AI does not make it true.

Only evidence-backed Canon can make a Fact canonical.

## Evidence

Evidence proves where a Fact came from.

Evidence should identify:

* Source
* Chapter
* Scene
* Paragraph
* Sentence
* Quote or excerpt
* Confidence

Evidence begins with Story Import.

AI extraction may point to Evidence, but Story Import owns the stable source anchor.

## Relationship

A Relationship connects two Entities.

Examples:

```text
Mark owns Iron Sword
Mark travels_with Luna
Luna located_at Northern Forest
Northern Fortress controlled_by Iron Kingdom
```

Relationships are also evidence-backed.

## Timeline Event

A Timeline Event is something that happens at a story position.

Examples:

* Mark buys the Iron Sword.
* The bridge collapses.
* Luna leaves the party.

Timeline Events give meaning to when state changes happen.

## State Change

A State Change records when a Fact becomes valid and when it stops being valid.

Examples:

```text
Current Weapon: Iron Sword
Valid From: Chapter 8, Scene 2
Valid Until: Chapter 20, Scene 3
```

State Changes connect Canon truth to Timeline validity.

## Scene Snapshot

A Scene Snapshot is the reconstructed state of a scene.

It answers:

```text
What is true right now?
```

A Scene Snapshot may include:

* Characters present
* Character state
* Location state
* Environment state
* Active relationships
* Active state changes
* Timeline events

## Concept Flow

```text
Story Import
-> Evidence
-> Facts and Relationships
-> Canon
-> Timeline State Changes
-> Character Cards
-> Scene Snapshots
-> Prompts
-> Exports
```

## Data Model Rule

Do not create a new core concept unless it cannot honestly fit into:

* Entity
* Fact
* Evidence
* Relationship
* Timeline Event
* State Change
* Scene Snapshot

No logic belongs in the core data model phase.

Only data definitions belong there.

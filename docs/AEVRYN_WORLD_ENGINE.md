# Aevryn World Engine

## What Is It?

The World Engine reconstructs the current state of the story world from accepted Canon.

It covers World Objects.

World Objects are non-character story entities that describe the world characters move through.

World Objects include:

* Locations
* Buildings
* Cities
* Regions
* Kingdoms
* Political boundaries
* Organizations
* Items
* Vehicles
* Creatures
* Weather
* Environmental conditions
* Natural resources
* Infrastructure
* Ownership
* Damage
* Reconstruction

The World Engine does not create canon.

It reads canon.

---

## Why Does It Exist?

Stories do not only change characters.

Worlds change too.

A fortress can be damaged.

A city can change ownership.

A kingdom can fall.

A battlefield can become a ruin.

Aevryn needs a dedicated system that can answer:

* What is true about this location right now?
* Who owns this building?
* What damage exists?
* What organizations control this place?
* What world facts are valid at this chapter?
* What world facts are valid at this scene?
* What evidence supports those facts?

Without the World Engine, Aevryn would understand characters but fail to preserve the world around them.

---

## Authority Owned

The World Engine owns world-state views.

It may build:

* World State
* World Snapshot
* Location State
* Building State
* Organization State
* Item State
* Vehicle State
* Creature State
* Environmental State

It may answer:

* Current world facts
* Current ownership
* Current damage
* Current population when evidence exists
* Current threat level when evidence exists
* Current environmental state
* Current connected relationships
* Evidence for world facts

Example World Snapshot:

```text
Chapter 14

Northern Fortress

Owner:
Empire

Damage:
35%

Population:
Unknown

Weather:
Snow

Threat Level:
Medium

Evidence:
42 verified facts
```

---

## Authority Not Owned

The World Engine does not own:

* Story import
* Entity extraction
* Canon truth
* Timeline validity
* Character cards
* Scene analysis
* Prompt generation
* Presentation formatting
* Export writing

If the World Engine needs truth, it asks Canon.

If the World Engine needs story position, it uses the requested chapter or scene context.

It never invents missing world facts.

Characters never own world state.

World never owns character state.

Relationships connect characters and World Objects.

---

## Failure Modes

The World Engine fails when:

* A requested world entity does not exist in Canon
* A world fact references missing evidence
* Canon has no accepted facts for the requested entity
* The requested chapter has no active world state
* Relationships exist but the connected entity was never accepted
* A world state contains duplicate entity entries
* World output contains malformed IDs, blank display values, or invalid chapter indexes
* Scene-position world output leaks facts or relationships from a later scene

Unknown world details remain Unknown.

Missing information must not be guessed.

---

## Interaction With Other Systems

```text
Story Import
-> Canon Engine
-> Timeline Engine
-> Character Engine
-> Scene Engine
-> Scene Analyzer
-> Prompt Engine
-> Presentation Engine
-> Export Engine

Story Import
-> Canon Engine
-> Timeline Engine
-> World Engine
-> Scene Engine
-> Scene Analyzer
-> Prompt Engine
-> Presentation Engine
-> Export Engine
```

The World Engine consumes accepted Canon records.

The Character Engine and World Engine are siblings.

Neither owns the other.

Relationships connect characters to World Objects.

The Scene Engine may use World Engine output when reconstructing a scene.

The Scene Analyzer should use world state through the Scene Engine and World Engine boundary to identify environment, mood, conflict, and visual highlights.

The Prompt Engine may use world state through Scene Engine and Scene Analyzer output.

The Presentation Engine turns World Engine output into human-readable world sheets.

The Export Engine writes those sheets to files.

---

## V1 Rule

The World Engine is a read layer.

It does not mutate Canon.

It does not call AI.

It does not summarize scenes.

It only reconstructs world state from evidence-backed truth.

The World Engine is deterministic.

Given the same Canon and the same chapter, it must always produce the same world state.

Given the same Canon, chapter, and scene, it must always produce the same scene-position world state.

World-state visible names and fact values are whitespace-normalized for stable display.

Scene-position world state must not expose facts or relationships introduced later in the same chapter.

World Engine output is only for World Objects.

Character entities are rejected.

Selected world entity IDs must be nonblank machine-safe tokens.

Relationship endpoints must resolve to accepted Canon entities.

Display names come from active Canon display-name facts when they exist.

World state view models must reject malformed output:

* World entity IDs are required and must be machine-safe.
* World entity types are required and must be machine-safe.
* Display names are required.
* Chapter indexes are one-based.
* World fact attributes are required and must be machine-safe.
* World fact values are required.
* Valid-from source IDs must be machine-safe.
* A World State cannot include the same entity more than once.

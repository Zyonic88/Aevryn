# SceneSmith Scene Engine

## What Is It?

The Scene Engine assembles scene context for a specific story position.

It answers:

```text
What is true in this scene?
```

It does not generate prompts.

It prepares accurate context for systems that do.

## Why Does It Exist?

Creators need scene-specific continuity.

Given a scene, SceneSmith should know:

* Who is present
* Where the scene happens
* When it happens
* What each character currently has
* What injuries or status changes apply
* What relationships matter
* What world or environment state is active

The Scene Engine exists so prompt generation and exports do not have to guess.

## What Authority Does It Own?

The Scene Engine owns:

* Scene context assembly
* Character cards present in a scene
* Environment snapshots for a scene
* Active timeline events for a scene
* Active timeline state changes for a scene

It turns Canon, Timeline, and Character data into one scene-ready context object.

## V1 Rules

The Scene Engine is deterministic.

Given the same Canon, Timeline, imported scene, and selected entities, it must return the same scene context.

Repeated selected entity IDs are deduplicated.

Relationships are deduplicated and returned in stable order.

Scene snapshots may include related location IDs when Canon relationships prove them.

Scene context must be timeline-aware.

Scene context snapshots must match the context's scene, character cards, active facts, and relationships.

Scene context view models must reject impossible state:

* Context position must match the Timeline scene position.
* Character cards in the context must match the context position.
* Characters and environment snapshots cannot be duplicated.
* Environment fact keys must match their fact attributes.
* Timeline events must match the context position.
* Active state changes cannot start in the future or already be expired.

When reconstructing a scene, facts or relationships introduced in later chapters or later scenes in the same chapter must not appear.

Character cards embedded in scene context must use the requested scene position, not only the chapter position.

Scene-relevant facts are selected through genre-neutral attribute categories such as status, role, appearance, equipment, goals, tasks, plans, rules, assets, locations, mood, injuries, promises, abilities, and limitations.

Scene relevance must not depend on one test story's names, factions, power systems, or vehicles.

The Scene Engine never generates prompt text.

## What Does It NOT Own?

The Scene Engine does not own:

* Canon fact storage
* Timeline order
* Character card rules
* Prompt generation
* Image generation
* Export formatting
* Story import
* AI extraction

It reads other systems.

It does not replace them.

## How Does It Fail?

The Scene Engine can fail if:

* The requested scene position does not exist.
* It includes characters that are not registered in canon.
* It ignores Timeline validity.
* It leaks future facts or relationships into an earlier scene.
* It leaks later same-chapter facts through embedded character cards.
* It invents missing environment details.
* It mutates Canon or Timeline state.
* It produces prompt text instead of scene context.
* It duplicates characters, facts, or relationships because of repeated inputs.
* Its snapshot IDs disagree with the context data they are meant to summarize.
* Its scene position, events, character cards, or active state changes disagree with one another.

Unknown scene details remain absent until supported by Canon and Timeline.

## How Does It Interact With Other Systems?

The Timeline Engine provides scene position, scene metadata, events, and active state changes.

The Character Engine provides living character cards for characters present in the scene.

The Canon Engine provides environment and world snapshots.

The Prompt Engine will eventually consume Scene Engine context to generate prompts.

The Export Engine can output Scene Engine context as scene sheets.

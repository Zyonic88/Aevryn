# Aevryn Architecture

Aevryn is a Story Continuity Engine.

Its responsibility is to understand existing stories and maintain their current canonical state.

It is not a story generator, image generator, or chatbot.

## Architectural Principle

The Canon Engine is the source of truth.

Every other subsystem either feeds evidence into canon, reads canon to produce context, or exports canon for external tools.

## Subsystems

### Story Import System

Owns ingestion of source material.

Responsibilities:

* Parse supported document formats
* Preserve source order
* Split stories into chapters
* Split chapters into scenes

Does not own canon decisions.

### Canon Engine

Owns the current truth of the story.

Responsibilities:

* Store evidence-backed facts
* Preserve unknown information as Unknown
* Track confidence
* Maintain current state

Does not invent missing details.

### Character Engine

Owns character-specific state and history.

Responsibilities:

* Appearance
* Clothing
* Weapons
* Equipment
* Injuries
* Personality
* Relationships
* Status
* Current location

Does not own global timeline authority.

### World Engine

Owns location and environment state.

Responsibilities:

* Cities
* Buildings
* Villages
* Kingdoms
* Weather
* Environment
* Ownership
* Damage
* Reconstruction

Does not own character state.

### Timeline Engine

Owns story order and state reconstruction over time.

Responsibilities:

* Chapter sequence
* Scene sequence
* Event sequence
* State lookup at a specific point in the story

Does not extract facts directly from prose.

### Scene Engine

Owns scene context generation.

Responsibilities:

* Characters present
* Environment
* Time
* Weather
* Equipment
* Active relationships
* Current world state

Does not change canon.

### Prompt Engine

Owns production-ready prompt creation.

Responsibilities:

* AI image prompts
* Narration prompts
* Camera prompts
* Animation prompts

Does not create canon or invent unknown facts.

### Export Engine

Owns output formatting.

Responsibilities:

* JSON
* Markdown
* CSV
* Character sheets
* Scene sheets
* Prompt sheets

Does not modify canon.

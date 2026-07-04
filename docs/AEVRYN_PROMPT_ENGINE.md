# Aevryn Prompt Engine

See also: [Aevryn Prompting Philosophy](AEVRYN_PROMPTING_PHILOSOPHY.md).

## What Is It?

The Prompt Engine turns Scene Analyzer output and Scene Engine context into production-ready prompt text and production packs.

It creates structured prompts for:

* Images
* Narration
* Camera direction
* Animation direction

It also assembles Production Packs containing:

* Scene summary
* Character cards
* Environment
* Visual highlights
* Image prompt
* Narration prompt
* Camera prompt
* Animation prompt
* Continuity notes
* Forbidden elements

It does not call AI services.

It does not generate images.

The prompt is the final presentation of structured story understanding. It is not a substitute for that understanding.

## Why Does It Exist?

Creators need consistent prompts that match the current canon state of a scene.

The Prompt Engine exists so generated media can reference:

* Current character state
* Current equipment
* Current environment
* Scene Analyzer summary
* Active state changes

The prompt should be based on Scene Analyzer output and accepted canon, not guesses.

Prompt quality should improve because Aevryn understands the story better, not because the prompt text adds unsupported adjectives.

## What Authority Does It Own?

The Prompt Engine owns:

* Prompt text assembly
* Production pack assembly
* Prompt section formatting
* Prompt type selection
* Converting analyzed scene context into prompt-ready language

It is a formatter of known context and analyzed scene meaning.

## V1 Rules

The Prompt Engine is deterministic.

It consumes Scene Engine and Scene Analyzer output.

It does not reach into Canon or Timeline directly.

Prompt sections must be concise and production-ready.

Character details in prompts must come from scene-relevant context facts, not the full living character card.

Prompt character details should omit mechanical metadata such as task rewards, penalties, and feasibility scores unless that metadata is explicitly needed by a future prompt mode.

Repeated bullets and prompt lines are deduplicated.

Long analysis text is shortened before entering prompts.

Prompt Engine never calls external AI tools.

Prompt outputs must not be blank.

Production Pack scene IDs are whitespace-free machine tokens.

Production Packs must reference Scene Analyzer output for the same scene ID.

Production Pack list fields must not contain blank visible rows.

Production Pack list fields are whitespace-normalized before uniqueness checks.

Production Pack list fields must not contain duplicate visible rows.

`Unknown` is allowed when evidence is absent.

## Production Prompt Rules

Prompt sections must separate:

* Story facts
* Scene meaning
* Character state
* World and environment context
* Important objects
* Prompt-type direction
* Forbidden elements

Story facts come first.

Scene meaning comes second.

Style comes last.

The Prompt Engine must prioritize current-scene truth over retained background canon.

Scene production briefs should answer:

* What is happening right now?
* Where is it happening?
* Who is present?
* What world or object details matter?
* What should not appear?

Prompt Packs must consume resolved identities. Prompt generation does not perform entity resolution.

Prompt Packs must consume normalized Canon and scene context. Prompt generation does not own translation.

World, location, item, vehicle, system, and object details should enter prompts only through accepted scene context.

Unknown information remains Unknown and must not be replaced by assumptions.

Forbidden elements should be explicit enough to prevent generation tools from adding unsupported characters, objects, vehicles, logos, settings, or physical traits.

## What Does It NOT Own?

The Prompt Engine does not own:

* Canon state
* Timeline validity
* Character cards
* Scene context assembly
* Scene analysis
* AI service calls
* Image generation
* Video generation
* Narration generation
* Export files

It prepares prompts.

It does not execute them.

## How Does It Fail?

The Prompt Engine can fail if:

* It invents missing canon.
* It ignores scene context or Scene Analyzer output.
* It reaches into Canon or Timeline directly instead of using Scene Engine context.
* It mixes prompt types incorrectly.
* It produces empty or misleading prompts.
* It calls external AI services.
* It re-dumps raw chapter text instead of concise scene context.
* It dumps full character cards instead of scene-relevant character facts.
* It lets mechanical metadata crowd out production-relevant scene details.
* It repeats the same facts or notes until the prompt becomes noisy.
* It combines prompt output and scene analysis from different scenes.
* It emits blank visual highlights, goals, objects, notes, or forbidden elements.
* It emits duplicate visual highlights, goals, objects, notes, or forbidden elements.

Unknown information must remain absent or explicitly Unknown.

## How Does It Interact With Other Systems?

The Scene Engine provides complete scene context.

The Scene Analyzer provides compact scene meaning.

The Prompt Engine turns that context into prompt text and production packs.

The Export Engine can later write prompt sheets.

External AI tools can consume prompt text, but the Prompt Engine does not call them.

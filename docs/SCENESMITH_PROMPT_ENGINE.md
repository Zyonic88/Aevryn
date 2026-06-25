# SceneSmith Prompt Engine

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

## Why Does It Exist?

Creators need consistent prompts that match the current canon state of a scene.

The Prompt Engine exists so generated media can reference:

* Current character state
* Current equipment
* Current environment
* Scene Analyzer summary
* Active state changes

The prompt should be based on Scene Analyzer output and accepted canon, not guesses.

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

Repeated bullets and prompt lines are deduplicated.

Long analysis text is shortened before entering prompts.

Prompt Engine never calls external AI tools.

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
* It repeats the same facts or notes until the prompt becomes noisy.

Unknown information must remain absent or explicitly Unknown.

## How Does It Interact With Other Systems?

The Scene Engine provides complete scene context.

The Scene Analyzer provides compact scene meaning.

The Prompt Engine turns that context into prompt text and production packs.

The Export Engine can later write prompt sheets.

External AI tools can consume prompt text, but the Prompt Engine does not call them.

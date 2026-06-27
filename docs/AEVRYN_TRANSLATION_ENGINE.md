# Aevryn Translation Engine

## What Is It?

The Translation Engine converts imported source text into another language while preserving story meaning and canon continuity.

It is not a normal text translator.

It is localization-aware story translation.

It translates for meaning, preserves canon, and never changes story facts.

## Why Does It Exist?

Many long-form stories are written in Chinese, Korean, Japanese, English, Spanish, French, and other languages.

Creators may want to produce recaps, narration, prompts, and character sheets in a different language than the original source.

A normal translator can preserve words while damaging story continuity.

Aevryn needs translation that preserves:

* Meaning
* Tone
* Names
* Titles
* Power systems
* Item names
* Faction names
* Dialogue intent
* Story continuity

## What Authority Does It Own?

The Translation Engine owns:

* Translation workflow
* Localization mode selection
* Glossary and term-bank checks
* Name preservation
* Alias detection
* Title and honorific handling
* Sentence restructuring
* Dialogue intent preservation
* Canon term consistency
* Translation-to-source evidence links

It may produce:

* Literal translation
* Clean English translation
* Localized translation
* Subtitle or narration translation
* Translated scene text

## What Does It NOT Own?

The Translation Engine does not own:

* Canon truth
* Entity extraction
* Story Import structure
* Timeline validity
* Character cards
* Scene context
* Prompt generation
* Export formatting
* Source access permissions
* Copyright bypass

It does not decide whether a translated statement is canon.

It does not invent missing information.

It does not rewrite story events.

## How Does It Fail?

The Translation Engine can fail if:

* A name is translated inconsistently.
* A title or honorific changes meaning.
* A power-system term is localized incorrectly.
* An item, ship, skill, or faction name changes between chapters.
* Dialogue intent changes.
* Emotional tone is flattened or exaggerated.
* Literal phrasing becomes awkward English.
* Natural rewriting changes who did what.
* Translated text loses source evidence links.
* The translation inserts unsupported facts.

When uncertain, Translation should preserve the original term and mark it for glossary review.

Unknown stays unknown.

## How Does It Interact With Other Systems?

Story Import creates source anchors from the original text.

Translation Engine may run after Story Import and before Entity Extraction.

It produces translated scene text that still points back to original source anchors.

Entity Extraction may read translated or normalized scene text, but extracted candidates must still cite evidence anchors.

Canon Updating accepts or rejects extracted candidates.

Canon Engine stores truth, not translations.

Prompt Engine may use translated canon-safe scene context for prompts.

Export Engine may export translated sheets, subtitles, narration text, or localized prompt sheets.

## Translation Flow

```text
Source Text
-> Literal Translation
-> Context Review
-> Canon Term Check
-> Natural Language Rewrite
-> Consistency Pass
-> Translated Scene
```

## Glossary / Term Bank

The Translation Engine should maintain consistent terms.

Examples:

* Zhao Chen always remains Zhao Chen.
* Super Starfleet System stays consistent.
* T3 Blizzard-class Light Interstellar Battlecruiser stays consistent.
* Fleet Luck Bonus stays consistent.
* Eye of Insight stays consistent.

Glossary entries should preserve:

* Source term
* Preferred translation
* Entity ID if known
* First evidence anchor
* Notes

## Name Handling

Translation must:

* Preserve names.
* Detect aliases.
* Detect titles.
* Detect honorifics.
* Avoid accidental name localization.
* Keep entity IDs stable across translation variants.

## Quality Modes

Translation should support:

* Literal
* Clean English
* Localization
* Subtitle/Narration

Literal mode prioritizes direct meaning.

Clean English mode removes awkward machine-translation phrasing.

Localization mode adapts phrasing while preserving story facts.

Subtitle/Narration mode optimizes for spoken or timed output.

## V1 Boundary

For V1, Translation is optional.

The core product remains continuity.

Translation should not block Canon, Timeline, Character, Scene, Prompt, or Export work.

Build it only after the core continuity loop is stable across multiple chapters.

## Core Rule

Translate for meaning.

Preserve canon.

Never change story facts.

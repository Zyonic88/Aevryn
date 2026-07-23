# Aevryn Sentence Understanding

> Built by **Aetherra Labs**

## Purpose

Sentence Understanding analyzes imported sentences into evidence-linked meaning
metadata.

It helps Aevryn understand what a sentence is doing before translation,
extraction, scene analysis, prompts, or presentation consume it.

This layer exists because stories often contain ambiguous language:

* one word may have multiple translations
* a title may also be a role
* a system term may also be an ordinary word
* a skill may look like an item name
* an item may be part of a system interface
* a pronoun may point to more than one character

Sentence Understanding gives downstream systems structured signals instead of
forcing them to guess from raw text alone.

## Core Rule

```text
Sentence Understanding observes meaning signals.
Canon decides truth.
```

## What It Owns

Sentence Understanding owns:

* sentence-level signal detection
* action cues
* dialogue cues
* item-reference cues
* skill-reference cues
* system-reference cues
* relationship-reference cues
* identity-reference cues
* translation ambiguity cues
* evidence-anchor linkage
* review-required metadata

It may say:

```text
This sentence appears to mention a skill.
This sentence appears to mention a system.
This sentence contains a term that may need translation review.
```

It must not say:

```text
This skill is Canon.
This system exists in Canon.
This translation meaning is definitely correct.
```

## What It Does NOT Own

Sentence Understanding does not own:

* Story Import
* Translation
* Entity Extraction
* Entity Resolution
* Canon Updating
* Timeline validity
* Character cards
* Prompt generation
* Export formatting

It does not store full manuscript sentences in understanding output.

It does not replace source evidence anchors.

It does not make Canon decisions.

## Workflow Position

```text
Story Import
-> Sentence Understanding
-> Translation Foundation
-> Entity Extraction
-> Entity Resolution
-> Canon Updating
-> Scene Analysis
-> Prompt Packs
```

Sentence Understanding may run directly after Story Import because Story Import
already creates sentence IDs and evidence anchors.

Translation may use sentence signals to preserve meaning when source terms are
ambiguous.

Entity Extraction may use sentence signals to decide whether to inspect for
items, skills, systems, relationships, or identity references.

The extraction prompt receives sentence-understanding summaries as metadata:

* evidence anchor ID
* signal names
* compact cue terms
* ambiguity terms
* review-required flag

It must not receive a second copy of the full source sentence through this
metadata channel.

Prompt Packs may eventually use accepted downstream meaning, not raw sentence
understanding, because prompts must remain Canon-backed.

## Translation Support

Sentence Understanding improves translation by identifying review-worthy terms
before translation chooses a meaning.

Examples:

* `dao`
* `qi`
* `core`
* `seal`
* `spirit`
* `vessel`
* `system`
* `art`

When a sentence contains an ambiguity cue, Aevryn should preserve the source
term or route it through glossary review instead of selecting a translation by
default.

For V2, Translation Foundation consumes sentence ambiguity as review metadata.
If a sentence marks `dao`, `qi`, `core`, `system`, or another compact cue as
ambiguous, the Translation Engine records a review issue tied to the original
evidence anchor. If a glossary term already requires review for that source
term, the glossary issue remains the single authority and duplicate sentence
issues are suppressed.

Sentence Understanding never sends a second copy of the source sentence into
Translation. It sends only the compact metadata required for review routing.

## Extraction Support

Sentence Understanding can help extraction focus on what each sentence is
probably doing:

* dialogue
* action
* description
* identity reference
* relationship reference
* item reference
* skill reference
* system reference
* translation ambiguity

These are routing hints, not Canon facts.

If a sentence has both item and skill signals, Aevryn should treat the sentence
as review-worthy instead of pretending the classification is obvious.

Sentence Understanding may also detect compact phrase cues when a single word is
too ambiguous on its own.

Examples:

* `status panel`
* `quest reward`
* `system interface`
* `sword technique`
* `cultivation art`
* `spirit core`

Phrase cues help route downstream extraction and translation review. They do
not create Canon entities. For example, `sword technique` may route as a skill
phrase without treating `sword` as a separate item unless the sentence also
describes an actual sword object.

## Privacy Boundary

Sentence Understanding output should remain metadata-only.

It may store:

* sentence ID
* evidence anchor ID
* chapter ID
* scene ID
* paragraph index
* sentence index
* signal names
* compact cue terms
* ambiguity terms
* review-required boolean

It must not store:

* full source sentences
* full paragraphs
* full chapters
* raw AI payloads
* generated translation prose

## Version 2 Boundary

For V2 public-beta readiness, Sentence Understanding is a foundation layer.

V2 does not need a full linguistic parser, dependency tree, grammar engine, or
public sentence-review UI.

V2 should provide:

* deterministic sentence signal detection
* evidence-anchor linkage
* ambiguity metadata
* tests proving no full sentence prose is stored in understanding output
* a clear boundary that downstream systems can consume later

Future versions may add deeper parsing, language-specific analyzers, provider
assisted semantic parsing, and creator-facing review tools.

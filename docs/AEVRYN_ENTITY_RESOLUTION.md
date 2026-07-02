# Aevryn Entity Resolution Engine

> Built by **Aetherra Labs**

The Entity Resolution Engine determines when different story references point to the same canonical entity.

It improves extraction accuracy without owning extraction itself.

Core rule:

```text
Extraction proposes entities.
Resolution determines identity.
Canon decides truth.
```

---

# Why It Exists

Stories rarely use one stable name for a character, organization, place, object, vehicle, faction, title, or creature.

Authors naturally alternate between:

* names
* aliases
* titles
* roles
* honorifics
* descriptions
* family relationships
* pronouns
* translated variants

Human readers resolve those references as identity.

Aevryn must do the same without inventing unsupported canon.

---

# Authority Boundary

The Entity Resolution Engine owns identity matching.

It owns:

* alias detection
* title detection
* pronoun resolution
* description matching
* canon-assisted identity matching
* confidence scoring
* surface-reference tracking
* identity ambiguity detection
* cross-scene identity resolution
* cross-chapter identity resolution
* translation-aware identity preservation

It may produce:

* resolved entity references
* unresolved entity candidates
* ambiguous identity candidates
* confidence scores
* surface-reference records
* identity evidence links

---

# What It Does Not Own

The Entity Resolution Engine does not own:

* Story Import
* Translation
* Entity Extraction
* Canon Updating
* Timeline validity
* Character sheet generation
* Prompt generation
* Export formatting

It must not create canon facts by itself.

It must not silently merge identities when confidence is too low.

It must not erase uncertainty.

---

# Example

Source references:

* Charlotte
* General Charlotte
* the General
* the white-haired beauty
* the female general
* the Half-Beastman
* she

Resolution output:

```text
Canonical entity: Charlotte
Surface references:
- Charlotte
- General Charlotte
- the General
- the white-haired beauty
- the female general
- the Half-Beastman
- she
```

The output is valid only when evidence supports that these references point to the same identity.

---

# Entity Identity Profile

A canonical entity may accumulate:

* canonical name
* stable entity ID
* aliases
* titles
* honorifics
* descriptions
* relationship labels
* pronoun evidence
* surface references
* first evidence anchor
* latest evidence anchor

Example:

```text
Canonical Name: Charlotte
Aliases: Charlotte, General Charlotte, Commander Charlotte
Titles: General, Commander
Descriptions: white-haired Half-Beastman, white-haired beauty, female general
Surface References: she, her, the woman, the commander
```

---

# Confidence Model

Every identity decision must carry a confidence score.

Example:

| Reference | Candidate | Confidence |
| --- | --- | --- |
| Charlotte | Charlotte | 0.99 |
| the General | Charlotte | 0.95 |
| the white-haired woman | Charlotte | 0.90 |
| she | Charlotte | 0.87 |
| the officer | Charlotte | 0.58 |

High-confidence decisions may resolve to an existing entity.

Low-confidence matches remain candidates.

Ambiguous references remain unresolved until additional evidence supports one identity.

---

# Translation Integration

Translation increases the importance of entity resolution.

Chinese, Korean, Japanese, and translated web-novel prose often avoid repeated names and rely on:

* titles
* honorifics
* occupations
* family roles
* physical descriptions
* pronouns
* faction roles

The Translation Engine and Entity Resolution Engine must cooperate to preserve stable entity IDs across translated and normalized text.

Translation may normalize language.

Resolution preserves identity.

Canon decides whether extracted facts become truth.

---

# Required Safety Rules

Entity Resolution must:

* preserve source evidence anchors
* preserve uncertainty
* avoid unsupported identity merges
* treat pronouns as context-dependent
* keep surface references auditable
* avoid using display names as the only identity signal
* keep extraction and canon updating separate
* remain deterministic for the same inputs

Unknown stays unknown.

Ambiguous stays ambiguous.

---

# Version 2 Boundary

Entity Resolution is now required for V2 story-understanding quality.

The V2 implementation may begin with deterministic identity profiles, confidence scoring, ambiguity handling, and source-backed surface-reference tracking.

Advanced AI-assisted entity resolution, user-editable merge review, and large-scale cross-project identity tools can wait for later versions.


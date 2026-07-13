# Aevryn V2 Phase 12 Acceptance

> Built by **Aetherra Labs**

Phase 12 adds the language and identity understanding required before Aevryn V2 can be considered complete for release-candidate readiness.

It promotes Translation Foundation and Entity Resolution Foundation from future or optional systems into required V2 quality gates.

---

# Phase 12 Name

```text
Language And Identity Understanding
```

Phase 12 has two slices:

* Phase 12A - Translation Foundation
* Phase 12B - Entity Resolution Foundation

---

# Core Rule

```text
Translation preserves meaning.
Resolution preserves identity.
Canon decides truth.
```

---

# Phase 12A - Translation Foundation

Translation Foundation is accepted when:

* translated or normalized text remains linked to original source evidence anchors
* names, titles, aliases, honorifics, factions, locations, items, skills, and power-system terms are preserved or glossary-controlled
* uncertain translations preserve the original term and mark it for review
* terms with multiple plausible meanings preserve the original term and expose metadata-only review context
* translation does not create canon facts
* translation does not remove source evidence
* extraction can consume normalized text while citing original anchors
* no full source prose is logged
* no full AI translation payload is logged
* deterministic tests cover glossary preservation, anchor preservation, and uncertainty handling

---

# Phase 12B - Entity Resolution Foundation

Entity Resolution Foundation is accepted when:

* aliases can resolve to an existing canonical entity with confidence
* titles can resolve to an existing canonical entity with confidence
* descriptions can resolve to an existing canonical entity with confidence
* pronouns resolve only when context supports one clear candidate
* ambiguous references remain unresolved candidates
* low-confidence matches do not silently merge entities
* surface references are tracked with evidence anchors
* cross-scene identity state can be carried forward
* cross-chapter identity state can be carried forward
* extraction remains separate from resolution
* canon updating remains the only system that accepts truth
* deterministic tests cover aliases, titles, descriptions, pronouns, ambiguity, and low-confidence candidates

---

# Presentation Acceptance

The workspace must avoid exposing raw machine identity artifacts as creator-facing output.

Accepted UI behavior:

* character sheets show canonical names, aliases, titles, descriptions, race, gender, status, relationships, and recent changes in human-readable language
* world sheets phrase relationships as readable statements
* timeline and continuity views group changes by chapter and scene
* unresolved or ambiguous identity references appear as reviewable uncertainty, not noisy machine IDs
* developer details remain hidden behind developer review surfaces

---

# Non-Goals

Phase 12 does not include:

* image generation
* video generation
* voice generation
* public translation marketplace features
* user-facing identity merge UI beyond simple review-ready output
* cross-project identity graphs
* broad frontend redesign
* replacing Canon with AI opinion

---

# Completion Rule

Phase 12 is complete only when backend gates, frontend gates, deterministic translation tests, deterministic entity-resolution tests, and a browser alpha pass all succeed.

V2 release-candidate readiness remains blocked until Phase 12 is accepted.

---

# Current Status

Status: **Acceptance pending hosted browser recheck after alpha-noise fixes**

Verified on July 13, 2026:

* Backend deterministic gates passed: `946 passed`
* Translation Foundation tests passed: `24 passed`
* Entity Resolution Foundation tests passed: `20 passed`
* Frontend lint passed
* Frontend tests passed: `160 passed`
* Frontend production build passed
* Hosted browser alpha sweep completed across Dashboard, Overview, Story, Import, Characters, World, Timeline, Scenes, Continuity, Prompt Packs, Exports, and Settings
* Browser sweep found two creator-facing presentation issues:
  * internal source-backed placeholder text leaked into character output
  * timeline and continuity summary labels lacked readable separators
* Branch fixes were implemented and verified locally with frontend lint, tests, and production build

Remaining before Phase 12 acceptance:

* Merge and deploy the alpha-noise fixes
* Recheck hosted Aevryn after deployment
* Confirm creator-facing views hide raw machine identity artifacts after deployment
* Confirm translation and entity-resolution metadata appear only as review-safe uncertainty after deployment

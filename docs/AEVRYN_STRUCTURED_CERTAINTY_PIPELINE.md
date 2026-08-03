# Aevryn Structured Certainty Pipeline

> Built by **Aetherra Labs**

This document defines the V2 architecture contract for how Aevryn turns source
story material into Canon-backed production context.

---

# Core Rule

```text
Every downstream system should receive more structured information than the
system before it.
```

Every stage reduces ambiguity when evidence allows it.

Every stage preserves uncertainty when evidence does not allow certainty.

No stage may pretend confidence simply because a later stage needs cleaner
output.

---

# Pipeline

```text
Story Import
-> Sentence Understanding
-> Translation / Normalization
-> Entity Extraction
-> Entity Resolution
-> Canon Updating / Canon
-> Scene, Character, World, Timeline, Continuity
-> Prompt Engine
```

The important identity boundary is:

```text
Extraction proposes.
Resolution consolidates.
Canon decides truth.
```

Entity Resolution may use early mention or sentence signals as hints, but full
canonical identity resolution happens after extraction proposes candidates.

---

# Stage Contracts

| Stage | Owns | Produces | Must Not Own | Uncertainty Output |
| --- | --- | --- | --- | --- |
| Story Import | Source intake and source order | Chapters, scenes, paragraphs, sentence evidence anchors | Meaning, Canon, AI interpretation | Missing or unsupported source structure |
| Sentence Understanding | Sentence-level meaning signals | Metadata-only signals, cue terms, ambiguity terms, review flags | Translation, extraction, Canon truth | Ambiguous terms, mixed item/skill/system cues |
| Translation / Normalization | Meaning-preserving language normalization | Normalized scene text linked to original evidence anchors | Canon truth, new story facts, ownership of source structure | Review issues tied to anchors |
| Entity Extraction | Evidence-bounded candidate discovery | Candidate entities, facts, relationships, state changes | Identity merging, Canon acceptance | Rejected or low-confidence candidates |
| Entity Resolution | Identity matching and stable surface references | Resolved, ambiguous, or unresolved identity decisions | Extraction, Canon truth, frontend presentation | Ambiguous or unresolved references |
| Canon Updating / Canon | Evidence-backed truth acceptance | Accepted facts, relationships, state changes, snapshots | Raw AI opinion, inferred missing facts | Rejected candidates and conflicts |
| Scene / Character / World / Timeline / Continuity | Read models over accepted Canon | Human-readable state, history, scene context, continuity deltas | Canon mutation, unsupported invention | Unknown fields and reviewable gaps |
| Prompt Engine | Production context from accepted story state | Canon-bound image, narration, camera, and animation prompts | Canon creation, hidden inference, image/video generation | Missing required visual/context details |

---

# Non-Negotiable Boundaries

## Metadata Does Not Become Truth

Sentence Understanding and Translation may create useful structured metadata.

That metadata is routing and review context. It is not Canon.

## Normalized Text Does Not Replace Evidence

Translation may provide normalized scene text to extraction.

Extracted candidates must still cite original source evidence anchors.

## AI Output Does Not Bypass Canon

Provider-backed extraction may propose candidates only.

Candidate output must pass validation, identity resolution, and Canon Updating
before it can appear as accepted project state.

## Resolution Does Not Invent Missing Identity

Entity Resolution may merge identities only when confidence is supported.

Low-confidence matches remain unresolved or ambiguous.

## Prompts Do Not Fill Gaps With Guesswork

Prompt Packs must use accepted Canon, scene analysis, and verified context.

If character appearance, location details, mood, or world state are unknown,
the prompt should expose that absence instead of inventing production details.

---

# Testing Expectations

V2 pipeline tests should prove:

* sentence-understanding metadata reaches extraction without duplicating full
  source prose through the metadata channel
* translation-normalized text remains linked to original evidence anchors
* extraction candidates cannot become Canon without Canon Updating
* entity resolution rewrites supported duplicate identities before Canon
  acceptance
* ambiguous identity matches remain reviewable instead of silently merging
* prompt output remains Canon-bound and exposes missing inputs
* logs and review metadata do not leak full source prose, full provider payloads,
  secrets, or private storage references

---

# Product Meaning

Aevryn is not valuable because it forwards story text to an AI model.

Aevryn is valuable because each stage creates a more reliable structure for the
next stage.

The Prompt Engine should receive production context, not a pile of prose.

The user should receive Canon-backed creative direction, not a confident guess.


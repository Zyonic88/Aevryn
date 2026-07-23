# AEVRYN PROMPTING PHILOSOPHY

> Built by **Aetherra Labs**

This document defines how Aevryn generates prompts.

It is not a prompt library.

It is the philosophy and architecture behind prompt generation.

---

# Purpose

Aevryn does not attempt to become the world's best prompt writer.

Instead, Aevryn attempts to become the world's best story understanding system.

The quality of a prompt is determined by the quality of the information behind it.

Prompt engineering is the final step.

Story understanding is everything before it.

---

# Core Philosophy

Traditional prompting follows this pattern:

```text
Story
-> AI Prompt
-> Image
```

Aevryn follows a different approach:

```text
Story
-> Evidence
-> Canon
-> Timeline
-> Character
-> World
-> Scene
-> Scene Analysis
-> Prompt
-> Image / Video / Audio
```

The prompt is not the product.

The prompt is the final presentation of structured understanding.

---

# Prompt Design Principle

A prompt should never attempt to compensate for poor understanding.

Better understanding creates better prompts.

Poor understanding cannot be fixed by adding more adjectives.

---

# Information Before Style

Facts come first.

Style comes second.

The prompt should always separate story facts, scene meaning, and style.

## Story Facts

Story facts answer:

* Who is present?
* Where are they?
* What equipment do they have?
* What injuries exist?
* What relationships matter?
* What objects are important?
* What is actually happening?

These come directly from Canon.

## Scene Meaning

Scene meaning answers:

* Why is this scene important?
* What is the conflict?
* What is the emotional tone?
* What changed?
* What should production focus on?

These come from Scene Analyzer.

## Style

Only after the scene is understood should Aevryn describe:

* Art style
* Rendering quality
* Lighting
* Camera
* Composition
* Color grading

Style enhances understanding.

Style never replaces understanding.

---

# Prompt Architecture

Every prompt should be built from structured sections rather than one large paragraph.

Recommended structure:

```text
Scene Summary
-> Characters
-> Environment
-> Important Objects
-> Current Canon State
-> Scene Purpose
-> Conflict
-> Mood
-> Composition
-> Lighting
-> Camera
-> Animation Notes
-> Narration Notes
-> Forbidden Elements
-> Rendering Style
```

Each section has one responsibility.

---

# Character Information

Character information should come from Character Engine.

Aevryn should not regenerate an entire character description every scene.

Instead:

* Character identity remains stable.
* Current state changes.
* Scene-relevant facts enter the prompt.
* Unknown details remain unknown.
* Known visual traits are listed explicitly.
* Missing visual traits are named as unspecified, not invented.

Example character prompt sections:

```text
Character
Charlotte

Current Equipment
Current Mood
Current Injury
Current Goal
Current Location
Relationship Context
```

This improves consistency across generated media.

For image, camera, and animation prompts, Aevryn should separate:

* known character appearance
* known race or species
* known gender
* known clothing or equipment
* known posture or expression
* unspecified visual traits

If Canon does not support a visual trait, the prompt should tell the generation
tool to keep that trait neutral. This avoids over-tightening extraction while
still preventing confident-looking hallucinations in generated media.

---

# Environment

Environment comes from World Engine through scene context.

It should include:

* Location
* Weather
* Time of day
* Damage
* Ownership
* Environmental conditions

Only information supported by Canon should appear.

---

# Scene Purpose

Every prompt should answer:

Why does this scene exist?

Example purposes:

* Character introduction
* Emotional confrontation
* Tactical planning
* Discovery
* Combat
* Escape
* Celebration
* Revelation

Purpose helps production determine emphasis.

---

# Conflict

Conflict is independent from mood.

Examples:

* Internal conflict
* Character conflict
* Tactical conflict
* Resource conflict
* Environmental conflict

Conflict should come from Scene Analyzer.

---

# Mood

Mood should describe emotional atmosphere.

Examples:

* Hopeful
* Tense
* Suspenseful
* Desperate
* Peaceful
* Triumphant

Mood influences presentation.

It never changes Canon.

---

# Composition

Composition should describe visual arrangement.

Examples:

* Wide establishing shot
* Medium dialogue shot
* Close-up
* Over-the-shoulder
* Character-centered
* Environmental focus

Composition exists separately from camera.

---

# Camera

Camera describes cinematography.

Examples:

* Eye level
* Low angle
* High angle
* Tracking shot
* Static shot
* 35mm lens
* 85mm portrait

Camera should remain independent from composition.

---

# Lighting

Lighting should describe physical light.

Examples:

* Dawn
* Golden hour
* Overcast
* Moonlight
* Torchlight
* Volumetric fog

Lighting should never redefine mood.

---

# Important Objects

Objects that matter to the scene should be explicitly listed.

Examples:

* Fleet blueprint
* Ancient sword
* Broken crown
* Medical scanner

Objects should never be buried inside paragraphs.

---

# Relationships

Relevant relationships should be included when they affect the scene.

Examples:

* Allies
* Rivals
* Parent
* Commander
* Student

Relationship context helps pose characters correctly.

---

# Forbidden Elements

Every prompt should explicitly state what must not appear.

Examples:

* No additional characters
* No incorrect uniforms
* No futuristic buildings
* No duplicate weapons
* No smiling
* No text
* No watermark

Negative guidance reduces ambiguity.

---

# Visible Text

Prompt metadata should not become generated image text.

Aevryn may include character names, departments, goals, roles, scene IDs, or object names in a prompt so the generation model understands the scene.

That does not mean those labels should appear inside the generated image.

Image, camera, and animation prompts should explicitly prevent:

* character names rendered as name tags
* entity IDs rendered as visible text
* scene titles rendered as captions
* prompt headings rendered as UI panels
* Canon attributes rendered as clothing text, wall signs, badges, or hologram labels
* readable screen, book, interface, or blueprint text unless exact visible text is accepted Canon

If a screen, sign, book, interface, or blueprint is Canon, the object may be shown visually.

Readable text on that object requires explicit Canon support.

---

# Style

Style should remain independent from story facts.

Examples:

* Semi-realistic
* Painterly
* Anime
* Cinematic
* Stylized
* Photorealistic

Style should never overwrite Canon.

---

# Prompt Variants

Different production targets consume different prompt variants.

## Image

Focus:

* Visual accuracy
* Composition
* Character placement
* Environment
* Important objects
* Forbidden elements

## Video

Focus:

* Motion
* Camera
* Transitions
* Continuity

## Narration

Focus:

* Speech
* Emotion
* Pacing

## Storyboard

Focus:

* Blocking
* Shot planning
* Composition

## Audiobook

Focus:

* Voice
* Pronunciation
* Emotion
* Dialogue assignment

Every variant consumes the same underlying understanding.

---

# Character Persistence

Aevryn should prioritize persistent character identity.

The engine should know:

```text
Charlotte
-> Canonical Character
-> Current State
```

Instead of rebuilding Charlotte from scratch every scene.

Identity remains stable.

State changes.

---

# Translation

Prompt generation should consume normalized story understanding rather than raw translated text.

Translation exists to improve Canon accuracy.

Prompt generation exists to communicate Canon.

These are separate responsibilities.

---

# Entity Resolution

Prompt generation should consume resolved identities.

Aliases, titles, pronouns, and descriptive references should already point to the correct canonical entity before prompt construction begins.

Prompt generation should never perform identity resolution.

---

# Canon Rule

The Prompt Engine never invents.

If Canon cannot support a detail, the detail remains Unknown.

Unknown information is never replaced by assumptions.

---

# Determinism

Given:

* The same Canon
* The same Timeline
* The same Scene
* The same Scene Analysis
* The same Prompt Profile

Aevryn should generate identical prompts.

Prompt generation must remain deterministic.

---

# Core Principle

Aevryn does not generate prompts because it understands prompting.

Aevryn generates prompts because it understands stories.

Prompt quality is a direct consequence of story understanding.

The better Aevryn understands the story, the better every downstream production system becomes.

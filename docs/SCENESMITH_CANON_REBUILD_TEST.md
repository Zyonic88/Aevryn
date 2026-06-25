# SceneSmith Canon Rebuild Test

> Built by **Aetherra Labs**

The Canon Rebuild Test is SceneSmith's permanent validation process for deterministic continuity behavior.

It asks one question:

Can SceneSmith rebuild the same story from an empty project and produce identical outputs?

---

# Purpose

The Canon Rebuild Test proves that SceneSmith's architecture is deterministic.

It does not test whether an AI model is creative.

It tests whether SceneSmith can prove and reproduce its own canon state.

---

# Test 1: Deterministic Rebuild

Process:

```text
Empty Project
-> Import Chapter 1
-> Import Chapter 2
-> Import Chapter 3
-> Import Chapter 4
-> Generate Character Cards
-> Generate World Sheets
-> Generate Scene Sheets
-> Generate Continuity Report
-> Generate Prompt Packs
-> Save Outputs
-> Delete Project
-> Repeat
-> Byte Compare
```

Pass rule:

Both runs must produce identical output bytes.

SceneSmith must also compare:

* Character count
* Fact count
* Relationship count
* State-change count
* Evidence count
* Prompt count
* Continuity report counts
* Warnings
* Errors

If output bytes or counts differ, the test fails.

---

# Test 2: Incremental Test

Process:

```text
Import Chapter 1
-> Stop
-> Import Chapter 2
-> Stop
-> Import Chapter 3
-> Stop
-> Import Chapter 4
```

Pass rule:

The final outputs must match the Deterministic Rebuild outputs.

This proves that resume-style creator workflows do not drift from full rebuild workflows.

---

# Test 3: Out-of-Order Protection Test

Process:

```text
Import Chapter 3
-> Import Chapter 1
-> Import Chapter 2
```

Pass rule:

SceneSmith must reject the import order or explicitly rebuild.

SceneSmith must not guess.

SceneSmith must not silently reorder.

---

# Test 4: Canon Stability Test

Process:

```text
Import Chapter 1
-> Import Chapter 2
-> ...
-> Import Chapter N
-> Generate Character Card
-> Delete Project
-> Repeat
```

Pass rule:

The final canon outputs must match exactly.

If the same source material produces different character cards, world sheets, scene sheets, prompt packs, or continuity reports, SceneSmith has found a determinism bug.

---

# Versioned Validation Ladder

SceneSmith validation tests are versioned:

1. Deterministic Import
2. Deterministic Canon
3. Deterministic Character
4. Deterministic World
5. Deterministic Scene
6. Deterministic Prompt
7. Deterministic Presentation
8. Integration: Canon Rebuild
9. Integration: Full Novel

Each level must remain deterministic before SceneSmith moves to larger stories.

---

# V1 Rule

The Canon Rebuild Test is part of V1 readiness.

AI may improve over time.

SceneSmith's evidence, canon, timeline, and presentation behavior must remain stable for the same accepted candidates.

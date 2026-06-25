# SceneSmith Development Rules

Every line of code must be written as if another professional engineer will inherit the project tomorrow.

## 1. Architecture Before Code

Never write code until the architecture for that subsystem is understood.

If we cannot explain:

* What it does
* Why it exists
* What authority it owns
* What it does not own
* How it fails
* How it interacts with other systems

then we do not write code.

## 2. Single Responsibility

Every class.

Every module.

Every function.

One job.

If something starts doing multiple unrelated things, split it.

## 3. Readability Over Cleverness

No clever code.

No one-line magic.

Future us should immediately understand:

```python
def update_character_weapon(...):
```

instead of:

```python
def upd(...):
```

or giant anonymous lambdas.

## 4. Documentation First

Every subsystem gets documentation before implementation.

Every system document must answer:

* What is it?
* Why does it exist?
* What authority does it own?
* What does it NOT own?
* How does it fail?
* How does it interact with other systems?

## 5. Type Hints Everywhere

Python should look like modern Python.

```python
def extract_characters(
    chapter: StoryChapter,
) -> list[Character]:
```

Not:

```python
def extract(ch):
```

## 6. Comprehensive Docstrings

Every public function.

Every class.

Explain:

* Purpose
* Parameters
* Return values
* Exceptions

## 7. Tests Are Required

No subsystem is complete until it has tests.

Not optional.

## 8. Logging

No random print statements.

Everything meaningful uses structured logging.

## 9. Never Duplicate Logic

If we are copying code, we are probably designing something incorrectly.

## 10. Evidence Over Assumption

This should become SceneSmith's defining philosophy.

If the story does not explicitly say:

Hair Color

Then:

Unknown

Never hallucinate.

Every extracted fact should have:

* Confidence
* Chapter
* Evidence

## 11. No Technical Debt "For Later"

If something feels wrong, fix it while it is still small.

Do not build a mountain of TODOs.

## 12. Git Discipline

Every commit should represent one meaningful change.

Examples:

```text
feat(character): add appearance extraction
fix(canon): preserve equipment state after upgrades
test(world): validate location state transitions
```

## 13. Repository Discipline

Git contains:

* Source
* Docs
* Tests
* Configs

Git never contains:

* Builds
* Cache
* Runtime
* Generated output
* Dependencies
* Temporary files

## 14. Understanding Rule

Before a subsystem is considered complete, we must be able to explain:

* What it does
* Why it exists
* What authority it owns
* What authority it does NOT own
* How it fails
* How it interacts with the rest of SceneSmith

without reading the code.

## 15. The User Comes First

Every feature must answer:

Does this make creating a story recap easier?

If the answer is "no," it probably does not belong in Version 1.

## 16. The 2-Year Rule

Every time we write code, ask:

If we come back to this in two years, will we immediately understand it?

If the answer is "probably not," rewrite it.

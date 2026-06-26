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

## 2. Authority Is Sacred

Every system owns exactly one responsibility.

If another system needs that responsibility, it asks the owning system.

Never duplicate authority.

Examples:

* Prompt Engine wants character information? It asks Character Engine.
* Character Engine wants timeline position? It asks Timeline Engine.
* Timeline Engine wants canon state? It asks Canon Engine.
* Canon Engine wants source proof? It uses Story Import evidence anchors.

No shortcuts.

## 3. The AI Never Owns Truth

The AI owns extraction.

The Canon owns truth.

AI may propose facts.

AI may extract evidence.

AI may suggest relationships.

AI may identify possible state changes.

But AI never becomes the source of truth.

Only the Canon Engine stores canonical truth, and only when the fact is evidence-backed.

This distinction is what makes SceneSmith a trusted production tool instead of just another AI app.

## 4. Single Responsibility

Every class.

Every module.

Every function.

One job.

If something starts doing multiple unrelated things, split it.

## 5. Readability Over Cleverness

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

## 6. Documentation First

Every subsystem gets documentation before implementation.

Every system document must answer:

* What is it?
* Why does it exist?
* What authority does it own?
* What does it NOT own?
* How does it fail?
* How does it interact with other systems?

## 7. Type Hints Everywhere

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

## 8. Comprehensive Docstrings

Every public function.

Every class.

Explain:

* Purpose
* Parameters
* Return values
* Exceptions

## 9. Tests Are Required

No subsystem is complete until it has tests.

Not optional.

## 10. Logging

No random print statements.

Everything meaningful uses structured logging.

## 11. Never Duplicate Logic

If we are copying code, we are probably designing something incorrectly.

## 12. Evidence Over Assumption

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

## 13. No Technical Debt "For Later"

If something feels wrong, fix it while it is still small.

Do not build a mountain of TODOs.

## 14. Git Discipline

Every commit should represent one meaningful change.

Examples:

```text
feat(character): add appearance extraction
fix(canon): preserve equipment state after upgrades
test(world): validate location state transitions
```

## 15. Repository Discipline

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

## 16. Understanding Rule

Before a subsystem is considered complete, we must be able to explain:

* What it does
* Why it exists
* What authority it owns
* What authority it does NOT own
* How it fails
* How it interacts with the rest of SceneSmith

without reading the code.

## 17. The User Comes First

Every feature must answer:

Does this make creating a story recap easier?

If the answer is "no," it probably does not belong in Version 1.

## 18. The 2-Year Rule

Every time we write code, ask:

If we come back to this in two years, will we immediately understand it?

If the answer is "probably not," rewrite it.

## 19. V1 Feature Freeze

From this point until Version 1 is released:

* No new core systems
* No new architecture
* No major redesigns

Allowed work:

* Bug fixes
* Performance improvements
* UX improvements
* Testing
* Documentation

The goal is confidence, not more scope.

SceneSmith V1 is now moving toward Release Candidate 1.

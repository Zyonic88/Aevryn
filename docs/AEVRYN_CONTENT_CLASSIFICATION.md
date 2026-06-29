# Aevryn Content Classification

> Built by **Aetherra Labs**

Aevryn is content-aware, not content-opinionated.

The platform helps creators understand their own stories. Classification exists to make the product safer, clearer, and more predictable; it does not exist to judge lawful fiction.

---

# Core Rule

```text
Aevryn may classify content for handling.
Aevryn does not claim ownership or moral authority over user stories.
```

---

# Project Ratings

Aevryn should support project-level content ratings.

## General

Suitable for broad audiences.

May include:

* mild conflict
* non-graphic peril
* ordinary romance
* light language

## Teen

Suitable for teen-oriented stories.

May include:

* stronger conflict
* moderate violence
* implied intimacy
* moderate language
* emotionally intense themes

## Mature

For adult-oriented stories.

May include:

* mature themes
* stronger violence
* non-explicit sexual content
* trauma, addiction, or psychological distress
* stronger language

## Explicit

For stories with explicit adult material or graphic content.

May include:

* explicit sexual content
* graphic violence
* extreme horror
* intense mature themes

Explicit classification must inform UI and generation behavior, but lawful user-owned fiction is not automatically banned because it is mature.

---

# UI Behavior

The UI should eventually:

* show the project rating in settings
* warn before opening explicit projects in shared environments
* allow users to filter or label exports by rating
* avoid surprising previews for mature or explicit content
* keep classification metadata separate from source prose

---

# Generation Module Behavior

Aevryn V2 does not generate images, video, voice, music, or chatbot output.

Future generation modules must respect project ratings and provider safety rules.

Generation modules should:

* use classification metadata when choosing prompt constraints
* avoid sending disallowed content to providers
* explain provider refusals without exposing source prose
* preserve user ownership of generated assets

---

# Export Considerations

Exports should be able to include rating metadata when useful for production workflows.

Exports must not silently strip or rewrite user-owned story content because of rating alone.

---

# Future Moderation

Future moderation work should focus on:

* legal compliance
* platform abuse prevention
* provider policy compatibility
* user controls
* clear appeals or correction paths where moderation affects access

Moderation must never become hidden training, hidden ownership, or hidden surveillance.

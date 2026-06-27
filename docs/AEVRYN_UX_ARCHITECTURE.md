# Aevryn UX Architecture

> Built by **Aetherra Labs**

This document defines the workspace-first user experience architecture for Aevryn.

It complements `docs/AEVRYN_WEBSITE.md`.

The Website document defines the frontend boundary.

This document defines how Aevryn should feel to use.

---

# Core UX Principle

Aevryn is a professional story-continuity workspace.

It should feel closer to a focused creative IDE than a marketing website.

Reference products:

* VS Code
* JetBrains Rider
* Obsidian
* Figma
* Linear

These products are useful references because they solve dense professional workflows with stable navigation, predictable panels, and fast context switching.

---

# UX Order Of Operations

Frontend work must happen in this order:

1. UX architecture
2. Low-fidelity wireframes
3. Interaction model
4. Navigation model
5. High-fidelity mockups
6. Branding
7. Motion and polish

Do not begin with colors, gradients, icons, or animations.

First decide where each workspace responsibility belongs.

---

# One Screen, One Question

Every Aevryn screen should answer one primary question.

If a screen answers more than one primary question, it is probably too busy.

Primary screen questions:

* Dashboard: What projects do I have?
* Story: What chapters exist?
* Character: Who is this person?
* Scene: What is true here?
* Timeline: What happened when?
* World: What exists in this world?
* Continuity: What changed?
* Prompt Pack: What do I generate?
* Export: What portable output do I need?
* Settings: How is this project configured?

Secondary metadata can exist, but it must not compete with the primary question.

---

# Workspace-First Design

The Project Workspace is the most important product surface.

Creators will spend most of their time inside a project, not on login or dashboard screens.

Therefore:

* Design the Project Workspace first.
* Design login and dashboard after the workspace architecture is stable.
* Treat output views as workspace tools, not standalone landing pages.
* Keep the workspace dense enough for repeated use.
* Keep view models readable enough for fast scanning.

---

# Current Phase 5 Cross-Reference

Phase 5 already has:

* Login screen
* Register screen
* Dashboard
* Project workspace shell
* Sidebar navigation
* Direct workspace tab URLs
* Overview tab
* Import view
* Character view
* World view
* Timeline view
* Scene view
* Continuity view
* Prompt Pack view
* Export request view
* Loading, empty, and error states
* API-backed response validation
* Stale result and stale error clearing

Phase 5 does not yet have:

* Formal low-fidelity workspace wireframes
* A dedicated Story view
* A dedicated Settings view
* Pinned tabs
* Split panes
* Drag-reorderable tabs
* Reopenable closed tabs
* Global search
* Local workspace search
* Command palette
* Inspector/info panel
* Bottom panel for validation, logs, queue, and output
* Locked future-module surfaces for Images and Video
* High-fidelity dark theme
* Branding pass
* Motion or animation pass

Everything in the second list is optional until it is promoted into a scoped phase.

---

# Low-Fidelity Workspace Target

The first UX target should be a black-and-white wireframe.

No color.

No branding.

No icons unless they clarify layout ownership.

Initial workspace structure:

```text
+--------------------------------------------------------------------------+
| Aevryn                                            Project: Project Name   |
+--------------+-----------------------------------------------------------+
|              | Story | Character | Timeline | Scene | Prompt | World | + |
| Story        +-----------------------------------------------------------+
| Characters   |                                             |             |
| World        |                                             | Info Panel  |
| Timeline     |                Main Workspace               |             |
| Scenes       |                                             |             |
| Continuity   |                                             |             |
| Prompt Packs |                                             |             |
| Exports      |                                             |             |
| Settings     |                                             |             |
+--------------+---------------------------------------------+-------------+
| Images LOCK  | Validation | Logs | Queue | Output                         |
| Video LOCK   +------------------------------------------------------------+
+--------------------------------------------------------------------------+
```

This wireframe is a target, not a current implementation.

The current Phase 5 implementation has the left workspace navigation and main workspace content. It does not yet have top document tabs, right info panel, bottom utility panel, locked future-module rail, or Settings.

---

# Workspace Regions

## Top Bar

Purpose:

* Identify Aevryn
* Show the active project
* Provide account/session controls

Current status:

* Implemented as a global app topbar.

Future hardening:

* Clarify whether project identity belongs in global topbar, workspace sidebar, or both.

## Left Sidebar

Purpose:

* Stable workspace navigation
* Long-lived project sections

Required sections:

* Story
* Characters
* World
* Timeline
* Scenes
* Continuity
* Prompt Packs
* Exports
* Settings

Current status:

* Implemented for Overview, Import, Characters, World, Timeline, Scenes, Continuity, Prompt Packs, and Exports.

Future hardening:

* Decide whether Import becomes Story or remains separate.
* Add Settings when there is a project-settings API-backed surface.

## Top Document Tabs

Purpose:

* Fast switching between open working contexts.
* IDE-like navigation within the project.

Examples:

* Character: Mark
* Scene: Chapter 4 Scene 2
* Prompt: Scene 4
* Timeline

Current status:

* Not implemented.

Future hardening:

* Define whether tabs can pin, close, reorder, split, or restore.

## Main Workspace

Purpose:

* Answer the active screen's primary question.
* Render API view models.
* Own form interaction and request state.

Current status:

* Implemented for Phase 5B output previews.

Future hardening:

* Replace preview/dev forms with project-storage-backed workflows after Phase 6 storage exists.

## Right Info Panel

Purpose:

* Show metadata, evidence anchors, selected item details, warnings, and context without crowding the main workspace.

Current status:

* Not implemented.

Future hardening:

* Use for evidence details only through API-provided contracts.
* Do not reconstruct canon or timeline state in the panel.

## Bottom Utility Panel

Purpose:

* Validation
* Logs
* Queue
* Output

Current status:

* Not implemented.

Future hardening:

* Depends on project storage, background workers, monitoring, and queue visibility.

## Locked Future Modules

Purpose:

* Show future product direction without enabling out-of-scope V2 media generation.

Examples:

* Images LOCKED
* Video LOCKED

Current status:

* Not implemented.

Future hardening:

* Optional. Must not imply V2 supports image or video generation.

---

# Interaction Model Questions

Before high-fidelity design, answer these:

* Can workspace tabs be closed?
* Can workspace tabs be pinned?
* Can workspace tabs be reordered?
* Can workspace tabs split vertically or horizontally?
* Can a closed tab be reopened?
* Does browser history follow tab changes?
* Does project navigation open a new tab or replace the current tab?
* What is the default tab for a project?
* Where do validation errors appear?
* Where do long-running job states appear?
* How does the user return from Character to Scene to Prompt?
* Does search open a result in the current workspace or a new tab?

Do not implement these by default.

Promote each behavior only when it removes real workflow friction.

---

# Navigation Model

Minimum navigation paths:

```text
Dashboard
-> Project Workspace
-> Story
-> Scene
-> Character
-> Continuity
-> Prompt Pack
-> Export
```

Fast navigation targets:

* Project search
* Character search
* Scene search
* Evidence anchor search
* Command palette

Current status:

* Direct workspace tab URLs exist.
* Sidebar navigation exists.
* Search does not exist.

Future hardening:

* Add search after project storage gives the frontend durable project data to search through an API.

---

# Implementation Boundary

UX architecture must not weaken Aevryn authority boundaries.

The frontend may:

* Own navigation state.
* Own panel state.
* Own tab state.
* Render API view models.
* Show API errors.
* Submit user input to API routes.

The frontend may not:

* Decide canon truth.
* Parse source stories.
* Build timeline state.
* Build continuity state.
* Generate prompt text.
* Serialize exports.
* Reconstruct presentation view models from raw engine data.

---

# Recommended Next UX Work

Before adding visual polish, create low-fidelity wireframes for:

1. Login
2. Dashboard
3. Project Workspace
4. Story View
5. Character View
6. Scene View
7. Timeline View
8. World View
9. Continuity View
10. Prompt Pack View
11. Export View
12. Settings View

The Project Workspace wireframe should come first.

Only after these layouts are accepted should Aevryn move into:

* dark theme
* Aevryn colors
* iconography
* typography
* motion
* branding polish

---

# Phase Relationship

Phase 5B implemented the API-backed output views.

Phase 6 is Project Storage.

The UX architecture in this document should guide future frontend work, but Phase 6 should still prioritize durable project data over visual polish.

The practical next sequence is:

1. Phase 6 Project Storage planning and acceptance criteria.
2. Storage-backed project workflows.
3. Replace preview-only workspace flows with saved project flows.
4. Low-fidelity workspace wireframes for the storage-backed experience.
5. High-fidelity visual design.

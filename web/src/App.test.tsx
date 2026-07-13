import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { API_PATHS } from "./api/client";
import { MAX_IMPORT_SOURCE_CHARACTERS } from "./importing/importPayload";

const session = {
  user_id: "user_demo",
  email: "demo@example.com",
  display_name: "Demo User",
  session_token: "session-token",
  expires_at: "2999-06-27T00:00:00.000Z",
};

const healthPayload = {
  status: "ok",
  api_version: "v2",
  engine: "Aevryn",
  storage: {
    project_storage: "configured",
    import_content_storage: "configured",
  },
};

const capabilitiesPayload = {
  api_version: "v2",
  engine: "Aevryn",
  phase: "v2_phase_5_web_shell",
  routes: [
    { method: "GET", path: API_PATHS.health, purpose: "Health" },
    { method: "POST", path: API_PATHS.authLogin, purpose: "Login" },
  ],
  source_formats: { supported: [], deferred: [] },
  export_capabilities: [],
  platform_limits: [],
};
const sourceFormatsPayload = {
  supported: [
    {
      extension: ".txt",
      status: "supported",
      adapter: "SourceFileTextExtractor",
      evidence_anchor_status: "supported",
      notes: "Read as UTF-8 text and passed directly to Story Import.",
    },
    {
      extension: ".md/.markdown",
      status: "supported",
      adapter: "SourceFileTextExtractor",
      evidence_anchor_status: "supported",
      notes: "Read as UTF-8 text; Markdown markers remain source text.",
    },
    {
      extension: ".html/.htm/.xhtml",
      status: "supported",
      adapter: "SourceFileTextExtractor",
      evidence_anchor_status: "supported",
      notes: "Extracts visible text and skips script, style, and navigation.",
    },
    {
      extension: ".fb2",
      status: "supported",
      adapter: "SourceFileTextExtractor",
      evidence_anchor_status: "supported",
      notes: "Extracts paragraph-like XML text.",
    },
    {
      extension: ".docx",
      status: "supported",
      adapter: "SourceFileTextExtractor",
      evidence_anchor_status: "supported",
      notes: "Extracts paragraph text from word/document.xml.",
    },
    {
      extension: ".odt",
      status: "supported",
      adapter: "SourceFileTextExtractor",
      evidence_anchor_status: "supported",
      notes: "Extracts heading and paragraph text from content.xml.",
    },
    {
      extension: ".epub",
      status: "supported",
      adapter: "EpubTextExtractor",
      evidence_anchor_status: "supported",
      notes: "Extracts readable spine content and skips navigation material.",
    },
  ],
  deferred: [
    {
      extension: ".pdf",
      status: "deferred",
      adapter: "none",
      evidence_anchor_status: "not_enabled",
      notes: "Requires deterministic PDF reading-order parser support.",
    },
    {
      extension: ".mobi",
      status: "deferred",
      adapter: "none",
      evidence_anchor_status: "not_enabled",
      notes: "Requires dedicated Kindle parser support.",
    },
    {
      extension: ".azw3",
      status: "deferred",
      adapter: "none",
      evidence_anchor_status: "not_enabled",
      notes: "Requires dedicated Kindle parser support.",
    },
  ],
};

function isImportRunSubmitPath(url: string, projectId: string, storyId: string): boolean {
  const importRunsPrefix = `${API_PATHS.projects}/${projectId}/stories/${storyId}/imports/`;
  return url.includes(importRunsPrefix) && url.endsWith("/runs");
}

function importIdFromRunSubmitPath(url: string): string {
  const match = /\/imports\/([^/]+)\/runs$/u.exec(url);
  return match ? decodeURIComponent(match[1]) : importRecordPayload.import_id;
}

const importInspectPayload = {
  source_id: "source_alpha",
  source_format: "txt",
  title: "Alpha",
  chapters: 1,
  chapter_ids: ["source_alpha_chapter_001"],
  scenes: 8,
  scene_ids: Array.from(
    { length: 8 },
    (_, index) => `source_alpha_chapter_${String(index + 1).padStart(3, "0")}_scene_001`,
  ),
  scene_map: Array.from({ length: 8 }, (_, index) => ({
    chapter_id: `source_alpha_chapter_${String(index + 1).padStart(3, "0")}`,
    chapter_index: index + 1,
    scene_id: `source_alpha_chapter_${String(index + 1).padStart(3, "0")}_scene_001`,
    scene_index: 1,
    title: `Scene ${index + 1}`,
  })),
  paragraphs: 1,
  evidence_anchors: 1,
  first_evidence_anchors: [
    {
      anchor_id: "source_alpha_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
      chapter_id: "source_alpha_chapter_001",
      scene_id: "source_alpha_chapter_001_scene_001",
      paragraph_index: 1,
      sentence_index: 1,
    },
  ],
};
const worldPreviewPayload = {
  source_id: "source_alpha",
  source_format: "txt",
  scene_id: "source_alpha_chapter_002_scene_001",
  world_sheet: {
    chapter_label: "Chapter 2",
    entity_sections: [
      {
        title: "Hangar (location)",
        items: ["condition: Alarm active", "ownership: Academy", "owner: Zhao Chen's starship"],
      },
    ],
    evidence_summary: "2 verified world facts",
  },
};

const timelinePreviewPayload = {
  source_id: "source_alpha",
  source_format: "txt",
  current_scene_id: "source_alpha_chapter_002_scene_001",
  chapter_ids: ["source_alpha_chapter_001", "source_alpha_chapter_002"],
  scene_map: [
    {
      chapter_id: "source_alpha_chapter_001",
      chapter_index: 1,
      scene_id: "source_alpha_chapter_001_scene_001",
      scene_index: 1,
      title: "Scene 1",
    },
    {
      chapter_id: "source_alpha_chapter_002",
      chapter_index: 2,
      scene_id: "source_alpha_chapter_002_scene_001",
      scene_index: 1,
      title: "Scene 1",
    },
  ],
  accepted_state_change_ids: ["state_fact_character_mark_current_weapon_iron_sword"],
};

const scenePreviewPayload = {
  source_id: "source_alpha",
  source_format: "txt",
  scene_id: "source_alpha_chapter_001_scene_001",
  scene_sheet: {
    scene_id: "source_alpha_chapter_001_scene_001",
    title: "Scene 7",
    chapter_label: "Chapter 1",
    location: { title: "Location", items: ["Hangar"] },
    characters_present: { title: "Characters Present", items: ["Mark"] },
    mood: { title: "Mood", items: ["Tense"] },
    purpose: { title: "Purpose", items: ["Establish current state."] },
    visual_highlights: { title: "Visual Highlights", items: ["Rusty Dagger"] },
    continuity_changes: { title: "Continuity Changes", items: ["Mark equipped Rusty Dagger"] },
    environment: { title: "Environment", items: ["Quiet hangar"] },
    evidence_summary: "1 verified evidence reference",
  },
};

const promptPreviewPayload = {
  source_id: "source_alpha",
  source_format: "txt",
  scene_id: "source_alpha_chapter_001_scene_001",
  production_pack: {
    scene: scenePreviewPayload.scene_sheet,
    image_prompt: {
      title: "Image Prompt",
      items: [
        "Generate this image using only accepted Aevryn canon.",
        "Scene Summary: Mark prepares in the hangar.",
      ],
    },
    narration_prompt: {
      title: "Narration Prompt",
      items: ["Narrate using only accepted canon facts."],
    },
    camera_prompt: {
      title: "Camera Prompt",
      items: ["Describe camera framing without inventing new canon."],
    },
    animation_prompt: {
      title: "Animation Prompt",
      items: ["Describe motion using only accepted scene facts."],
    },
  },
};

const exportPreviewPayload = {
  source_id: "source_alpha",
  source_format: "txt",
  scene_id: "source_alpha_chapter_001_scene_001",
  export_kind: "production_pack",
  export_format: "markdown",
  filename: "source_alpha_production_pack.md",
  content_type: "text/markdown; charset=utf-8",
  content: "# Scene 7\n\n## Image Prompt\nGenerate this image using only accepted Aevryn canon.",
};

const continuityPreviewPayload = {
  source_id: "source_alpha",
  source_format: "txt",
  continuity_report: {
    source_id: "source_alpha",
    scenes: [
      {
        scene_id: "source_alpha_chapter_001_scene_001",
        new: [
          {
            record_id: "fact_character_mark_current_weapon_rusty_dagger",
            record_type: "fact",
            description: "character_mark current_weapon = Rusty Dagger.",
            evidence_id: "source_alpha_anchor_001",
            chapter_id: "source_alpha_chapter_001",
            scene_id: "source_alpha_chapter_001_scene_001",
          },
        ],
        updated: [],
        still_known: [],
        invalidated: [],
      },
      {
        scene_id: "source_alpha_chapter_002_scene_001",
        new: [],
        updated: [
          {
            record_id: "fact_character_mark_current_weapon_iron_sword",
            record_type: "fact",
            description: "character_mark current_weapon = Iron Sword.",
            evidence_id: "source_alpha_anchor_002",
            chapter_id: "source_alpha_chapter_002",
            scene_id: "source_alpha_chapter_002_scene_001",
          },
        ],
        still_known: [
          {
            record_id: "fact_character_mark_relationship_luna_ally",
            record_type: "fact",
            description: "character_mark relationship = Luna - Ally.",
            evidence_id: "source_alpha_anchor_003",
            chapter_id: "source_alpha_chapter_002",
            scene_id: "source_alpha_chapter_002_scene_001",
          },
        ],
        invalidated: [
          {
            record_id: "fact_character_mark_current_weapon_rusty_dagger_invalidated",
            record_type: "fact",
            description: "character_mark current_weapon = Rusty Dagger.",
            evidence_id: "source_alpha_anchor_001",
            chapter_id: "source_alpha_chapter_001",
            scene_id: "source_alpha_chapter_001_scene_001",
          },
        ],
      },
    ],
  },
};

const characterPreviewPayload = {
  source_id: "source_alpha",
  source_format: "txt",
  scene_id: "source_alpha_chapter_001_scene_001",
  character_profiles: [
    {
      character_id: "character_mark",
      display_name: "Mark",
      subtitle: "Known character",
      aliases: { title: "Aliases", items: ["Captain Mark"] },
      titles: { title: "Titles", items: ["Captain"] },
      descriptions: { title: "Descriptions", items: ["human male captain"] },
      race: { title: "Race", items: ["Human"] },
      gender: { title: "Gender", items: ["Male"] },
      status: { title: "Status", items: ["Alive"] },
      current_goal: { title: "Current Goal", items: ["Find the fortress"] },
      current_equipment: { title: "Current Equipment", items: ["Rusty Dagger"] },
      current_abilities: { title: "Current Abilities", items: ["Tracking"] },
      current_assets: { title: "Current Assets", items: [] },
      territory: { title: "Territory", items: [] },
      relationships: { title: "Relationships", items: ["Luna - Ally"] },
      current_limitations: { title: "Current Limitations", items: ["Injured arm"] },
      recent_changes: {
        title: "Recent Changes",
        items: ["display_name -> Mark", "race -> Human", "gender -> Male", "Equipped Rusty Dagger"],
      },
      evidence_summary: "3 verified facts",
    },
  ],
};

const projectAlpha = {
  id: "project_alpha",
  name: "Alpha",
  updatedAt: "2026-06-27T00:00:00.000Z",
};
const projectAlphaPayload = {
  project_id: projectAlpha.id,
  name: projectAlpha.name,
  created_at: projectAlpha.updatedAt,
  updated_at: projectAlpha.updatedAt,
};
const projectBetaPayload = {
  project_id: "project_beta",
  name: "Beta",
  created_at: "2026-06-28T00:00:00.000Z",
  updated_at: "2026-06-30T00:00:00.000Z",
};
const projectSettingsPayload = {
  project_id: projectAlpha.id,
  default_export_format: "markdown",
  locale: "en-US",
};
const storyAlphaPayload = {
  story_id: "story_alpha",
  project_id: projectAlpha.id,
  title: "Alpha Story",
  created_at: projectAlpha.updatedAt,
  updated_at: projectAlpha.updatedAt,
};
const importRecordPayload = {
  import_id: "import_alpha",
  story_id: storyAlphaPayload.story_id,
  source_id: "source_alpha",
  filename: "chapter_001.txt",
  source_format: "txt",
  storage_ref: "api_import://story_alpha/import_alpha",
  chapter_count: 1,
  scene_count: 8,
  evidence_anchor_count: 1,
  created_at: projectAlpha.updatedAt,
};
const engineRunPayload = {
  run_id: "run_alpha",
  project_id: projectAlpha.id,
  story_id: storyAlphaPayload.story_id,
  import_id: importRecordPayload.import_id,
  status: "pending",
  engine_version: "aevryn_v1",
  started_at: projectAlpha.updatedAt,
  status_updated_at: projectAlpha.updatedAt,
  finished_at: null,
  error_summary: "",
  job_ref: "queue://job_alpha",
};
const snapshotPayload = {
  snapshot_id: "snapshot_run_alpha_canon",
  project_id: projectAlpha.id,
  story_id: storyAlphaPayload.story_id,
  run_id: engineRunPayload.run_id,
  snapshot_kind: "canon",
  content_type: "application/json",
  serialized_output: '{"source_id":"source_alpha"}',
  created_at: projectAlpha.updatedAt,
};
const projectStatusPayload = {
  project_id: projectAlpha.id,
  status: "succeeded",
  story_count: 1,
  import_count: 1,
  run_count: 1,
  latest_import: {
    import_id: importRecordPayload.import_id,
    story_id: storyAlphaPayload.story_id,
    filename: importRecordPayload.filename,
    source_format: importRecordPayload.source_format,
    created_at: importRecordPayload.created_at,
  },
  latest_engine_run: {
    run_id: engineRunPayload.run_id,
    story_id: storyAlphaPayload.story_id,
    import_id: importRecordPayload.import_id,
    status: "succeeded",
    started_at: engineRunPayload.started_at,
    status_updated_at: projectAlpha.updatedAt,
    finished_at: projectAlpha.updatedAt,
    error_summary: "",
    job_ref: engineRunPayload.job_ref,
  },
  worker: {
    state: "idle",
    total_jobs: 1,
    queued_jobs: 0,
    running_jobs: 0,
    succeeded_jobs: 1,
    failed_jobs: 0,
    next_job_id: "",
  },
  snapshots: {
    available: true,
    count: 1,
    latest_snapshot_id: snapshotPayload.snapshot_id,
    latest_snapshot_kind: snapshotPayload.snapshot_kind,
  },
  exports: {
    available: true,
    count: 1,
    latest_export_id: "export_alpha",
    latest_export_kind: "canon",
    latest_export_format: "markdown",
  },
  latest_failure_summary: "",
  recent_workflow_events: [
    {
      event_type: "export_created",
      status: "succeeded",
      occurred_at: projectAlpha.updatedAt,
      story_id: "",
      import_id: "",
      run_id: "",
      snapshot_id: snapshotPayload.snapshot_id,
      export_id: "export_alpha",
      summary: "Created markdown canon export.",
    },
    {
      event_type: "snapshot_created",
      status: "succeeded",
      occurred_at: projectAlpha.updatedAt,
      story_id: storyAlphaPayload.story_id,
      import_id: "",
      run_id: engineRunPayload.run_id,
      snapshot_id: snapshotPayload.snapshot_id,
      export_id: "",
      summary: "Created canon snapshot.",
    },
  ],
};
const projectExportPayload = {
  export_id: "export_alpha",
  project_id: projectAlpha.id,
  snapshot_id: snapshotPayload.snapshot_id,
  export_kind: "canon",
  export_format: "json",
  filename: "alpha-canon-snapshot.json",
  content_type: "application/json",
  size: 128,
  checksum: "checksum-alpha",
  created_at: projectAlpha.updatedAt,
};
const projectOutputsPayload = {
  project_id: projectAlpha.id,
  status: "succeeded",
  latest_import: projectStatusPayload.latest_import,
  latest_engine_run: projectStatusPayload.latest_engine_run,
  canon: {
    available: true,
    title: "Alpha",
    snapshot_kind: "canon",
    created_at: projectAlpha.updatedAt,
    source_id: "source_alpha",
    chapters: 1,
    scenes: 8,
    evidence_anchor_count: 1,
    extraction_result_count: 1,
    accepted_entity_count: 2,
    accepted_fact_count: 4,
    accepted_relationship_count: 1,
    accepted_state_change_count: 2,
    rejected_candidate_count: 0,
    chapter_scene_counts: [
      { chapter_index: 1, scene_count: 2 },
      { chapter_index: 2, scene_count: 2 },
      { chapter_index: 3, scene_count: 2 },
      { chapter_index: 4, scene_count: 2 },
    ],
  },
  surfaces: [
    {
      surface: "characters",
      title: "Characters",
      status: "ready",
      summary:
        "2 accepted character or entity records are available from the latest canon snapshot.",
      item_count: 2,
    },
    {
      surface: "world",
      title: "World",
      status: "ready",
      summary: "1 accepted world relationship is available from the latest canon snapshot.",
      item_count: 1,
    },
    {
      surface: "timeline",
      title: "Timeline",
      status: "ready",
      summary: "2 accepted state changes are available from the latest canon snapshot.",
      item_count: 2,
    },
    {
      surface: "scenes",
      title: "Scenes",
      status: "ready",
      summary: "8 processed scenes are available from the latest canon snapshot.",
      item_count: 8,
    },
    {
      surface: "continuity",
      title: "Continuity",
      status: "ready",
      summary: "4 accepted facts are available for continuity review.",
      item_count: 4,
    },
    {
      surface: "prompts",
      title: "Prompt Packs",
      status: "ready",
      summary: "1 extraction result is available for prompt pack generation.",
      item_count: 1,
    },
    {
      surface: "exports",
      title: "Exports",
      status: "ready",
      summary: "8 processed scenes are available for export.",
      item_count: 8,
    },
  ],
  language_identity: {
    translation_unit_count: 8,
    translation_review_count: 1,
    translation_review_items: [
      {
        issue_code: "translation_review_required",
        issue_label: "Glossary term needs review",
        chapter_id: "source_alpha_chapter_001",
        scene_id: "source_alpha_chapter_001_scene_001",
        evidence_anchor_count: 1,
        reason: "Aevryn preserved an uncertain term for review.",
      },
    ],
    identity_decision_count: 7,
    identity_resolved_count: 5,
    identity_ambiguous_count: 1,
    identity_unresolved_count: 1,
    identity_review_items: [
      {
        status: "ambiguous",
        chapter_id: "source_alpha_chapter_001",
        scene_id: "source_alpha_chapter_001_scene_001",
        evidence_anchor_id: "anchor_001",
        reference_kind: "title",
        reference_label: "The general",
        candidate_count: 2,
        confidence: 0.87,
        reason: "Multiple identity profiles have equal confidence.",
      },
      {
        status: "unresolved",
        chapter_id: "source_alpha_chapter_001",
        scene_id: "source_alpha_chapter_001_scene_002",
        evidence_anchor_id: "anchor_002",
        reference_kind: "description",
        reference_label: "the white-haired officer",
        candidate_count: 0,
        confidence: 0,
        reason: "No supported identity match was found.",
      },
    ],
  },
  character_profiles: [
    ...characterPreviewPayload.character_profiles,
    {
      ...characterPreviewPayload.character_profiles[0],
      character_id: "character_mark_duplicate",
      aliases: { title: "Aliases", items: ["Captain Mark"] },
      titles: { title: "Titles", items: ["Captain"] },
      descriptions: { title: "Descriptions", items: ["human male captain"] },
      race: { title: "Race", items: ["Human"] },
      gender: { title: "Gender", items: ["Male"] },
      recent_changes: {
        title: "Recent Changes",
        items: ["display_name -> Mark", "gender -> Male", "current_weapon -> Rusty Dagger"],
      },
      evidence_summary: "8 verified facts",
    },
  ],
  world_sheet: worldPreviewPayload.world_sheet,
  timeline_changes: [
    {
      change_id: "state_fact_character_mark_current_weapon_iron_sword",
      chapter_index: 1,
      scene_index: 1,
      chapter_title: "Chapter 1",
      scene_title: "Scene 1",
      entity_id: "character_mark",
      entity_name: "Mark",
      attribute: "current_weapon",
      value: "Iron Sword",
    },
    {
      change_id: "state_fact_character_lyra_status_injured",
      chapter_index: 2,
      scene_index: 1,
      chapter_title: "Chapter 2",
      scene_title: "Scene 1",
      entity_id: "character_lyra",
      entity_name: "Lyra",
      attribute: "status",
      value: "Injured",
    },
  ],
  scene_sheets: [
    {
      ...scenePreviewPayload.scene_sheet,
      title: "Processed Scene 7",
    },
  ],
  prompt_packs: [promptPreviewPayload.production_pack],
  continuity_report: continuityPreviewPayload.continuity_report,
  export_options: [
    {
      export_kind: "production_pack",
      formats: ["markdown"],
      label: "Production Pack",
    },
    {
      export_kind: "continuity_report",
      formats: ["markdown", "json"],
      label: "Continuity Report",
    },
  ],
};

const manyPromptPacks = Array.from({ length: 28 }, (_, index) => ({
  ...promptPreviewPayload.production_pack,
  scene: {
    ...promptPreviewPayload.production_pack.scene,
    scene_id: `scene_${index + 1}`,
    title: `Scene ${index + 1}`,
  },
  image_prompt: {
    ...promptPreviewPayload.production_pack.image_prompt,
    items: [
      ...promptPreviewPayload.production_pack.image_prompt.items,
      `Scene ${index + 1} image prompt detail`,
    ],
  },
}));

function storeAuthenticatedProject() {
  window.localStorage.setItem("aevryn.session", JSON.stringify(session));
  window.localStorage.setItem("aevryn.projects", JSON.stringify([projectAlpha]));
}

function projectOutputsPath(projectId: string): string {
  return `${API_PATHS.projects}/${projectId}/outputs`;
}

describe("App shell routing", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        if (url.endsWith(API_PATHS.projects)) {
          if (init?.method === "POST") {
            const body = JSON.parse(String(init.body));
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  project_id: body.project_id,
                  name: body.name,
                  created_at: body.now,
                  updated_at: body.now,
                }),
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify({ projects: [] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/settings`)) {
          if (init?.method === "PUT") {
            const body = JSON.parse(String(init.body));
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  project_id: projectAlphaPayload.project_id,
                  default_export_format: body.default_export_format,
                  locale: body.locale,
                }),
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify(projectSettingsPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
          if (init?.method === "POST") {
            const body = JSON.parse(String(init.body));
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  story_id: body.story_id,
                  project_id: projectAlphaPayload.project_id,
                  title: body.title,
                  created_at: body.now,
                  updated_at: body.now,
                }),
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify({ stories: [] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
          )
        ) {
          if (init?.method === "POST") {
            const body = JSON.parse(String(init.body));
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  ...importRecordPayload,
                  import_id: body.import_id,
                  source_id: body.source_id,
                  filename: body.filename,
                  created_at: body.now,
                }),
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify({ imports: [] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
          return Promise.resolve(new Response(JSON.stringify({ runs: [] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/status`)) {
          return Promise.resolve(new Response(JSON.stringify(projectStatusPayload)));
        }
        if (url.endsWith(projectOutputsPath(projectAlphaPayload.project_id))) {
          return Promise.resolve(new Response(JSON.stringify(projectOutputsPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/exports`)) {
          if (init?.method === "POST") {
            const body = JSON.parse(String(init.body));
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  ...projectExportPayload,
                  export_id: body.export_id,
                  snapshot_id: body.snapshot_id,
                  export_format: body.export_format,
                  filename: body.filename,
                  created_at: body.now,
                }),
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify({ exports: [projectExportPayload] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
        }
        if (
          isImportRunSubmitPath(url, projectAlphaPayload.project_id, storyAlphaPayload.story_id)
        ) {
          const body = JSON.parse(String(init?.body));
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...engineRunPayload,
                import_id: importIdFromRunSubmitPath(url),
                run_id: body.run_id,
                job_ref: `queue://${body.job_id}`,
                started_at: body.now,
                status_updated_at: body.now,
              }),
            ),
          );
        }
        if (url.endsWith(API_PATHS.workerProcess)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                claimed_jobs: 1,
                succeeded_jobs: 1,
                failed_jobs: 0,
              }),
            ),
          );
        }
        if (url.endsWith(API_PATHS.workerProcess)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                claimed_jobs: 1,
                succeeded_jobs: 1,
                failed_jobs: 0,
              }),
            ),
          );
        }
        if (url.endsWith(API_PATHS.workerProcess)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                claimed_jobs: 1,
                succeeded_jobs: 1,
                failed_jobs: 0,
              }),
            ),
          );
        }
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        if (url.endsWith(API_PATHS.importsInspect)) {
          return Promise.resolve(new Response(JSON.stringify(importInspectPayload)));
        }
        if (url.endsWith(API_PATHS.charactersPreview)) {
          return Promise.resolve(new Response(JSON.stringify(characterPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.timelinePreview)) {
          return Promise.resolve(new Response(JSON.stringify(timelinePreviewPayload)));
        }
        if (url.endsWith(API_PATHS.scenesPreview)) {
          return Promise.resolve(new Response(JSON.stringify(scenePreviewPayload)));
        }
        if (url.endsWith(API_PATHS.promptsPreview)) {
          return Promise.resolve(new Response(JSON.stringify(promptPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.exportsPreview)) {
          return Promise.resolve(new Response(JSON.stringify(exportPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.continuityPreview)) {
          return Promise.resolve(new Response(JSON.stringify(continuityPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.worldPreview)) {
          return Promise.resolve(new Response(JSON.stringify(worldPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.authLogin) || url.endsWith(API_PATHS.authRegister)) {
          return Promise.resolve(new Response(JSON.stringify(session)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("redirects unauthenticated users to login", async () => {
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
    expect(screen.getByText("Aevryn")).toBeInTheDocument();
    expect(screen.queryByText("Aevryn Web Alpha Shell")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveValue("");
  });

  it("logs in through the auth API and stores the returned session", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <App />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Password"), "StrongPass123");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(JSON.parse(window.localStorage.getItem("aevryn.session") ?? "{}")).toMatchObject({
      session_token: "session-token",
    });
  });

  it("warns when auth session persistence fails", async () => {
    const user = userEvent.setup();
    const originalSetItem = Storage.prototype.setItem;
    const setItem = vi.spyOn(Storage.prototype, "setItem");
    setItem.mockImplementation(function setStorageItem(this: Storage, key: string, value: string) {
      if (key === "aevryn.session") {
        throw new Error("storage unavailable");
      }
      return originalSetItem.call(this, key, value);
    });

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <App />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Password"), "StrongPass123");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(await screen.findByRole("alert")).toHaveTextContent("Session storage failed");
    expect(window.localStorage.getItem("aevryn.session")).toBeNull();
  });

  it("shows auth API login failures", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.authLogin)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                error: "invalid_credentials",
                detail: "Invalid email or password.",
              }),
              {
                status: 401,
              },
            ),
          );
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <App />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Password"), "WrongPass123");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.");
    expect(window.localStorage.getItem("aevryn.session")).toBeNull();
  });

  it("registers through the auth API with normalized values", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);

    render(
      <MemoryRouter initialEntries={["/register"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Create account" })).toBeInTheDocument();
    expect(screen.getByText("Aevryn")).toBeInTheDocument();
    expect(screen.queryByText("Aevryn Web Alpha Shell")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Display name")).toHaveValue("");
    expect(screen.getByLabelText("Email")).toHaveValue("");
    await user.clear(screen.getByLabelText("Display name"));
    await user.type(screen.getByLabelText("Display name"), "  Demo   User  ");
    await user.clear(screen.getByLabelText("Email"));
    await user.type(screen.getByLabelText("Email"), " DEMO.User@example.com ");
    await user.type(screen.getByLabelText("Password"), "StrongPass123");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    const registerCall = fetchMock.mock.calls.find(([input]) =>
      String(input).endsWith(API_PATHS.authRegister),
    );
    const registerBody = JSON.parse(String(registerCall?.[1]?.body));
    expect(registerBody).toMatchObject({
      user_id: "user_demo_user",
      display_name: "Demo User",
      email: "demo.user@example.com",
      password: "StrongPass123",
    });
    expect(registerBody.now).toEqual(expect.any(String));
  });

  it("shows client-side register validation before calling the API", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);

    render(
      <MemoryRouter initialEntries={["/register"]}>
        <App />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Display name"), "Demo User");
    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Password"), "short");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByText("Password must be at least 12 characters.")).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([input]) => String(input).endsWith(API_PATHS.authRegister)),
    ).toBe(false);
  });

  it("redirects users with expired stored sessions to login", async () => {
    window.localStorage.setItem(
      "aevryn.session",
      JSON.stringify({ ...session, expires_at: "2000-01-01T00:00:00.000Z" }),
    );

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
    expect(window.localStorage.getItem("aevryn.session")).toBeNull();
  });

  it("lands on the dashboard after session expiry and login", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem(
      "aevryn.session",
      JSON.stringify({ ...session, expires_at: "2000-01-01T00:00:00.000Z" }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/monitoring"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Password"), "StrongPass123");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Monitoring" })).not.toBeInTheDocument();
  });

  it("redirects authenticated users away from auth screens", async () => {
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Log in" })).not.toBeInTheDocument();
  });

  it("redirects unknown routes to the dashboard for authenticated users", async () => {
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));

    render(
      <MemoryRouter initialEntries={["/unknown-route"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  });

  it("redirects missing projects to the dashboard", async () => {
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));

    render(
      <MemoryRouter initialEntries={["/projects/project_missing"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  });

  it("opens direct workspace tab URLs and marks the active tab", async () => {
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    window.localStorage.setItem(
      "aevryn.projects",
      JSON.stringify([
        {
          id: "project_alpha",
          name: "Alpha",
          updatedAt: "2026-06-27T00:00:00.000Z",
        },
      ]),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/characters"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Alpha" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Characters" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Characters" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("renders project monitoring from API-provided status", async () => {
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/monitoring"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Monitoring" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Monitoring" })).not.toBeInTheDocument();
    expect(await screen.findByRole("region", { name: "API health" })).toHaveTextContent("ok");
    expect(screen.getByRole("region", { name: "API health" })).toHaveTextContent(
      "Project Storageconfigured",
    );
    expect(screen.getByRole("region", { name: "API health" })).toHaveTextContent(
      "Import Storageconfigured",
    );
    expect(screen.getByRole("region", { name: "Current project run state" })).toHaveTextContent(
      "succeeded",
    );
    expect(screen.getByRole("region", { name: "Current project run state" })).toHaveTextContent(
      "idle",
    );
    expect(screen.getByRole("region", { name: "Latest failure" })).toHaveTextContent(
      "No recent failure",
    );
    expect(screen.getByRole("region", { name: "Snapshot availability" })).toHaveTextContent(
      "Canon snapshot ready",
    );
    expect(screen.getByRole("region", { name: "Export availability" })).toHaveTextContent(
      "canon is available.",
    );
    expect(screen.getByRole("region", { name: "Recent workflow events" })).toHaveTextContent(
      "Created markdown canon export.",
    );
  });

  it("reuses dashboard health data when navigating to monitoring inside the freshness window", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith(API_PATHS.health)) {
        return Promise.resolve(new Response(JSON.stringify(healthPayload)));
      }
      if (url.endsWith(API_PATHS.capabilities)) {
        return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
      }
      if (url.endsWith(API_PATHS.projects)) {
        return Promise.resolve(new Response(JSON.stringify({ projects: [projectAlphaPayload] })));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
        return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/status`)) {
        return Promise.resolve(new Response(JSON.stringify(projectStatusPayload)));
      }
      if (url.endsWith(projectOutputsPath(projectAlphaPayload.project_id))) {
        return Promise.resolve(new Response(JSON.stringify(projectOutputsPayload)));
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    await user.click(await screen.findByText("Diagnostics"));
    const dashboardHealth = await screen.findByRole("region", { name: "API Health" });
    await waitFor(() => expect(dashboardHealth).toHaveTextContent("ok"));
    await user.click(await screen.findByRole("link", { name: /Alpha/ }));
    await user.click(await screen.findByRole("link", { name: "View monitoring" }));
    expect(
      await screen.findByRole("region", { name: "Current project run state" }),
    ).toHaveTextContent("succeeded");

    const healthCalls = fetchMock.mock.calls.filter(([input]) =>
      String(input).endsWith(API_PATHS.health),
    );
    expect(healthCalls).toHaveLength(1);
  });

  it("supports a Phase 10 frontend alpha smoke path across workspace surfaces", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        if (url.endsWith(API_PATHS.projects)) {
          return Promise.resolve(new Response(JSON.stringify({ projects: [projectAlphaPayload] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
          return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ imports: [importRecordPayload] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                runs: [
                  {
                    ...engineRunPayload,
                    status: "succeeded",
                    finished_at: projectAlpha.updatedAt,
                  },
                ],
              }),
            ),
          );
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ snapshots: [snapshotPayload] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/status`)) {
          return Promise.resolve(new Response(JSON.stringify(projectStatusPayload)));
        }
        if (url.endsWith(projectOutputsPath(projectAlphaPayload.project_id))) {
          return Promise.resolve(new Response(JSON.stringify(projectOutputsPayload)));
        }
        if (url.endsWith(API_PATHS.charactersPreview)) {
          return Promise.resolve(new Response(JSON.stringify(characterPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.worldPreview)) {
          return Promise.resolve(new Response(JSON.stringify(worldPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.timelinePreview)) {
          return Promise.resolve(new Response(JSON.stringify(timelinePreviewPayload)));
        }
        if (url.endsWith(API_PATHS.scenesPreview)) {
          return Promise.resolve(new Response(JSON.stringify(scenePreviewPayload)));
        }
        if (url.endsWith(API_PATHS.continuityPreview)) {
          return Promise.resolve(new Response(JSON.stringify(continuityPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.promptsPreview)) {
          return Promise.resolve(new Response(JSON.stringify(promptPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.exportsPreview)) {
          return Promise.resolve(new Response(JSON.stringify(exportPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    await user.click(await screen.findByRole("link", { name: /Alpha/ }));
    expect(await screen.findByRole("heading", { name: "Alpha" })).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Import" }));
    expect(await screen.findByRole("heading", { name: "Saved Imports" })).toBeInTheDocument();
    expect(await screen.findByText("Canon snapshot ready")).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "View monitoring" }));
    expect(
      await screen.findByRole("region", { name: "Current project run state" }),
    ).toHaveTextContent("Succeeded");
    expect(screen.getByRole("region", { name: "Snapshot availability" })).toHaveTextContent(
      "Canon snapshot ready",
    );

    await user.click(screen.getByRole("link", { name: "Characters" }));
    expect(
      await screen.findByRole("region", { name: "Processed project output" }),
    ).toHaveTextContent("2 accepted character or entity records");
    expect(screen.getByLabelText("Source text")).not.toBeVisible();
    await user.click(screen.getByText("Developer preview"));
    await user.click(await screen.findByRole("button", { name: "Preview characters" }));
    expect(await screen.findByRole("heading", { name: "Character Profiles" })).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "World" }));
    expect(
      await screen.findByRole("region", { name: "Processed project output" }),
    ).toHaveTextContent("1 accepted world relationship");
    const worldOutput = screen.getByRole("region", { name: "Processed project output" });
    const worldDetailPanels = worldOutput.querySelectorAll("details.profile-disclosure");
    expect(worldDetailPanels.length).toBeGreaterThanOrEqual(1);
    worldDetailPanels.forEach((panel) => expect(panel).not.toHaveAttribute("open"));
    expect(screen.getByLabelText("AI response JSON")).not.toBeVisible();
    await user.click(screen.getByText("Developer preview"));
    await user.click(await screen.findByRole("button", { name: "Preview world" }));
    expect(await screen.findByRole("heading", { name: "World Sheet" })).toBeInTheDocument();
    const previewWorldDetails = screen.getAllByText("World details")[0].closest("details");
    expect(previewWorldDetails).not.toBeNull();
    expect(previewWorldDetails).not.toHaveAttribute("open");

    await user.click(screen.getByRole("link", { name: "Timeline" }));
    expect(
      await screen.findByRole("region", { name: "Processed project output" }),
    ).toHaveTextContent("2 accepted state changes");
    const timelineOutput = screen.getByRole("region", { name: "Processed project output" });
    expect(screen.getByRole("region", { name: "Processed project output" })).toHaveTextContent(
      "Chapter 1, Scene 1",
    );
    expect(screen.getByRole("region", { name: "Processed project output" })).toHaveTextContent(
      "Mark - Current Weapon: Iron Sword",
    );
    const timelineDetailRows = timelineOutput.querySelectorAll("details.detail-disclosure");
    expect(timelineDetailRows.length).toBeGreaterThanOrEqual(1);
    timelineDetailRows.forEach((row) => expect(row).not.toHaveAttribute("open"));
    await user.click(screen.getByText("Developer preview"));
    await user.click(await screen.findByRole("button", { name: "Preview timeline" }));
    expect(await screen.findByRole("heading", { name: "Timeline Order" })).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Scenes" }));
    expect(
      await screen.findByRole("region", { name: "Processed project output" }),
    ).toHaveTextContent("8 processed scenes");
    expect(screen.getByRole("region", { name: "Processed project output" })).toHaveTextContent(
      "Processed Scene 7",
    );
    const sceneOutput = screen.getByRole("region", { name: "Processed project output" });
    const sceneDetailPanels = sceneOutput.querySelectorAll("details.profile-disclosure");
    expect(sceneDetailPanels.length).toBeGreaterThanOrEqual(1);
    sceneDetailPanels.forEach((panel) => expect(panel).not.toHaveAttribute("open"));
    expect(screen.getByRole("region", { name: "Processed project output" })).toHaveTextContent(
      "Characters Present",
    );
    await user.click(screen.getByText("Developer preview"));
    await user.click(await screen.findByRole("button", { name: "Preview scene" }));
    expect(await screen.findByRole("heading", { name: "Scene 7" })).toBeInTheDocument();
    const previewSceneDetails = screen.getAllByText("Scene details")[0].closest("details");
    expect(previewSceneDetails).not.toBeNull();
    expect(previewSceneDetails).not.toHaveAttribute("open");

    await user.click(screen.getByRole("link", { name: "Continuity" }));
    expect(
      await screen.findByRole("region", { name: "Processed project output" }),
    ).toHaveTextContent("4 accepted facts");
    const continuityOutput = screen.getByRole("region", { name: "Processed project output" });
    expect(screen.getByRole("region", { name: "Processed project output" })).toHaveTextContent(
      "Current Weapon: Rusty Dagger.",
    );
    const continuityDetailRows = continuityOutput.querySelectorAll("details.detail-disclosure");
    expect(continuityDetailRows.length).toBeGreaterThanOrEqual(1);
    continuityDetailRows.forEach((row) => expect(row).not.toHaveAttribute("open"));
    expect(continuityOutput).toHaveTextContent("1 still known");
    await user.click(screen.getByText("Developer preview"));
    await user.click(await screen.findByRole("button", { name: "Preview continuity" }));
    expect(await screen.findByRole("heading", { name: "Continuity Report" })).toBeInTheDocument();
    const previewContinuityDetails = screen.getAllByText("Continuity details")[0].closest("details");
    expect(previewContinuityDetails).not.toBeNull();
    expect(previewContinuityDetails).not.toHaveAttribute("open");
    const stableContinuityDetails = screen.getAllByText("1 still known")[0].closest("details");
    expect(stableContinuityDetails).not.toBeNull();
    expect(stableContinuityDetails).not.toHaveAttribute("open");

    await user.click(screen.getByRole("link", { name: "Prompt Packs" }));
    expect(
      await screen.findByRole("region", { name: "Processed project output" }),
    ).toHaveTextContent("1 extraction result");
    expect(screen.getByRole("region", { name: "Processed project output" })).toHaveTextContent(
      "Image Prompt",
    );
    await user.click(screen.getByText("Developer preview"));
    await user.click(await screen.findByRole("button", { name: "Preview prompt pack" }));
    expect(await screen.findByRole("heading", { name: "Production Pack" })).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Exports" }));
    expect(
      await screen.findByRole("region", { name: "Processed project output" }),
    ).toHaveTextContent("8 processed scenes");
    expect(screen.getByRole("region", { name: "Processed project output" })).toHaveTextContent(
      "Production Pack",
    );
    expect(screen.getByRole("region", { name: "Processed project output" })).toHaveTextContent(
      "MARKDOWN",
    );
    await user.click(screen.getByText("Developer preview"));
    await user.click(await screen.findByRole("button", { name: "Preview export" }));
    expect(
      await screen.findByRole("heading", { name: "source_alpha_production_pack.md" }),
    ).toBeInTheDocument();
  });

  it("renders monitoring status API failures without inferring workflow state", async () => {
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/status`)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                error: "project_status_failed",
                detail: "Project status unavailable.",
              }),
              { status: 503 },
            ),
          );
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/monitoring"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Monitoring" })).toBeInTheDocument();
    expect(await screen.findByRole("alert")).toHaveTextContent("Project status unavailable.");
    expect(screen.queryByRole("region", { name: "Export availability" })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: "Recent workflow events" }),
    ).not.toBeInTheDocument();
  });

  it("renders the dashboard shell for authenticated users", async () => {
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Demo User")).toBeInTheDocument();
    expect(await screen.findByText("Evidence in. Canon out.")).toBeInTheDocument();
    expect(await screen.findByText("No projects")).toBeInTheDocument();
    expect(screen.getByText("Open a project to continue working, or create a new story workspace."))
      .toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Dashboard" })).toHaveAttribute("aria-current", "page");
  });

  it("logs out and clears the stored session", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Dashboard" });
    await user.click(screen.getByRole("button", { name: "Log out" }));

    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
    expect(window.localStorage.getItem("aevryn.session")).toBeNull();
  });

  it("renders dashboard loading states without showing diagnostics by default", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>(() => {})),
    );

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    const statuses = await screen.findAllByRole("status");
    expect(statuses).toHaveLength(1);
    expect(statuses[0]).toHaveTextContent("Loading projects.");

    await user.click(screen.getByText("Diagnostics"));
    const openStatuses = await screen.findAllByRole("status");
    expect(openStatuses).toHaveLength(3);
    expect(openStatuses[0]).toHaveTextContent("Loading projects.");
    expect(openStatuses[1]).toHaveTextContent("Checking API health.");
    expect(openStatuses[2]).toHaveTextContent("Loading capabilities.");
  });

  it("renders dashboard API errors as alerts", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({ error: "health_failed", detail: "Health check failed." }),
              {
                status: 503,
              },
            ),
          );
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        if (url.endsWith(API_PATHS.projects)) {
          return Promise.resolve(new Response(JSON.stringify({ projects: [] })));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    await user.click(await screen.findByText("Diagnostics"));
    expect(await screen.findByRole("alert")).toHaveTextContent("Health check failed.");
  });

  it("orders dashboard projects by most recent activity", async () => {
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        if (url.endsWith(API_PATHS.projects)) {
          return Promise.resolve(
            new Response(JSON.stringify({ projects: [projectAlphaPayload, projectBetaPayload] })),
          );
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("2 projects")).toBeInTheDocument();
    const projectLinks = screen
      .getAllByRole("link")
      .filter((link) => link.getAttribute("href")?.startsWith("/projects/"));
    expect(projectLinks[0]).toHaveTextContent("Beta");
    expect(projectLinks[1]).toHaveTextContent("Alpha");
  });

  it("shows project API create failures", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        if (url.endsWith(API_PATHS.projects) && init?.method !== "POST") {
          return Promise.resolve(new Response(JSON.stringify({ projects: [] })));
        }
        if (url.endsWith(API_PATHS.projects) && init?.method === "POST") {
          return Promise.resolve(
            new Response(
              JSON.stringify({ error: "project_create_failed", detail: "Project storage failed." }),
              { status: 503 },
            ),
          );
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    const input = await screen.findByLabelText("Project name");
    await user.clear(input);
    await user.type(input, "Temporary Project");
    await user.click(screen.getByRole("button", { name: "Create project" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Project storage failed.");
    expect(screen.queryByRole("link", { name: /Temporary Project/ })).not.toBeInTheDocument();
  });

  it("creates and opens a project", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    const input = await screen.findByLabelText("Project name");
    await user.clear(input);
    await user.type(input, "  Test   Novel  ");
    await user.click(screen.getByRole("button", { name: "Create project" }));

    expect(await screen.findByRole("heading", { name: "Test Novel" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Characters" })).toBeInTheDocument();
  });

  it("deletes a project from the dashboard after two confirmations", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi
      .spyOn(window, "confirm")
      .mockReturnValueOnce(true)
      .mockReturnValueOnce(true);
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith(API_PATHS.health)) {
        return Promise.resolve(new Response(JSON.stringify(healthPayload)));
      }
      if (url.endsWith(API_PATHS.capabilities)) {
        return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
      }
      if (url.endsWith(API_PATHS.projects)) {
        return Promise.resolve(new Response(JSON.stringify({ projects: [projectAlphaPayload] })));
      }
      if (
        url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`) &&
        init?.method === "DELETE"
      ) {
        return Promise.resolve(new Response(null, { status: 204 }));
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("1 project")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Alpha Updated/u })).toHaveAttribute(
      "href",
      "/projects/project_alpha",
    );
    expect(screen.getByText("Open workspace")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Delete project Alpha" }));

    await waitFor(() =>
      expect(screen.queryByRole("link", { name: /Alpha Updated/u })).not.toBeInTheDocument(),
    );
    expect(confirmSpy).toHaveBeenNthCalledWith(1, "Delete project Alpha?");
    expect(confirmSpy).toHaveBeenNthCalledWith(
      2,
      "Project data will be lost forever, are you sure?",
    );
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(`${API_PATHS.projects}/project_alpha`),
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("keeps the create button disabled for blank project names", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    const input = await screen.findByLabelText("Project name");
    await user.clear(input);
    await user.type(input, "   ");

    expect(screen.getByRole("button", { name: "Create project" })).toBeDisabled();
  });

  it("inspects pasted source from the import workspace tab", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    window.localStorage.setItem(
      "aevryn.projects",
      JSON.stringify([
        {
          id: "project_alpha",
          name: "Alpha",
          updatedAt: "2026-06-27T00:00:00.000Z",
        },
      ]),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Import" })).toBeInTheDocument();
    expect(await screen.findByText(".txt")).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.click(screen.getByRole("button", { name: "Inspect import" }));

    expect(await screen.findByRole("heading", { name: "Import Structure" })).toBeInTheDocument();
    expect(screen.getByText("Evidence anchors")).toBeInTheDocument();
    expect(screen.getByText("1 chapter, 8 scenes, 1 evidence anchor.")).toBeInTheDocument();
    expect(screen.queryByText("8 scenes ready for review.")).not.toBeInTheDocument();
    expect(screen.getByText("Chapter 1")).toBeInTheDocument();
    expect(screen.queryByText("source_alpha_chapter_007_scene_001")).not.toBeInTheDocument();
  });

  it("shows web import as unavailable until permission checks exist", async () => {
    storeAuthenticatedProject();
    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Web Import" })).toBeInTheDocument();
    expect(screen.getByLabelText("Source URL")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Check permissions" })).toBeDisabled();
    expect(
      screen.getByText("Unavailable: permission checks are required before web intake."),
    ).toBeInTheDocument();
  });

  it("inspects selected source files from the import workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    const inspectBodies: Array<Record<string, string>> = [];
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith(API_PATHS.importsInspect)) {
        inspectBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(new Response(JSON.stringify(importInspectPayload)));
      }
      if (url.endsWith(API_PATHS.health)) {
        return Promise.resolve(new Response(JSON.stringify(healthPayload)));
      }
      if (url.endsWith(API_PATHS.capabilities)) {
        return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
        return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
        return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
        )
      ) {
        return Promise.resolve(new Response(JSON.stringify({ imports: [] })));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
        return Promise.resolve(new Response(JSON.stringify({ runs: [] })));
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
        )
      ) {
        return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
      }
      if (url.endsWith(API_PATHS.sourceFormats)) {
        return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Import" })).toBeInTheDocument();
    expect(await screen.findByText(".md/.markdown")).toBeInTheDocument();
    expect(screen.getByLabelText("Source text")).toHaveValue("");
    expect(screen.getByLabelText("Source file")).toHaveAttribute(
      "accept",
      ".txt,.md,.markdown,.html,.htm,.xhtml,.fb2,.docx,.odt,.epub",
    );
    expect(screen.getByLabelText("Source file")).toHaveAttribute("multiple");

    const supportedUploads = [
      { filename: "chapter_upload.txt", sourceId: "chapter_upload" },
      { filename: "chapter_upload.md", sourceId: "chapter_upload" },
      { filename: "chapter_upload.html", sourceId: "chapter_upload" },
      { filename: "chapter_upload.fb2", sourceId: "chapter_upload" },
      { filename: "chapter_upload.docx", sourceId: "chapter_upload" },
      { filename: "chapter_upload.odt", sourceId: "chapter_upload" },
      { filename: "chapter_upload.epub", sourceId: "chapter_upload" },
    ];

    for (const [index, upload] of supportedUploads.entries()) {
      const content = `Chapter 1\nUploaded from ${upload.filename}.`;
      await user.upload(screen.getByLabelText("Source file"), new File([content], upload.filename));
      await waitFor(() =>
        expect(screen.getAllByText(new RegExp(upload.filename, "u")).length).toBeGreaterThanOrEqual(
          1,
        ),
      );
      await user.click(screen.getByRole("button", { name: "Inspect import" }));
      await waitFor(() => expect(inspectBodies).toHaveLength(index + 1));

      expect(inspectBodies[index]).toMatchObject({
        filename: upload.filename,
        source_id: upload.sourceId,
      });
      expect((screen.getByLabelText("Import reference") as HTMLInputElement).value).toMatch(
        /^import_chapter_upload_/u,
      );
      expect(atob(inspectBodies[index].content_base64)).toBe(content);
    }

    await user.upload(screen.getByLabelText("Source file"), [
      new File(["Chapter 1\nMark arrived."], "chapter_001.txt"),
      new File(["Chapter 2\nLena answered."], "chapter_002.txt"),
    ]);
    await waitFor(() => expect(screen.getByText(/2 files \//u)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Inspect import" }));
    await waitFor(() => expect(inspectBodies).toHaveLength(supportedUploads.length + 1));
    const bundledBody = inspectBodies[supportedUploads.length];
    expect(bundledBody).toMatchObject({
      filename: "aevryn_import_bundle.txt",
      source_id: "aevryn_import_bundle",
    });
    expect((screen.getByLabelText("Import reference") as HTMLInputElement).value).toMatch(
      /^import_aevryn_import_bundle_/u,
    );
    expect(atob(bundledBody.content_base64)).toContain("File: chapter_001.txt");
    expect(atob(bundledBody.content_base64)).toContain("Chapter 2\nLena answered.");

    expect(await screen.findByRole("heading", { name: "Import Structure" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(API_PATHS.importsInspect),
      expect.anything(),
    );
  });

  it("saves multi-file imports with a fresh import reference", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    let savedImportId = "";
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
          return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
          )
        ) {
          if (init?.method === "POST") {
            const body = JSON.parse(String(init.body));
            savedImportId = body.import_id;
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  ...importRecordPayload,
                  import_id: body.import_id,
                  source_id: body.source_id,
                  filename: body.filename,
                  chapter_count: 10,
                  scene_count: 19,
                  evidence_anchor_count: 513,
                  created_at: body.now,
                }),
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify({ imports: [] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
          return Promise.resolve(new Response(JSON.stringify({ runs: [] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
        }
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        if (url.endsWith(API_PATHS.importsInspect)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...importInspectPayload,
                chapters: 10,
                scenes: 19,
                evidence_anchors: 513,
              }),
            ),
          );
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByText(".txt");
    await user.upload(screen.getByLabelText("Source file"), [
      new File(["Chapter 1\nMark arrived."], "chapter_001.txt"),
      new File(["Chapter 2\nLena answered."], "chapter_002.txt"),
    ]);
    await user.click(await screen.findByRole("button", { name: "Inspect import" }));
    expect(
      await screen.findByText("10 chapters, 19 scenes, 513 evidence anchors."),
    ).toBeInTheDocument();
    expect(screen.queryByText("19 scenes ready for review.")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Save import" }));

    await waitFor(() => expect(savedImportId).toMatch(/^import_aevryn_import_bundle_/u));
    expect(screen.queryByText("Import saved.")).not.toBeInTheDocument();
    expect(savedImportId).not.toBe("import_alpha");
  });

  it("retries duplicate automatic import references with a new reference", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    const savedImportIds: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
          return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
          )
        ) {
          if (init?.method === "POST") {
            const body = JSON.parse(String(init.body));
            savedImportIds.push(body.import_id);
            if (savedImportIds.length === 1) {
              return Promise.resolve(
                new Response(
                  JSON.stringify({
                    error: "duplicate_record",
                    detail: `Duplicate import: ${body.import_id}`,
                  }),
                  { status: 409 },
                ),
              );
            }
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  ...importRecordPayload,
                  import_id: body.import_id,
                  source_id: body.source_id,
                  filename: body.filename,
                  chapter_count: 10,
                  scene_count: 19,
                  evidence_anchor_count: 513,
                  created_at: body.now,
                }),
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify({ imports: [] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
          return Promise.resolve(new Response(JSON.stringify({ runs: [] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
        }
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        if (url.endsWith(API_PATHS.importsInspect)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...importInspectPayload,
                chapters: 10,
                scenes: 19,
                evidence_anchors: 513,
              }),
            ),
          );
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByText(".txt");
    await user.upload(screen.getByLabelText("Source file"), [
      new File(["Chapter 1\nMark arrived."], "chapter_001.txt"),
      new File(["Chapter 2\nLena answered."], "chapter_002.txt"),
    ]);
    await user.click(await screen.findByRole("button", { name: "Inspect import" }));
    await screen.findByText("10 chapters, 19 scenes, 513 evidence anchors.");
    await user.click(screen.getByRole("button", { name: "Save import" }));

    await waitFor(() => expect(savedImportIds).toHaveLength(2));
    expect(savedImportIds[0]).toMatch(/^import_aevryn_import_bundle_/u);
    expect(savedImportIds[1]).toMatch(/^import_aevryn_import_bundle_/u);
    expect(savedImportIds[1]).not.toBe(savedImportIds[0]);
    expect(screen.queryByText(/Duplicate import:/u)).not.toBeInTheDocument();
  });

  it("asks before adding another import to an already populated story", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    let createImportCalls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
          return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
          )
        ) {
          if (init?.method === "POST") {
            createImportCalls += 1;
            return Promise.resolve(new Response(JSON.stringify(importRecordPayload)));
          }
          return Promise.resolve(new Response(JSON.stringify({ imports: [importRecordPayload] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
          return Promise.resolve(new Response(JSON.stringify({ runs: [] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
        }
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        if (url.endsWith(API_PATHS.importsInspect)) {
          return Promise.resolve(new Response(JSON.stringify(importInspectPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Chapter import")).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 2{enter}Different opening.");
    await user.click(screen.getByRole("button", { name: "Inspect import" }));
    await user.click(await screen.findByRole("button", { name: "Save import" }));

    expect(confirm).toHaveBeenCalledWith(
      "Alpha Story already has imported source. Only continue if this source belongs to the same story. Add it anyway?",
    );
    expect(createImportCalls).toBe(0);
  });

  it("saves import metadata from the import workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    let projectRuns: Record<string, unknown>[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
          return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
          )
        ) {
          if (init?.method === "POST") {
            const body = JSON.parse(String(init.body));
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  ...importRecordPayload,
                  import_id: body.import_id,
                  source_id: body.source_id,
                  filename: body.filename,
                  created_at: body.now,
                }),
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify({ imports: [] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
          return Promise.resolve(new Response(JSON.stringify({ runs: projectRuns })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
        }
        if (
          isImportRunSubmitPath(url, projectAlphaPayload.project_id, storyAlphaPayload.story_id)
        ) {
          const body = JSON.parse(String(init?.body));
          const run = {
            ...engineRunPayload,
            import_id: importIdFromRunSubmitPath(url),
            run_id: body.run_id,
            job_ref: `queue://${body.job_id}`,
            started_at: body.now,
            status_updated_at: body.now,
          };
          projectRuns = [
            {
              ...run,
              status: "succeeded",
              finished_at: body.now,
            },
          ];
          return Promise.resolve(new Response(JSON.stringify(run)));
        }
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        if (url.endsWith(API_PATHS.importsInspect)) {
          return Promise.resolve(new Response(JSON.stringify(importInspectPayload)));
        }
        if (url.endsWith(API_PATHS.workerProcess)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                claimed_jobs: 1,
                succeeded_jobs: 1,
                failed_jobs: 0,
              }),
            ),
          );
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Import" })).toBeInTheDocument();
    expect(await screen.findByText("No saved imports")).toBeInTheDocument();
    expect(screen.getByText("Advanced import references")).toBeVisible();
    expect(screen.getByLabelText("Import reference")).not.toBeVisible();
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.click(screen.getByRole("button", { name: "Inspect import" }));
    await user.click(await screen.findByRole("button", { name: "Save import" }));

    await screen.findByText("Chapter import");
    expect(screen.queryByText("Import saved.")).not.toBeInTheDocument();
    expect(screen.queryByText("chapter_001.txt")).not.toBeInTheDocument();
    expect(screen.getAllByText("8 scenes").length).toBeGreaterThanOrEqual(1);
    await user.click(screen.getByRole("button", { name: "Submit processing" }));

    expect(screen.queryByText("Processing started.")).not.toBeInTheDocument();
    expect(screen.queryByText("Processing completed.")).not.toBeInTheDocument();
    expect(await screen.findByText("Succeeded run")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Processed" })).toBeDisabled();

    await user.clear(screen.getByLabelText("Source text"));
    expect(screen.getByRole("button", { name: "Inspect import" })).toBeDisabled();
    await user.upload(
      screen.getByLabelText("Source file"),
      new File(["Chapter 2\nA new import can begin."], "chapter_002.txt"),
    );
    expect(await screen.findByRole("button", { name: "Inspect import" })).toBeEnabled();
  });

  it("does not drain worker jobs from hosted browser sessions", async () => {
    vi.stubEnv("VITE_AEVRYN_BROWSER_WORKER_DRAIN_ENABLED", "false");
    const user = userEvent.setup();
    storeAuthenticatedProject();
    const projectRuns: Record<string, unknown>[] = [];
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
        return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
        return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
        )
      ) {
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...importRecordPayload,
                import_id: body.import_id,
                source_id: body.source_id,
                filename: body.filename,
                created_at: body.now,
              }),
            ),
          );
        }
        return Promise.resolve(new Response(JSON.stringify({ imports: [] })));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
        return Promise.resolve(new Response(JSON.stringify({ runs: projectRuns })));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/status`)) {
        return Promise.resolve(new Response(JSON.stringify(projectStatusPayload)));
      }
      if (url.endsWith(projectOutputsPath(projectAlphaPayload.project_id))) {
        return Promise.resolve(new Response(JSON.stringify(projectOutputsPayload)));
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
        )
      ) {
        return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
      }
      if (
        isImportRunSubmitPath(url, projectAlphaPayload.project_id, storyAlphaPayload.story_id)
      ) {
        const body = JSON.parse(String(init?.body));
        const run = {
          ...engineRunPayload,
          import_id: importIdFromRunSubmitPath(url),
          run_id: body.run_id,
          job_ref: `queue://${body.job_id}`,
          started_at: body.now,
          status_updated_at: body.now,
        };
        projectRuns.unshift(run);
        return Promise.resolve(new Response(JSON.stringify(run)));
      }
      if (url.endsWith(API_PATHS.sourceFormats)) {
        return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
      }
      if (url.endsWith(API_PATHS.importsInspect)) {
        return Promise.resolve(new Response(JSON.stringify(importInspectPayload)));
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Import" })).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.click(screen.getByRole("button", { name: "Inspect import" }));
    await user.click(await screen.findByRole("button", { name: "Save import" }));
    await screen.findByText("Chapter import");
    await user.click(screen.getByRole("button", { name: "Submit processing" }));

    expect(await screen.findByText("Pending run")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Processing" })).toBeDisabled();
    expect(
      fetchMock.mock.calls.some(([input]) => String(input).endsWith(API_PATHS.workerProcess)),
    ).toBe(false);
  });

  it("keeps saved import processing state scoped to the submitted import row", async () => {
    vi.stubEnv("VITE_AEVRYN_BROWSER_WORKER_DRAIN_ENABLED", "false");
    const user = userEvent.setup();
    storeAuthenticatedProject();
    const secondImport = {
      ...importRecordPayload,
      import_id: "import_beta",
      source_id: "source_beta",
      filename: "chapter_002.txt",
      storage_ref: "api_import://story_alpha/import_beta",
    };
    let resolveSubmittedRun: (() => void) | undefined;
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
        return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
        return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
        )
      ) {
        return Promise.resolve(
          new Response(JSON.stringify({ imports: [importRecordPayload, secondImport] })),
        );
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              runs: [
                {
                  ...engineRunPayload,
                  status: "succeeded",
                  finished_at: "2026-06-27T00:00:05.000Z",
                },
              ],
            }),
          ),
        );
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
        )
      ) {
        return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports/${secondImport.import_id}/runs`,
        )
      ) {
        const body = JSON.parse(String(init?.body));
        const pendingRun = {
          ...engineRunPayload,
          run_id: body.run_id,
          import_id: secondImport.import_id,
          status: "pending",
          job_ref: `queue://${body.job_id}`,
          started_at: body.now,
          status_updated_at: body.now,
          finished_at: null,
        };
        return new Promise<Response>((resolve) => {
          resolveSubmittedRun = () => resolve(new Response(JSON.stringify(pendingRun)));
        });
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/status`)) {
        return Promise.resolve(new Response(JSON.stringify(projectStatusPayload)));
      }
      if (url.endsWith(projectOutputsPath(projectAlphaPayload.project_id))) {
        return Promise.resolve(new Response(JSON.stringify(projectOutputsPayload)));
      }
      if (url.endsWith(API_PATHS.sourceFormats)) {
        return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Chapter import")).toBeInTheDocument();
    expect(await screen.findByText("Chapter import 2")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Processed" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Submit processing" }));

    expect(await screen.findByRole("button", { name: "Submitting" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Processed" })).toBeDisabled();

    resolveSubmittedRun?.();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Submit processing" })).toBeEnabled(),
    );
    expect(screen.getByRole("button", { name: "Processed" })).toBeDisabled();
  });

  it("polls hosted import runs until processing finishes", async () => {
    vi.stubEnv("VITE_AEVRYN_BROWSER_WORKER_DRAIN_ENABLED", "false");
    vi.stubEnv("VITE_AEVRYN_ACTIVE_RUN_POLL_INTERVAL_MS", "10");
    const user = userEvent.setup();
    storeAuthenticatedProject();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    let submittedRun: Record<string, unknown> | null = null;
    let runListReadsAfterSubmit = 0;
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
        return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
        return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
        )
      ) {
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...importRecordPayload,
                import_id: body.import_id,
                source_id: body.source_id,
                filename: body.filename,
                created_at: body.now,
              }),
            ),
          );
        }
        return Promise.resolve(new Response(JSON.stringify({ imports: [importRecordPayload] })));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
        if (submittedRun) {
          runListReadsAfterSubmit += 1;
        }
        const status = runListReadsAfterSubmit >= 2 ? "succeeded" : "pending";
        const finishedFields =
          status === "succeeded"
            ? { finished_at: "2026-06-27T00:00:05.000Z" }
            : { finished_at: null };
        return Promise.resolve(
          new Response(
            JSON.stringify({
              runs: submittedRun ? [{ ...submittedRun, status, ...finishedFields }] : [],
            }),
          ),
        );
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
        )
      ) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              snapshots:
                runListReadsAfterSubmit >= 2
                  ? [{ ...snapshotPayload, run_id: submittedRun?.run_id }]
                  : [],
            }),
          ),
        );
      }
      if (
        isImportRunSubmitPath(url, projectAlphaPayload.project_id, storyAlphaPayload.story_id)
      ) {
        const body = JSON.parse(String(init?.body));
        submittedRun = {
          ...engineRunPayload,
          import_id: importIdFromRunSubmitPath(url),
          run_id: body.run_id,
          status: "pending",
          job_ref: `queue://${body.job_id}`,
          started_at: body.now,
          status_updated_at: body.now,
          finished_at: null,
        };
        return Promise.resolve(new Response(JSON.stringify(submittedRun)));
      }
      if (url.endsWith(API_PATHS.sourceFormats)) {
        return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
      }
      if (url.endsWith(API_PATHS.importsInspect)) {
        return Promise.resolve(new Response(JSON.stringify(importInspectPayload)));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/status`)) {
        return Promise.resolve(new Response(JSON.stringify(projectStatusPayload)));
      }
      if (url.endsWith(projectOutputsPath(projectAlphaPayload.project_id))) {
        return Promise.resolve(new Response(JSON.stringify(projectOutputsPayload)));
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Import" })).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.click(screen.getByRole("button", { name: "Inspect import" }));
    await user.click(await screen.findByRole("button", { name: "Save import" }));
    await screen.findByText("Chapter import");
    await user.click(screen.getAllByRole("button", { name: "Submit processing" })[0]);

    expect(await screen.findByRole("button", { name: "Processing" })).toBeDisabled();
    expect(await screen.findByLabelText("Processing progress")).toHaveTextContent("Queued");
    expect(screen.getByLabelText("Processing progress")).toHaveTextContent("Processing");

    await waitFor(() => expect(screen.getByRole("button", { name: "Processed" })).toBeDisabled());
    expect(await screen.findByText("Succeeded run")).toBeInTheDocument();
    expect(screen.getByText("Canon snapshot ready")).toBeInTheDocument();
    expect(screen.getByText(/Canon output is ready/u)).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([input]) => String(input).endsWith(API_PATHS.workerProcess)),
    ).toBe(false);
  });

  it("creates default story metadata while saving the first import from a fresh project", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    let createdStoryId = "";
    let createdStoryTitle = "";
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
        return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          createdStoryId = body.story_id;
          createdStoryTitle = body.title;
          return Promise.resolve(
            new Response(
              JSON.stringify({
                story_id: body.story_id,
                project_id: projectAlphaPayload.project_id,
                title: body.title,
                created_at: body.now,
                updated_at: body.now,
              }),
            ),
          );
        }
        if (createdStoryId) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                stories: [
                  {
                    story_id: createdStoryId,
                    project_id: projectAlphaPayload.project_id,
                    title: createdStoryTitle,
                    created_at: projectAlpha.updatedAt,
                    updated_at: projectAlpha.updatedAt,
                  },
                ],
              }),
            ),
          );
        }
        return Promise.resolve(new Response(JSON.stringify({ stories: [] })));
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/story_alpha_story/imports`,
        )
      ) {
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...importRecordPayload,
                story_id: "story_alpha_story",
                import_id: body.import_id,
                source_id: body.source_id,
                filename: body.filename,
                created_at: body.now,
              }),
            ),
          );
        }
        return Promise.resolve(new Response(JSON.stringify({ imports: [] })));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
        return Promise.resolve(new Response(JSON.stringify({ runs: [] })));
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/story_alpha_story/snapshots?snapshot_kind=canon`,
        )
      ) {
        return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
      }
      if (url.endsWith(API_PATHS.sourceFormats)) {
        return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
      }
      if (url.endsWith(API_PATHS.importsInspect)) {
        return Promise.resolve(new Response(JSON.stringify(importInspectPayload)));
      }
      if (url.endsWith(API_PATHS.health)) {
        return Promise.resolve(new Response(JSON.stringify(healthPayload)));
      }
      if (url.endsWith(API_PATHS.capabilities)) {
        return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByText("Aevryn will create a story record when you save this import."),
    ).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.click(screen.getByRole("button", { name: "Inspect import" }));
    await user.click(await screen.findByRole("button", { name: "Save import" }));

    await waitFor(() => expect(createdStoryId).toBe("story_alpha_story"));
    expect(screen.queryByText("Import saved.")).not.toBeInTheDocument();
    expect(createdStoryTitle).toBe("Alpha Story");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("restores persisted imports runs and snapshot availability after refresh", async () => {
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
          return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ imports: [importRecordPayload] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                runs: [
                  {
                    ...engineRunPayload,
                    run_id: "run_old_succeeded",
                    status: "succeeded",
                    status_updated_at: "2026-06-26T00:00:00.000Z",
                    finished_at: "2026-06-26T00:00:00.000Z",
                  },
                  {
                    ...engineRunPayload,
                    run_id: "run_new_failed",
                    status: "failed",
                    status_updated_at: projectAlpha.updatedAt,
                    finished_at: projectAlpha.updatedAt,
                    error_summary: "Parser could not read chapter content.",
                  },
                ],
              }),
            ),
          );
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
          )
        ) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                snapshots: [{ ...snapshotPayload, run_id: "run_old_succeeded" }],
              }),
            ),
          );
        }
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}/status`)) {
          return Promise.resolve(new Response(JSON.stringify(projectStatusPayload)));
        }
        if (url.endsWith(projectOutputsPath(projectAlpha.id))) {
          return Promise.resolve(new Response(JSON.stringify(projectOutputsPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}/exports`)) {
          return Promise.resolve(new Response(JSON.stringify({ exports: [projectExportPayload] })));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(window.localStorage.getItem("aevryn.projects")).toBeNull();
    expect(await screen.findByRole("heading", { name: "Saved Imports" })).toBeInTheDocument();
    expect(await screen.findByText("Chapter import")).toBeInTheDocument();
    expect(screen.getByText("8 scenes")).toBeInTheDocument();
    expect(await screen.findByText("Failed run")).toBeInTheDocument();
    expect(screen.getByText("Succeeded run")).toBeInTheDocument();
    const projectRunsSection = screen.getByRole("region", { name: "Project runs" });
    const runStatuses = within(projectRunsSection).getAllByText(/^(Failed|Succeeded) run$/);
    expect(runStatuses.map((status) => status.textContent)).toEqual([
      "Failed run",
      "Succeeded run",
    ]);
    expect(screen.getByText("No snapshot: run failed")).toBeInTheDocument();
    expect(screen.getByText("Canon snapshot ready")).toBeInTheDocument();
  });

  it("shows persisted failed import runs without crashing after refresh", async () => {
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
          return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ imports: [importRecordPayload] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                runs: [
                  {
                    ...engineRunPayload,
                    status: "failed",
                    finished_at: projectAlpha.updatedAt,
                    error_summary: "Parser could not read chapter content.",
                  },
                ],
              }),
            ),
          );
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
        }
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}/status`)) {
          return Promise.resolve(new Response(JSON.stringify(projectStatusPayload)));
        }
        if (url.endsWith(projectOutputsPath(projectAlpha.id))) {
          return Promise.resolve(new Response(JSON.stringify(projectOutputsPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}/exports`)) {
          return Promise.resolve(new Response(JSON.stringify({ exports: [projectExportPayload] })));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Failed run")).toBeInTheDocument();
    expect(screen.getByText("No snapshot: run failed")).toBeInTheDocument();
    expect(
      screen.getByText("Run error: Parser could not read chapter content."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Canon snapshot ready")).not.toBeInTheDocument();
  });

  it("shows import evidence failures without internal anchor IDs", async () => {
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
          return Promise.resolve(new Response(JSON.stringify({ stories: [storyAlphaPayload] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ imports: [importRecordPayload] })));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                runs: [
                  {
                    ...engineRunPayload,
                    status: "failed",
                    finished_at: projectAlpha.updatedAt,
                    error_summary:
                      "Unknown evidence anchor: aevryn_import_bundle_chapter_010_scene_001_paragraph_023_sentence_002_anchor",
                  },
                  {
                    ...engineRunPayload,
                    run_id: "run_conflicting_fact",
                    status: "failed",
                    finished_at: projectAlpha.updatedAt,
                    error_summary: "Conflicting fact: fact_1",
                  },
                  {
                    ...engineRunPayload,
                    run_id: "run_duplicate_world_section",
                    status: "failed",
                    finished_at: projectAlpha.updatedAt,
                    error_summary: "World sheet section titles must be unique.",
                  },
                  {
                    ...engineRunPayload,
                    run_id: "run_provider_timeout",
                    status: "failed",
                    finished_at: projectAlpha.updatedAt,
                    error_summary: "OpenAI extraction request timed out.",
                  },
                ],
              }),
            ),
          );
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
        }
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}/status`)) {
          return Promise.resolve(new Response(JSON.stringify(projectStatusPayload)));
        }
        if (url.endsWith(projectOutputsPath(projectAlpha.id))) {
          return Promise.resolve(new Response(JSON.stringify(projectOutputsPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}/exports`)) {
          return Promise.resolve(new Response(JSON.stringify({ exports: [projectExportPayload] })));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findAllByText("Failed run")).toHaveLength(4);
    expect(
      screen.getByText(
        "Run error: Import evidence could not be matched during AI extraction. Review the import structure, then retry processing. If it repeats, split the import into smaller chapter batches.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Run error: AI extraction produced conflicting canon facts. Retry processing. If it repeats, review the import structure or split the import into smaller chapter batches.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Run error: World sheet output contained duplicate sections. Aevryn merged matching sections; retry processing.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Run error: AI extraction timed out while reading the provider response. Retry with a smaller chapter batch or increase the provider timeout for large imports.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Unknown evidence anchor/)).not.toBeInTheDocument();
    expect(screen.queryByText(/aevryn_import_bundle/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Conflicting fact/)).not.toBeInTheDocument();
    expect(screen.queryByText(/fact_1/)).not.toBeInTheDocument();
    expect(screen.queryByText(/World sheet section titles must be unique/)).not.toBeInTheDocument();
    expect(screen.queryByText(/OpenAI extraction request timed out/)).not.toBeInTheDocument();
  });

  it("previews character profiles from the characters workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/characters"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Characters" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.clear(screen.getByLabelText("Character IDs"));
    await user.type(screen.getByLabelText("Character IDs"), "character_mark");
    await user.click(screen.getByRole("button", { name: "Preview characters" }));

    expect(await screen.findByRole("heading", { name: "Character Profiles" })).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: "Mark" }).length).toBeGreaterThanOrEqual(1);
    const previewCard = screen.getAllByRole("heading", { name: "Mark" })[0].closest("article");
    expect(previewCard).not.toBeNull();
    expect(previewCard?.querySelector(".character-portrait")).toHaveTextContent("M");
    expect(previewCard?.querySelector("details.profile-disclosure")).not.toHaveAttribute("open");
    expect(screen.getAllByText("Rusty Dagger").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Luna - Ally").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("3 verified facts").length).toBeGreaterThanOrEqual(1);
  });

  it("renders processed character panels from project outputs", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/characters"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Characters" })).toBeInTheDocument();
    const characterHeading = await screen.findByRole("heading", { name: "Mark" });
    expect(characterHeading).toBeInTheDocument();
    const characterCard = characterHeading.closest("article");
    expect(characterCard).not.toBeNull();
    expect(characterCard?.querySelector(".character-portrait")).toHaveTextContent("M");
    expect(characterCard?.querySelector("details.profile-disclosure")).not.toHaveAttribute("open");
    expect(screen.getAllByRole("heading", { name: "Mark" })).toHaveLength(1);
    expect(screen.getByRole("heading", { name: "Race" })).toBeInTheDocument();
    expect(screen.getByText("Human")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Gender" })).toBeInTheDocument();
    expect(screen.getByText("Male")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Aliases" })).toBeInTheDocument();
    expect(screen.getByText("Captain Mark")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Titles" })).toBeInTheDocument();
    expect(screen.getByText("Captain")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Descriptions" })).toBeInTheDocument();
    expect(screen.getByText("Human Male Captain")).toBeInTheDocument();
    expect(screen.getByText("Rusty Dagger")).toBeInTheDocument();
    expect(screen.queryByText("Name: Mark")).not.toBeInTheDocument();
    expect(screen.getByText("8 normalized scenes; 1 review item")).toBeInTheDocument();
    expect(screen.getAllByText("Glossary term needs review").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText(
        "Chapter 1, Scene 1; 1 source link preserved; Aevryn preserved an uncertain term for review.",
      ).length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText("7 reference decisions; 5 resolved / 1 ambiguous / 1 unresolved"),
    ).toBeInTheDocument();
    expect(screen.getByText("Needs review")).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Chapter 1, Scene 1; 2 possible matches; 87% confidence; Aevryn did not merge this reference",
      ).length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Unresolved reference")).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Chapter 1, Scene 2; no supported match; Aevryn left this reference unresolved",
      ).length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("region", { name: "Identity review" })).toHaveTextContent(
      "5 resolved, 1 ambiguous, 1 unresolved.",
    );
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "Unresolved" }));
    expect(screen.getByRole("button", { name: "Unresolved" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByText("Description: the white-haired officer")).toBeInTheDocument();
    expect(screen.queryByText("Title: The general")).not.toBeInTheDocument();
    expect(screen.queryByText("anchor_001")).not.toBeInTheDocument();
    expect(screen.queryByText("source_alpha_chapter_001_scene_001")).not.toBeInTheDocument();
    expect(screen.getByText("11 verified facts")).toBeInTheDocument();
  });

  it("renders a safe project overview with identity review metadata", async () => {
    storeAuthenticatedProject();
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith(API_PATHS.health)) {
        return Promise.resolve(new Response(JSON.stringify(healthPayload)));
      }
      if (url.endsWith(API_PATHS.capabilities)) {
        return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
      }
      if (url.endsWith(projectOutputsPath(projectAlphaPayload.project_id))) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...projectOutputsPayload,
              language_identity: {
                ...projectOutputsPayload.language_identity,
                identity_review_items: [
                  ...projectOutputsPayload.language_identity.identity_review_items,
                  {
                    ...projectOutputsPayload.language_identity.identity_review_items[1],
                    evidence_anchor_id: "anchor_003",
                  },
                ],
              },
            }),
          ),
        );
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
        return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });
    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/overview"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Overview" })).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Language and Identity" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recommended Next Step" })).toBeInTheDocument();
    expect(screen.getByText("Review identity")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open characters" })).toHaveAttribute(
      "href",
      "/projects/project_alpha/characters",
    );
    expect(screen.getByRole("heading", { name: "Quick Actions" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Prompt Packs 1 scenes ready/u })).toHaveAttribute(
      "href",
      "/projects/project_alpha/prompts",
    );
    expect(screen.getByRole("link", { name: /Exports Snapshot export available/u })).toHaveAttribute(
      "href",
      "/projects/project_alpha/exports",
    );
    expect(screen.getByRole("link", { name: "View monitoring" })).toHaveAttribute(
      "href",
      "/projects/project_alpha/monitoring",
    );
    expect(screen.getByText("Title: The general")).toBeInTheDocument();
    expect(
      screen.getByText("Chapter 1, Scene 1; 2 possible matches; 87% confidence; held for review"),
    ).toBeInTheDocument();
    expect(screen.getByText("Description: the white-haired officer")).toBeInTheDocument();
    expect(
      screen.getByText("Chapter 1, Scene 2; 2 similar references; no supported match; left unresolved"),
    ).toBeInTheDocument();
    expect(screen.getByText("Glossary term needs review")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Chapter 1, Scene 1; 1 source link preserved; Aevryn preserved an uncertain term for review.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("anchor_001")).not.toBeInTheDocument();
    expect(screen.queryByText("source_alpha_chapter_001_scene_001")).not.toBeInTheDocument();
  });

  it("renders a bounded prompt scene picker with one selected prompt pack", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        if (url.endsWith(projectOutputsPath(projectAlphaPayload.project_id))) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...projectOutputsPayload,
                prompt_packs: manyPromptPacks,
              }),
            ),
          );
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/prompts"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("region", { name: "Processed project output" }),
    ).toHaveTextContent("Showing 24 of 28 prompt scenes");
    expect(screen.getByRole("button", { name: /Scene 24/u })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Scene 25/u })).not.toBeInTheDocument();

    const selectedPack = screen.getByRole("article", { name: "Selected prompt pack" });
    expect(within(selectedPack).getByRole("heading", { name: "Scene 1" })).toBeInTheDocument();
    expect(within(selectedPack).getByText(/Scene 1 image prompt detail/u)).toBeInTheDocument();
    expect(screen.queryByText(/Scene 2 image prompt detail/u)).not.toBeInTheDocument();
    const promptBodies = selectedPack.querySelectorAll("details.prompt-disclosure");
    expect(promptBodies).toHaveLength(4);
    promptBodies.forEach((body) => expect(body).not.toHaveAttribute("open"));
    await user.click(within(selectedPack).getByRole("button", { name: "Copy Image Prompt" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Scene 1 image prompt detail")),
    );
    expect(within(selectedPack).getByText("Copied")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^Scene 2\b/u }));

    expect(within(selectedPack).getByRole("heading", { name: "Scene 2" })).toBeInTheDocument();
    expect(within(selectedPack).getByText(/Scene 2 image prompt detail/u)).toBeInTheDocument();
  });

  it("clears stale character profiles when local AI JSON validation fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/characters"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Characters" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview characters" }));
    expect(await screen.findByRole("heading", { name: "Character Profiles" })).toBeInTheDocument();

    await user.clear(screen.getByLabelText("AI response JSON"));
    await user.type(screen.getByLabelText("AI response JSON"), "not json");
    await user.click(screen.getByRole("button", { name: "Preview characters" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("AI response must be valid JSON.");
    expect(screen.queryByRole("heading", { name: "Character Profiles" })).not.toBeInTheDocument();
  });

  it("renders an empty state when the character preview has no profiles", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.charactersPreview)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...characterPreviewPayload,
                character_profiles: [],
              }),
            ),
          );
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}`)) {
          return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}/status`)) {
          return Promise.resolve(new Response(JSON.stringify(projectStatusPayload)));
        }
        if (url.endsWith(projectOutputsPath(projectAlpha.id))) {
          return Promise.resolve(new Response(JSON.stringify(projectOutputsPayload)));
        }
        if (url.endsWith(`${API_PATHS.projects}/${projectAlpha.id}/exports`)) {
          return Promise.resolve(new Response(JSON.stringify({ exports: [projectExportPayload] })));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/characters"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Characters" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview characters" }));

    expect(
      await screen.findByRole("heading", { name: "No character profiles" }),
    ).toBeInTheDocument();
  });

  it("clears stale character profiles when a later preview fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    let failPreview = false;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.charactersPreview)) {
          if (failPreview) {
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  error: "character_preview_failed",
                  detail: "Unknown character: character_missing",
                }),
                { status: 400 },
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify(characterPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/characters"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Characters" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview characters" }));
    expect(await screen.findByRole("heading", { name: "Character Profiles" })).toBeInTheDocument();

    failPreview = true;
    await user.clear(screen.getByLabelText("Character IDs"));
    await user.type(screen.getByLabelText("Character IDs"), "character_missing");
    await user.click(screen.getByRole("button", { name: "Preview characters" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unknown character: character_missing",
    );
    expect(screen.queryByRole("heading", { name: "Character Profiles" })).not.toBeInTheDocument();
  });

  it("previews world sheets from the world workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/world"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "World" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}The hangar was quiet.");
    await user.clear(screen.getByLabelText("World entity IDs"));
    await user.type(screen.getByLabelText("World entity IDs"), "location_hangar");
    await user.click(screen.getByRole("button", { name: "Preview world" }));

    expect(await screen.findByRole("heading", { name: "World Sheet" })).toBeInTheDocument();
    expect(
      screen.getAllByRole("heading", { name: "Hangar (location)" }).length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Condition: Alarm active").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Ownership: Academy").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Owner: Zhao Chen's starship").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText(/Chen'S/)).not.toBeInTheDocument();
    expect(screen.getAllByText("2 verified world facts").length).toBeGreaterThanOrEqual(1);
  });

  it("previews timeline order from the timeline workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/timeline"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Timeline" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.click(screen.getByRole("button", { name: "Preview timeline" }));

    expect(await screen.findByRole("heading", { name: "Timeline Order" })).toBeInTheDocument();
    expect(screen.getAllByText("Chapter 1, Scene 1").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Chapter 2, Scene 1").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("source_alpha_chapter_001_scene_001")).not.toBeInTheDocument();
    expect(screen.getByText("Current")).toBeInTheDocument();
    expect(screen.getByText("State change: Mark Current Weapon Iron Sword")).toBeInTheDocument();
  });

  it("previews scene sheets from the scenes workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/scenes"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Scenes" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.clear(screen.getByLabelText("Character IDs"));
    await user.type(screen.getByLabelText("Character IDs"), "character_mark");
    await user.click(screen.getByRole("button", { name: "Preview scene" }));

    expect(await screen.findByRole("heading", { name: "Scene 7" })).toBeInTheDocument();
    expect(screen.getByText("Chapter 1 for Chapter 1, Scene 1.")).toBeInTheDocument();
    expect(screen.getAllByText("Hangar").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("source_alpha_chapter_001_scene_001")).not.toBeInTheDocument();
    expect(screen.getAllByText("Mark").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Mark equipped Rusty Dagger").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("1 verified evidence reference").length).toBeGreaterThanOrEqual(1);
  });

  it("previews continuity reports from the continuity workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/continuity"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Continuity" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.click(screen.getByRole("button", { name: "Preview continuity" }));

    expect(await screen.findByRole("heading", { name: "Continuity Report" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Chapter 1, Scene 1" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Chapter 2, Scene 1" })).toBeInTheDocument();
    const stableContinuityDetails = screen.getAllByText("1 still known")[0].closest("details");
    expect(stableContinuityDetails).not.toBeNull();
    expect(stableContinuityDetails).not.toHaveAttribute("open");
    expect(screen.queryByText("source_alpha_chapter_001_scene_001")).not.toBeInTheDocument();
    expect(
      screen.getAllByText((_content, element) => {
        return (
          element?.tagName === "LI" &&
          element.textContent?.includes("Current Weapon: Rusty Dagger.")
        );
      }).length,
    ).toBeGreaterThanOrEqual(2);
    expect(
      screen.getAllByText((_content, element) => {
        return (
          element?.tagName === "LI" && element.textContent?.includes("Current Weapon: Iron Sword.")
        );
      }).length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Evidence from Chapter 2, Scene 1").length).toBeGreaterThanOrEqual(
      1,
    );
    expect(screen.queryByText(/source_alpha_anchor_002/u)).not.toBeInTheDocument();
  });

  it("previews production packs from the prompt packs workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/prompts"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Prompt Packs" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.clear(screen.getByLabelText("Character IDs"));
    await user.type(screen.getByLabelText("Character IDs"), "character_mark");
    await user.click(screen.getByRole("button", { name: "Preview prompt pack" }));

    expect(await screen.findByRole("heading", { name: "Production Pack" })).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: "Image Prompt" }).length).toBeGreaterThanOrEqual(
      1,
    );
    expect(
      screen.getAllByRole("heading", { name: "Narration Prompt" }).length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText(/Generate this image using only accepted Aevryn canon/u).length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText(/Scene Summary: Mark prepares in the hangar/u).length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Chapter 1 / Chapter 1, Scene 1")).toBeInTheDocument();
    expect(screen.queryByText("source_alpha_chapter_001_scene_001")).not.toBeInTheDocument();
    expect(screen.getAllByText("1 verified evidence reference").length).toBeGreaterThanOrEqual(1);
  });

  it("renders unknown prompt sections when the production pack has empty sections", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.promptsPreview)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...promptPreviewPayload,
                production_pack: {
                  ...promptPreviewPayload.production_pack,
                  image_prompt: {
                    ...promptPreviewPayload.production_pack.image_prompt,
                    items: [],
                  },
                },
              }),
            ),
          );
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/prompts"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Prompt Packs" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview prompt pack" }));

    expect(await screen.findByRole("heading", { name: "Production Pack" })).toBeInTheDocument();
    expect(screen.getByText("Unknown.")).toBeInTheDocument();
  });

  it("clears stale production packs when local AI JSON validation fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/prompts"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Prompt Packs" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview prompt pack" }));
    expect(await screen.findByRole("heading", { name: "Production Pack" })).toBeInTheDocument();

    await user.clear(screen.getByLabelText("AI response JSON"));
    await user.type(screen.getByLabelText("AI response JSON"), "not json");
    await user.click(screen.getByRole("button", { name: "Preview prompt pack" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("AI response must be valid JSON.");
    expect(screen.queryByRole("heading", { name: "Production Pack" })).not.toBeInTheDocument();
  });

  it("clears stale production packs when a later preview fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    let failPreview = false;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.promptsPreview)) {
          if (failPreview) {
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  error: "prompt_preview_failed",
                  detail: "Prompt preview failed.",
                }),
                { status: 400 },
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify(promptPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/prompts"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Prompt Packs" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview prompt pack" }));
    expect(await screen.findByRole("heading", { name: "Production Pack" })).toBeInTheDocument();

    failPreview = true;
    await user.click(screen.getByRole("button", { name: "Preview prompt pack" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Prompt preview failed.");
    expect(screen.queryByRole("heading", { name: "Production Pack" })).not.toBeInTheDocument();
  });

  it("previews serialized exports from the exports workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/exports"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Exports" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.selectOptions(screen.getByLabelText("Export"), "production_pack:markdown");
    await user.clear(screen.getByLabelText("Character IDs"));
    await user.type(screen.getByLabelText("Character IDs"), "character_mark");
    await user.click(screen.getByRole("button", { name: "Preview export" }));

    expect(
      await screen.findByRole("heading", { name: "source_alpha_production_pack.md" }),
    ).toBeInTheDocument();
    expect(screen.getByText("production_pack")).toBeInTheDocument();
    expect(screen.getByText("markdown")).toBeInTheDocument();
    expect(screen.getByText("text/markdown; charset=utf-8")).toBeInTheDocument();
    expect(
      screen.getAllByText(/Generate this image using only accepted Aevryn canon/u).length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("creates stored snapshot exports from the exports workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    const fetchMock = vi.mocked(fetch);

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/exports"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Stored Exports" })).toBeInTheDocument();
    expect(await screen.findByText("alpha-canon-snapshot.json")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Create snapshot export" }));

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([input, init]) => {
          if (!String(input).endsWith(`${API_PATHS.projects}/project_alpha/exports`)) {
            return false;
          }
          if (init?.method !== "POST") {
            return false;
          }
          const body = JSON.parse(String(init.body));
          return (
            body.snapshot_id === "snapshot_run_alpha_canon" &&
            body.export_format === "json" &&
            body.filename === "alpha-canon-snapshot.json"
          );
        }),
      ).toBe(true);
    });
    expect(await screen.findByText("Snapshot export created.")).toBeInTheDocument();
  });

  it("clears stale export previews when local AI JSON validation fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/exports"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Exports" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview export" }));
    expect(
      await screen.findByRole("heading", { name: "source_alpha_production_pack.md" }),
    ).toBeInTheDocument();

    await user.clear(screen.getByLabelText("AI response JSON"));
    await user.type(screen.getByLabelText("AI response JSON"), "not json");
    await user.click(screen.getByRole("button", { name: "Preview export" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("AI response must be valid JSON.");
    expect(
      screen.queryByRole("heading", { name: "source_alpha_production_pack.md" }),
    ).not.toBeInTheDocument();
  });

  it("clears stale export previews when a later preview fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    let failPreview = false;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.exportsPreview)) {
          if (failPreview) {
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  error: "export_preview_failed",
                  detail: "Export preview failed.",
                }),
                { status: 400 },
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify(exportPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/exports"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Exports" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview export" }));
    expect(
      await screen.findByRole("heading", { name: "source_alpha_production_pack.md" }),
    ).toBeInTheDocument();

    failPreview = true;
    await user.click(screen.getByRole("button", { name: "Preview export" }));

    expect(await screen.findByText("Export preview failed.")).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "source_alpha_production_pack.md" }),
    ).not.toBeInTheDocument();
  });

  it("clears stale export API errors before showing local validation errors", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.exportsPreview)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                error: "export_preview_failed",
                detail: "Export preview failed.",
              }),
              { status: 400 },
            ),
          );
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/exports"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Exports" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview export" }));
    expect(await screen.findByText("Export preview failed.")).toBeInTheDocument();

    await user.clear(screen.getByLabelText("AI response JSON"));
    await user.type(screen.getByLabelText("AI response JSON"), "not json");
    await user.click(screen.getByRole("button", { name: "Preview export" }));

    expect(await screen.findByText("AI response must be valid JSON.")).toBeInTheDocument();
    expect(screen.queryByText("Export preview failed.")).not.toBeInTheDocument();
  });

  it("renders an empty state when the continuity preview has no scenes", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.continuityPreview)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...continuityPreviewPayload,
                continuity_report: {
                  ...continuityPreviewPayload.continuity_report,
                  scenes: [],
                },
              }),
            ),
          );
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/continuity"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Continuity" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview continuity" }));

    expect(
      await screen.findByRole("heading", { name: "No continuity scenes" }),
    ).toBeInTheDocument();
  });

  it("clears stale continuity reports when local AI JSON validation fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/continuity"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Continuity" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview continuity" }));
    expect(await screen.findByRole("heading", { name: "Continuity Report" })).toBeInTheDocument();

    await user.clear(screen.getByLabelText("AI response JSON"));
    await user.type(screen.getByLabelText("AI response JSON"), "not json");
    await user.click(screen.getByRole("button", { name: "Preview continuity" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("AI response must be valid JSON.");
    expect(screen.queryByRole("heading", { name: "Continuity Report" })).not.toBeInTheDocument();
  });

  it("clears stale continuity reports when a later preview fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    let failPreview = false;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.continuityPreview)) {
          if (failPreview) {
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  error: "continuity_preview_failed",
                  detail: "Continuity preview failed.",
                }),
                { status: 400 },
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify(continuityPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/continuity"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Continuity" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview continuity" }));
    expect(await screen.findByRole("heading", { name: "Continuity Report" })).toBeInTheDocument();

    failPreview = true;
    await user.click(screen.getByRole("button", { name: "Preview continuity" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Continuity preview failed.");
    expect(screen.queryByRole("heading", { name: "Continuity Report" })).not.toBeInTheDocument();
  });

  it("clears stale scene sheets when local AI JSON validation fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/scenes"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Scenes" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview scene" }));
    expect(await screen.findByRole("heading", { name: "Scene 7" })).toBeInTheDocument();

    await user.clear(screen.getByLabelText("AI response JSON"));
    await user.type(screen.getByLabelText("AI response JSON"), "not json");
    await user.click(screen.getByRole("button", { name: "Preview scene" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("AI response must be valid JSON.");
    expect(screen.queryByRole("heading", { name: "Scene 7" })).not.toBeInTheDocument();
  });

  it("renders unknown scene sections when the scene sheet has empty sections", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.scenesPreview)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...scenePreviewPayload,
                scene_sheet: {
                  ...scenePreviewPayload.scene_sheet,
                  location: { title: "Location", items: [] },
                  visual_highlights: { title: "Visual Highlights", items: [] },
                },
              }),
            ),
          );
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/scenes"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Scenes" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview scene" }));

    expect(await screen.findByRole("heading", { name: "Scene 7" })).toBeInTheDocument();
    expect(screen.getAllByText("Unknown").length).toBeGreaterThanOrEqual(2);
  });

  it("clears stale scene sheets when a later preview fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    let failPreview = false;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.scenesPreview)) {
          if (failPreview) {
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  error: "scene_preview_failed",
                  detail: "Unknown scene: source_alpha_scene_missing",
                }),
                { status: 400 },
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify(scenePreviewPayload)));
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/scenes"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Scenes" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview scene" }));
    expect(await screen.findByRole("heading", { name: "Scene 7" })).toBeInTheDocument();

    failPreview = true;
    await user.clear(screen.getByLabelText("Scene ID"));
    await user.type(screen.getByLabelText("Scene ID"), "source_alpha_scene_missing");
    await user.click(screen.getByRole("button", { name: "Preview scene" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unknown scene: source_alpha_scene_missing",
    );
    expect(screen.queryByRole("heading", { name: "Scene 7" })).not.toBeInTheDocument();
  });

  it("clears stale timeline previews when local AI JSON validation fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/timeline"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Timeline" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview timeline" }));
    expect(await screen.findByRole("heading", { name: "Timeline Order" })).toBeInTheDocument();

    await user.clear(screen.getByLabelText("AI response JSON"));
    await user.type(screen.getByLabelText("AI response JSON"), "not json");
    await user.click(screen.getByRole("button", { name: "Preview timeline" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("AI response must be valid JSON.");
    expect(screen.queryByRole("heading", { name: "Timeline Order" })).not.toBeInTheDocument();
  });

  it("renders an empty state when the timeline preview has no scene order", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.timelinePreview)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...timelinePreviewPayload,
                scene_map: [],
                accepted_state_change_ids: [],
              }),
            ),
          );
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/timeline"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Timeline" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview timeline" }));

    expect(await screen.findByRole("heading", { name: "No timeline scenes" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "No state changes" })).toBeInTheDocument();
  });

  it("clears stale timeline previews when a later preview fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    let failPreview = false;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.timelinePreview)) {
          if (failPreview) {
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  error: "timeline_preview_failed",
                  detail: "Unknown scene: source_alpha_scene_missing",
                }),
                { status: 400 },
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify(timelinePreviewPayload)));
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/timeline"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Timeline" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview timeline" }));
    expect(await screen.findByRole("heading", { name: "Timeline Order" })).toBeInTheDocument();

    failPreview = true;
    await user.clear(screen.getByLabelText("Scene ID"));
    await user.type(screen.getByLabelText("Scene ID"), "source_alpha_scene_missing");
    await user.click(screen.getByRole("button", { name: "Preview timeline" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unknown scene: source_alpha_scene_missing",
    );
    expect(screen.queryByRole("heading", { name: "Timeline Order" })).not.toBeInTheDocument();
  });

  it("clears stale world sheets when local AI JSON validation fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/world"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "World" })).toBeInTheDocument();
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview world" }));
    expect(await screen.findByRole("heading", { name: "World Sheet" })).toBeInTheDocument();

    await user.clear(screen.getByLabelText("AI response JSON"));
    await user.type(screen.getByLabelText("AI response JSON"), "not json");
    await user.click(screen.getByRole("button", { name: "Preview world" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("AI response must be valid JSON.");
    expect(screen.queryByRole("heading", { name: "World Sheet" })).not.toBeInTheDocument();
  });

  it("renders an empty state when the world preview has no entity sections", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.worldPreview)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...worldPreviewPayload,
                world_sheet: { ...worldPreviewPayload.world_sheet, entity_sections: [] },
              }),
            ),
          );
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/world"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "World" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview world" }));

    expect(await screen.findByRole("heading", { name: "No world entities" })).toBeInTheDocument();
  });

  it("clears stale world sheets when a later preview fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    let failPreview = false;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.worldPreview)) {
          if (failPreview) {
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  error: "world_preview_failed",
                  detail: "Unknown world entity: location_missing",
                }),
                { status: 400 },
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify(worldPreviewPayload)));
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/world"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "World" });
    await user.click(screen.getByText("Developer preview"));
    await user.click(screen.getByRole("button", { name: "Preview world" }));
    expect(await screen.findByRole("heading", { name: "World Sheet" })).toBeInTheDocument();

    failPreview = true;
    await user.clear(screen.getByLabelText("World entity IDs"));
    await user.type(screen.getByLabelText("World entity IDs"), "location_missing");
    await user.click(screen.getByRole("button", { name: "Preview world" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unknown world entity: location_missing",
    );
    expect(screen.queryByRole("heading", { name: "World Sheet" })).not.toBeInTheDocument();
  });

  it("clears stale import structure when a later inspection fails", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    let failImport = false;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        if (url.endsWith(API_PATHS.importsInspect)) {
          if (failImport) {
            return Promise.resolve(
              new Response(
                JSON.stringify({ error: "import_failed", detail: "Import inspection failed." }),
                { status: 400 },
              ),
            );
          }
          return Promise.resolve(new Response(JSON.stringify(importInspectPayload)));
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByText(".txt");
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.click(screen.getByRole("button", { name: "Inspect import" }));
    expect(await screen.findByRole("heading", { name: "Import Structure" })).toBeInTheDocument();

    failImport = true;
    await user.clear(screen.getByLabelText("Filename"));
    await user.type(screen.getByLabelText("Filename"), "chapter.txt");
    await user.click(screen.getByRole("button", { name: "Inspect import" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Import inspection failed.");
    expect(screen.queryByRole("heading", { name: "Import Structure" })).not.toBeInTheDocument();
  });

  it("shows source text character counts and blocks oversized pasted imports", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("0 / 500,000 characters")).toBeInTheDocument();
    await user.click(screen.getByLabelText("Source text"));
    await user.paste("a".repeat(MAX_IMPORT_SOURCE_CHARACTERS + 1));

    expect(await screen.findByText("500,001 / 500,000 characters")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Inspect import" })).toBeDisabled();
  });

  it("shows source-format API failures on the import workspace tab", async () => {
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({ error: "source_formats_failed", detail: "Formats unavailable." }),
              { status: 503 },
            ),
          );
        }
        if (url.endsWith(API_PATHS.health)) {
          return Promise.resolve(new Response(JSON.stringify(healthPayload)));
        }
        if (url.endsWith(API_PATHS.capabilities)) {
          return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("Formats unavailable.");
  });

  it("blocks deferred source formats before import inspection", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith(API_PATHS.sourceFormats)) {
        return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
      }
      if (url.endsWith(API_PATHS.importsInspect)) {
        return Promise.resolve(new Response(JSON.stringify(importInspectPayload)));
      }
      if (url.endsWith(API_PATHS.health)) {
        return Promise.resolve(new Response(JSON.stringify(healthPayload)));
      }
      if (url.endsWith(API_PATHS.capabilities)) {
        return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText(".pdf")).toBeInTheDocument();
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    const deferredInputs = [
      {
        filename: "chapter.pdf",
        message:
          ".pdf import is deferred. Requires deterministic PDF reading-order parser support.",
      },
      {
        filename: "chapter.mobi",
        message: ".mobi import is deferred. Requires dedicated Kindle parser support.",
      },
      {
        filename: "chapter.azw3",
        message: ".azw3 import is deferred. Requires dedicated Kindle parser support.",
      },
    ];

    for (const deferredInput of deferredInputs) {
      await user.clear(screen.getByLabelText("Filename"));
      await user.type(screen.getByLabelText("Filename"), deferredInput.filename);
      await user.click(screen.getByRole("button", { name: "Inspect import" }));

      expect(await screen.findByRole("alert")).toHaveTextContent(deferredInput.message);
      expect(screen.queryByRole("heading", { name: "Import Structure" })).not.toBeInTheDocument();
    }
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining(API_PATHS.importsInspect),
      expect.anything(),
    );
  });

  it("renders a controlled empty state for unknown workspace tabs", async () => {
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    window.localStorage.setItem(
      "aevryn.projects",
      JSON.stringify([
        {
          id: "project_alpha",
          name: "Alpha",
          updatedAt: "2026-06-27T00:00:00.000Z",
        },
      ]),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/not-a-tab"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Unknown workspace section")).toBeInTheDocument();
    expect(
      screen.getByText("This project exists, but that workspace section is not available."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Web Alpha Shell/)).not.toBeInTheDocument();
  });

  it("loads and saves project settings from the settings workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/settings"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Settings Areas" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Project Defaults/u })).toHaveAttribute(
      "href",
      "#project-settings",
    );
    expect(screen.getByRole("heading", { name: "Workspace Preferences" })).toBeInTheDocument();
    const accountPanel = screen.getByRole("heading", { name: "Account" }).closest("section");
    expect(accountPanel).not.toBeNull();
    expect(screen.getByRole("heading", { name: "Privacy & Data" })).toBeInTheDocument();
    expect(within(accountPanel as HTMLElement).getByText("Demo User")).toBeInTheDocument();
    expect(within(accountPanel as HTMLElement).getByText("demo@example.com")).toBeInTheDocument();
    expect(within(accountPanel as HTMLElement).getByText("Managed identity provider")).toBeInTheDocument();
    expect(
      screen.getByText("Off by default. Opt-in only. No live training pipeline is active."),
    ).toBeInTheDocument();
    expect(screen.getByText(/does not give Aevryn ownership/u)).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent("session-token");
    expect(await screen.findByDisplayValue("en-US")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Default export format"), "json");
    await user.clear(screen.getByLabelText("Locale"));
    await user.type(screen.getByLabelText("Locale"), "en-GB");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(await screen.findByRole("status")).toHaveTextContent("Settings saved.");
  });

  it("loads and creates stories from the story workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/story"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Story" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "No stories yet" })).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Story title"));
    await user.type(screen.getByLabelText("Story title"), " Alpha   Story ");
    await user.click(screen.getByRole("button", { name: "Create story" }));

    expect(await screen.findByText("Alpha Story")).toBeInTheDocument();
  });

  it("selects and deletes stories from the story workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    const betaStory = {
      ...storyAlphaPayload,
      story_id: "story_beta",
      title: "Beta Story",
    };
    let stories = [storyAlphaPayload, betaStory];
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith(API_PATHS.health)) {
        return Promise.resolve(new Response(JSON.stringify(healthPayload)));
      }
      if (url.endsWith(API_PATHS.capabilities)) {
        return Promise.resolve(new Response(JSON.stringify(capabilitiesPayload)));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}`)) {
        return Promise.resolve(new Response(JSON.stringify(projectAlphaPayload)));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories`)) {
        return Promise.resolve(new Response(JSON.stringify({ stories })));
      }
      if (
        url.endsWith(
          `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/story_beta`,
        ) &&
        init?.method === "DELETE"
      ) {
        stories = stories.filter((story) => story.story_id !== "story_beta");
        return Promise.resolve(new Response(null, { status: 204 }));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/runs`)) {
        return Promise.resolve(new Response(JSON.stringify({ runs: [] })));
      }
      if (url.endsWith(`${API_PATHS.projects}/${projectAlphaPayload.project_id}/status`)) {
        return Promise.resolve(new Response(JSON.stringify(projectStatusPayload)));
      }
      if (url.endsWith(projectOutputsPath(projectAlphaPayload.project_id))) {
        return Promise.resolve(new Response(JSON.stringify(projectOutputsPayload)));
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/story"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Alpha Story")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Beta Story Select story/ }));

    expect(window.localStorage.getItem("aevryn.activeStory.project_alpha")).toBe("story_beta");
    await user.click(screen.getByRole("button", { name: "Delete Beta Story" }));

    expect(confirmSpy).toHaveBeenNthCalledWith(1, "Delete project Beta Story?");
    expect(confirmSpy).toHaveBeenNthCalledWith(2, "Story data will be lost forever, are you sure?");
    expect(await screen.findByText("Alpha Story")).toBeInTheDocument();
    expect(screen.queryByText("Beta Story")).not.toBeInTheDocument();
    expect(window.localStorage.getItem("aevryn.activeStory.project_alpha")).toBe("story_alpha");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(`${API_PATHS.projects}/project_alpha/stories/story_beta`),
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});

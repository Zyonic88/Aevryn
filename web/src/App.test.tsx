import { render, screen, waitFor } from "@testing-library/react";
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
        items: ["condition: Alarm active", "ownership: Academy"],
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
        still_known: [],
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
      status: { title: "Status", items: ["Alive"] },
      current_goal: { title: "Current Goal", items: ["Find the fortress"] },
      current_equipment: { title: "Current Equipment", items: ["Rusty Dagger"] },
      current_abilities: { title: "Current Abilities", items: ["Tracking"] },
      current_assets: { title: "Current Assets", items: [] },
      territory: { title: "Territory", items: [] },
      relationships: { title: "Relationships", items: ["Luna - Ally"] },
      current_limitations: { title: "Current Limitations", items: ["Injured arm"] },
      recent_changes: { title: "Recent Changes", items: ["Equipped Rusty Dagger"] },
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
  serialized_output: "{\"source_id\":\"source_alpha\"}",
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

function storeAuthenticatedProject() {
  window.localStorage.setItem("aevryn.session", JSON.stringify(session));
  window.localStorage.setItem("aevryn.projects", JSON.stringify([projectAlpha]));
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
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/snapshots?snapshot_kind=canon`,
          )
        ) {
          return Promise.resolve(new Response(JSON.stringify({ snapshots: [] })));
        }
        if (
          url.endsWith(
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports/${importRecordPayload.import_id}/runs`,
          )
        ) {
          const body = JSON.parse(String(init?.body));
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...engineRunPayload,
                run_id: body.run_id,
                job_ref: `queue://${body.job_id}`,
                started_at: body.now,
                status_updated_at: body.now,
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
    vi.restoreAllMocks();
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
  });

  it("logs in through the auth API and stores the returned session", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <App />
      </MemoryRouter>,
    );

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

    await user.clear(screen.getByLabelText("Password"));
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

  it("redirects missing project shells to the dashboard", async () => {
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
    expect(screen.getByRole("link", { name: "Monitoring" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(await screen.findByRole("region", { name: "API health" })).toHaveTextContent("ok");
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
      "snapshot_run_alpha_canon",
    );
    expect(screen.getByRole("region", { name: "Export availability" })).toHaveTextContent(
      "export_alpha",
    );
    expect(screen.getByRole("region", { name: "Recent workflow events" })).toHaveTextContent(
      "Created markdown canon export.",
    );
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
    expect(screen.queryByRole("region", { name: "Recent workflow events" })).not.toBeInTheDocument();
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

  it("renders dashboard loading states as status messages", async () => {
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
    expect(statuses).toHaveLength(3);
    expect(statuses[0]).toHaveTextContent("Checking API health.");
    expect(statuses[1]).toHaveTextContent("Loading capabilities.");
    expect(statuses[2]).toHaveTextContent("Loading projects.");
  });

  it("renders dashboard API errors as alerts", async () => {
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

    expect(await screen.findByRole("alert")).toHaveTextContent("Health check failed.");
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
    await user.click(screen.getByRole("button", { name: "Create shell" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Project storage failed.");
    expect(screen.queryByRole("link", { name: /Temporary Project/ })).not.toBeInTheDocument();
  });

  it("creates and opens a project shell", async () => {
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
    await user.click(screen.getByRole("button", { name: "Create shell" }));
    await user.click(await screen.findByRole("link", { name: /Test Novel/ }));

    expect(await screen.findByRole("heading", { name: "Test Novel" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Characters" })).toBeInTheDocument();
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

    expect(screen.getByRole("button", { name: "Create shell" })).toBeDisabled();
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
    expect(screen.getByText("Showing first 6 of 8 scenes.")).toBeInTheDocument();
    expect(screen.getByText("source_alpha_chapter_001_scene_001")).toBeInTheDocument();
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
    expect(screen.getByLabelText("Source file")).toHaveAttribute(
      "accept",
      ".txt,.md,.markdown,.html,.htm,.xhtml,.fb2,.docx,.odt,.epub",
    );

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
      await user.upload(
        screen.getByLabelText("Source file"),
        new File([content], upload.filename),
      );
      await waitFor(() =>
        expect(screen.getByText(new RegExp(upload.filename, "u"))).toBeInTheDocument(),
      );
      await user.click(screen.getByRole("button", { name: "Inspect import" }));
      await waitFor(() => expect(inspectBodies).toHaveLength(index + 1));

      expect(inspectBodies[index]).toMatchObject({
        filename: upload.filename,
        source_id: upload.sourceId,
      });
      expect(atob(inspectBodies[index].content_base64)).toBe(content);
    }

    expect(await screen.findByRole("heading", { name: "Import Structure" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(API_PATHS.importsInspect),
      expect.anything(),
    );
  });

  it("saves import metadata from the import workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
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
          return Promise.resolve(new Response(JSON.stringify({ runs: [] })));
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
            `${API_PATHS.projects}/${projectAlphaPayload.project_id}/stories/${storyAlphaPayload.story_id}/imports/${importRecordPayload.import_id}/runs`,
          )
        ) {
          const body = JSON.parse(String(init?.body));
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...engineRunPayload,
                run_id: body.run_id,
                job_ref: `queue://${body.job_id}`,
                started_at: body.now,
                status_updated_at: body.now,
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
    await user.clear(screen.getByLabelText("Import ID"));
    await user.type(screen.getByLabelText("Import ID"), "import_alpha");
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.click(screen.getByRole("button", { name: "Inspect import" }));
    await user.click(await screen.findByRole("button", { name: "Save import metadata" }));

    expect(
      await screen.findByText("Saved import_alpha for durable project storage."),
    ).toBeInTheDocument();
    expect(screen.getByText("chapter_001.txt")).toBeInTheDocument();
    expect(screen.getByText("import_alpha / 8 scenes")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Submit processing" }));

    expect(await screen.findByText(/Submitted import_alpha_run_/u)).toBeInTheDocument();
    expect(await screen.findByText(/pending \/ import_alpha/u)).toBeInTheDocument();
  });

  it("shows persisted imports runs and snapshot availability after refresh", async () => {
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
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
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

    expect(await screen.findByRole("heading", { name: "Saved Imports" })).toBeInTheDocument();
    expect(await screen.findByText("chapter_001.txt")).toBeInTheDocument();
    expect(screen.getByText("import_alpha / 8 scenes")).toBeInTheDocument();
    expect(await screen.findByText("succeeded / import_alpha")).toBeInTheDocument();
    expect(screen.getByText("Canon snapshot: snapshot_run_alpha_canon")).toBeInTheDocument();
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
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("failed / import_alpha")).toBeInTheDocument();
    expect(screen.getByText("No snapshot: run failed")).toBeInTheDocument();
    expect(
      screen.getByText("Run error: Parser could not read chapter content."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Canon snapshot: snapshot_run_alpha_canon")).not.toBeInTheDocument();
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
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.clear(screen.getByLabelText("Character IDs"));
    await user.type(screen.getByLabelText("Character IDs"), "character_mark");
    await user.click(screen.getByRole("button", { name: "Preview characters" }));

    expect(await screen.findByRole("heading", { name: "Character Profiles" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Mark" })).toBeInTheDocument();
    expect(screen.getByText("Rusty Dagger")).toBeInTheDocument();
    expect(screen.getByText("Luna - Ally")).toBeInTheDocument();
    expect(screen.getByText("3 verified facts")).toBeInTheDocument();
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
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/characters"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Characters" });
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
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}The hangar was quiet.");
    await user.clear(screen.getByLabelText("World entity IDs"));
    await user.type(screen.getByLabelText("World entity IDs"), "location_hangar");
    await user.click(screen.getByRole("button", { name: "Preview world" }));

    expect(await screen.findByRole("heading", { name: "World Sheet" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Hangar (location)" })).toBeInTheDocument();
    expect(screen.getByText("condition: Alarm active")).toBeInTheDocument();
    expect(screen.getByText("ownership: Academy")).toBeInTheDocument();
    expect(screen.getByText("2 verified world facts")).toBeInTheDocument();
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
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.click(screen.getByRole("button", { name: "Preview timeline" }));

    expect(await screen.findByRole("heading", { name: "Timeline Order" })).toBeInTheDocument();
    expect(screen.getByText("source_alpha_chapter_001_scene_001")).toBeInTheDocument();
    expect(screen.getByText("source_alpha_chapter_002_scene_001")).toBeInTheDocument();
    expect(screen.getByText("Current")).toBeInTheDocument();
    expect(
      screen.getByText("state_fact_character_mark_current_weapon_iron_sword"),
    ).toBeInTheDocument();
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
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.clear(screen.getByLabelText("Character IDs"));
    await user.type(screen.getByLabelText("Character IDs"), "character_mark");
    await user.click(screen.getByRole("button", { name: "Preview scene" }));

    expect(await screen.findByRole("heading", { name: "Scene 7" })).toBeInTheDocument();
    expect(screen.getByText("Chapter 1 for source_alpha_chapter_001_scene_001.")).toBeInTheDocument();
    expect(screen.getByText("Hangar")).toBeInTheDocument();
    expect(screen.getByText("Mark")).toBeInTheDocument();
    expect(screen.getByText("Mark equipped Rusty Dagger")).toBeInTheDocument();
    expect(screen.getByText("1 verified evidence reference")).toBeInTheDocument();
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
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.click(screen.getByRole("button", { name: "Preview continuity" }));

    expect(await screen.findByRole("heading", { name: "Continuity Report" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "source_alpha_chapter_001_scene_001" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "source_alpha_chapter_002_scene_001" })).toBeInTheDocument();
    expect(
      screen.getAllByText((_content, element) => {
        return element?.tagName === "LI" && element.textContent?.includes("character_mark current_weapon = Rusty Dagger.");
      }),
    ).toHaveLength(2);
    expect(
      screen.getByText((_content, element) => {
        return element?.tagName === "LI" && element.textContent?.includes("character_mark current_weapon = Iron Sword.");
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/source_alpha_anchor_002/u)).toBeInTheDocument();
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
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.clear(screen.getByLabelText("Character IDs"));
    await user.type(screen.getByLabelText("Character IDs"), "character_mark");
    await user.click(screen.getByRole("button", { name: "Preview prompt pack" }));

    expect(await screen.findByRole("heading", { name: "Production Pack" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Image Prompt" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Narration Prompt" })).toBeInTheDocument();
    expect(screen.getByText("Generate this image using only accepted Aevryn canon.")).toBeInTheDocument();
    expect(screen.getByText("Scene Summary: Mark prepares in the hangar.")).toBeInTheDocument();
    expect(screen.getByText("Chapter 1 / source_alpha_chapter_001_scene_001")).toBeInTheDocument();
    expect(screen.getByText("1 verified evidence reference")).toBeInTheDocument();
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
    await user.click(screen.getByRole("button", { name: "Preview prompt pack" }));

    expect(await screen.findByRole("heading", { name: "Production Pack" })).toBeInTheDocument();
    expect(screen.getByText("Unknown")).toBeInTheDocument();
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
    await user.clear(screen.getByLabelText("Source text"));
    await user.type(screen.getByLabelText("Source text"), "Chapter 1{enter}Mark carried a dagger.");
    await user.selectOptions(screen.getByLabelText("Export"), "production_pack:markdown");
    await user.clear(screen.getByLabelText("Character IDs"));
    await user.type(screen.getByLabelText("Character IDs"), "character_mark");
    await user.click(screen.getByRole("button", { name: "Preview export" }));

    expect(await screen.findByRole("heading", { name: "source_alpha_production_pack.md" })).toBeInTheDocument();
    expect(screen.getByText("production_pack")).toBeInTheDocument();
    expect(screen.getByText("markdown")).toBeInTheDocument();
    expect(screen.getByText("text/markdown; charset=utf-8")).toBeInTheDocument();
    expect(screen.getByText(/Generate this image using only accepted Aevryn canon/u)).toBeInTheDocument();
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
    await user.click(screen.getByRole("button", { name: "Preview export" }));
    expect(await screen.findByRole("heading", { name: "source_alpha_production_pack.md" })).toBeInTheDocument();

    await user.clear(screen.getByLabelText("AI response JSON"));
    await user.type(screen.getByLabelText("AI response JSON"), "not json");
    await user.click(screen.getByRole("button", { name: "Preview export" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("AI response must be valid JSON.");
    expect(screen.queryByRole("heading", { name: "source_alpha_production_pack.md" })).not.toBeInTheDocument();
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
    await user.click(screen.getByRole("button", { name: "Preview export" }));
    expect(await screen.findByRole("heading", { name: "source_alpha_production_pack.md" })).toBeInTheDocument();

    failPreview = true;
    await user.click(screen.getByRole("button", { name: "Preview export" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Export preview failed.");
    expect(screen.queryByRole("heading", { name: "source_alpha_production_pack.md" })).not.toBeInTheDocument();
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
    await user.click(screen.getByRole("button", { name: "Preview export" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Export preview failed.");

    await user.clear(screen.getByLabelText("AI response JSON"));
    await user.type(screen.getByLabelText("AI response JSON"), "not json");
    await user.click(screen.getByRole("button", { name: "Preview export" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("AI response must be valid JSON.");
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
    await user.click(screen.getByRole("button", { name: "Preview continuity" }));

    expect(await screen.findByRole("heading", { name: "No continuity scenes" })).toBeInTheDocument();
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

    expect(await screen.findByText("10 / 500,000 characters")).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Source text"));
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
    vi.stubGlobal(
      "fetch",
      fetchMock,
    );

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText(".pdf")).toBeInTheDocument();
    const deferredInputs = [
      {
        filename: "chapter.pdf",
        message: ".pdf import is deferred. Requires deterministic PDF reading-order parser support.",
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
    expect(await screen.findByDisplayValue("en-US")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Default export format"), "json");
    await user.clear(screen.getByLabelText("Locale"));
    await user.type(screen.getByLabelText("Locale"), "en-GB");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Settings saved for project_alpha.",
    );
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
});

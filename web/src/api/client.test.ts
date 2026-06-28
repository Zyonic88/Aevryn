import { describe, expect, it, vi } from "vitest";

import { AevrynApiClient, API_PATHS } from "./client";

const healthPayload = {
  status: "ok",
  api_version: "2.0",
  engine: "Aevryn",
};

const sessionPayload = {
  user_id: "user_demo",
  email: "demo@example.com",
  display_name: "Demo User",
  session_token: "session-token",
  expires_at: "2026-06-27T00:00:00.000Z",
};
const projectPayload = {
  project_id: "project_alpha",
  name: "Alpha",
  created_at: "2026-06-27T00:00:00.000Z",
  updated_at: "2026-06-27T00:00:00.000Z",
};
const projectSettingsPayload = {
  project_id: "project_alpha",
  default_export_format: "markdown",
  locale: "en-US",
};
const storyPayload = {
  story_id: "story_alpha",
  project_id: "project_alpha",
  title: "Alpha",
  created_at: "2026-06-27T00:00:00.000Z",
  updated_at: "2026-06-27T00:00:00.000Z",
};
const importRecordPayload = {
  import_id: "import_alpha",
  story_id: "story_alpha",
  source_id: "source_alpha",
  filename: "chapter_001.txt",
  source_format: "txt",
  storage_ref: "api_import://story_alpha/import_alpha",
  chapter_count: 1,
  scene_count: 1,
  evidence_anchor_count: 1,
  created_at: "2026-06-27T00:00:00.000Z",
};
const engineRunPayload = {
  run_id: "run_alpha",
  project_id: "project_alpha",
  story_id: "story_alpha",
  import_id: "import_alpha",
  status: "pending",
  engine_version: "aevryn_v1",
  started_at: "2026-06-27T00:00:00.000Z",
  status_updated_at: "2026-06-27T00:00:00.000Z",
  finished_at: null,
  error_summary: "",
  job_ref: "queue://job_alpha",
};
const snapshotPayload = {
  snapshot_id: "snapshot_alpha",
  project_id: "project_alpha",
  story_id: "story_alpha",
  run_id: "run_alpha",
  snapshot_kind: "character_profile",
  content_type: "application/json",
  serialized_output: '{"character_id":"character_mark"}',
  created_at: "2026-06-27T00:30:00.000Z",
};
const projectStatusPayload = {
  project_id: "project_alpha",
  status: "succeeded",
  story_count: 1,
  import_count: 1,
  run_count: 1,
  latest_import: {
    import_id: "import_alpha",
    story_id: "story_alpha",
    filename: "chapter_001.txt",
    source_format: "txt",
    created_at: "2026-06-27T00:00:00.000Z",
  },
  latest_engine_run: {
    run_id: "run_alpha",
    story_id: "story_alpha",
    import_id: "import_alpha",
    status: "succeeded",
    started_at: "2026-06-27T00:00:00.000Z",
    status_updated_at: "2026-06-27T00:30:00.000Z",
    finished_at: "2026-06-27T00:30:00.000Z",
    error_summary: "",
    job_ref: "queue://job_alpha",
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
    latest_snapshot_id: "snapshot_run_alpha_canon",
    latest_snapshot_kind: "canon",
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
      event_type: "snapshot_created",
      status: "succeeded",
      occurred_at: "2026-06-27T00:30:00.000Z",
      story_id: "story_alpha",
      import_id: "",
      run_id: "run_alpha",
      snapshot_id: "snapshot_run_alpha_canon",
      export_id: "",
      summary: "Created canon snapshot.",
    },
  ],
};
const sourceFormatsPayload = {
  supported: [
    {
      extension: ".txt",
      status: "supported",
      adapter: "plain_text",
      evidence_anchor_status: "preserved",
      notes: "Plain text import.",
    },
  ],
  deferred: [],
};

const importInspectPayload = {
  source_id: "api_demo",
  source_format: "txt",
  title: "API Demo",
  chapters: 1,
  chapter_ids: ["api_demo_chapter_001"],
  scenes: 1,
  scene_ids: ["api_demo_chapter_001_scene_001"],
  scene_map: [
    {
      chapter_id: "api_demo_chapter_001",
      chapter_index: 1,
      scene_id: "api_demo_chapter_001_scene_001",
      scene_index: 1,
      title: "Chapter 1",
    },
  ],
  paragraphs: 1,
  evidence_anchors: 1,
  first_evidence_anchors: [
    {
      anchor_id: "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
      chapter_id: "api_demo_chapter_001",
      scene_id: "api_demo_chapter_001_scene_001",
      paragraph_index: 1,
      sentence_index: 1,
    },
  ],
};

const worldPreviewPayload = {
  source_id: "api_demo",
  source_format: "txt",
  scene_id: "api_demo_chapter_002_scene_001",
  world_sheet: {
    chapter_label: "Chapter 2",
    entity_sections: [
      {
        title: "Hangar (location)",
        items: ["condition: Alarm active"],
      },
    ],
    evidence_summary: "1 verified world fact",
  },
};

const characterPreviewPayload = {
  source_id: "api_demo",
  source_format: "txt",
  scene_id: "api_demo_chapter_001_scene_001",
  character_profiles: [
    {
      character_id: "character_mark",
      display_name: "Mark",
      subtitle: "Known character",
      status: { title: "Status", items: ["Alive"] },
      current_goal: { title: "Current Goal", items: ["Unknown"] },
      current_equipment: { title: "Current Equipment", items: ["Rusty Dagger"] },
      current_abilities: { title: "Current Abilities", items: [] },
      current_assets: { title: "Current Assets", items: [] },
      territory: { title: "Territory", items: [] },
      relationships: { title: "Relationships", items: [] },
      current_limitations: { title: "Current Limitations", items: [] },
      recent_changes: { title: "Recent Changes", items: ["Weapon established"] },
      evidence_summary: "1 verified fact",
    },
  ],
};

const timelinePreviewPayload = {
  source_id: "api_demo",
  source_format: "txt",
  current_scene_id: "api_demo_chapter_002_scene_001",
  chapter_ids: ["api_demo_chapter_001", "api_demo_chapter_002"],
  scene_map: [
    {
      chapter_id: "api_demo_chapter_001",
      chapter_index: 1,
      scene_id: "api_demo_chapter_001_scene_001",
      scene_index: 1,
      title: "Scene 1",
    },
    {
      chapter_id: "api_demo_chapter_002",
      chapter_index: 2,
      scene_id: "api_demo_chapter_002_scene_001",
      scene_index: 1,
      title: "Scene 1",
    },
  ],
  accepted_state_change_ids: ["state_fact_character_mark_current_weapon_iron_sword"],
};

const scenePreviewPayload = {
  source_id: "api_demo",
  source_format: "txt",
  scene_id: "api_demo_chapter_001_scene_001",
  scene_sheet: {
    scene_id: "api_demo_chapter_001_scene_001",
    title: "Scene 1",
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
  source_id: "api_demo",
  source_format: "txt",
  scene_id: "api_demo_chapter_001_scene_001",
  production_pack: {
    scene: scenePreviewPayload.scene_sheet,
    image_prompt: {
      title: "Image Prompt",
      items: ["Generate this image using only accepted Aevryn canon."],
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
  source_id: "api_demo",
  source_format: "txt",
  scene_id: "api_demo_chapter_001_scene_001",
  export_kind: "production_pack",
  export_format: "markdown",
  filename: "api_demo_production_pack.md",
  content_type: "text/markdown; charset=utf-8",
  content: "# Scene 1\n\n## Image Prompt\nGenerate this image using only accepted Aevryn canon.",
};

const continuityPreviewPayload = {
  source_id: "api_demo",
  source_format: "txt",
  continuity_report: {
    source_id: "api_demo",
    scenes: [
      {
        scene_id: "api_demo_chapter_001_scene_001",
        new: [
          {
            record_id: "fact_character_mark_current_weapon_rusty_dagger",
            record_type: "fact",
            description: "character_mark current_weapon = Rusty Dagger.",
            evidence_id: "anchor_001",
            chapter_id: "api_demo_chapter_001",
            scene_id: "api_demo_chapter_001_scene_001",
          },
        ],
        updated: [],
        still_known: [],
        invalidated: [],
      },
    ],
  },
};

describe("AevrynApiClient", () => {
  it("validates successful API responses", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(healthPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const baseUrl = "https://api.aevryn.ai";
    const client = new AevrynApiClient(`${baseUrl}/`);

    await expect(client.health()).resolves.toEqual(healthPayload);
    expect(fetchMock).toHaveBeenCalledWith(
      `${baseUrl}${API_PATHS.health}`,
      expect.objectContaining({ headers: expect.any(Headers) }),
    );
  });

  it("loads source formats", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(sourceFormatsPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");

    await expect(client.sourceFormats()).resolves.toEqual(sourceFormatsPayload);
    expect(fetchMock).toHaveBeenCalledWith(
      `https://api.aevryn.ai${API_PATHS.sourceFormats}`,
      expect.objectContaining({ headers: expect.any(Headers) }),
    );
  });

  it("sends JSON requests for import inspection", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(importInspectPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.inspectImport({
        source_id: "api_demo",
        filename: "chapter.txt",
        title: "API Demo",
        content_base64: "Q2hhcHRlciAx",
      }),
    ).resolves.toEqual(importInspectPayload);

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(fetchMock.mock.calls[0][0]).toBe(`https://api.aevryn.ai${API_PATHS.importsInspect}`);
    expect(init.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("sends JSON requests for world previews", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(worldPreviewPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.previewWorld({
        source_id: "api_demo",
        filename: "chapter.txt",
        title: "API Demo",
        content_base64: "Q2hhcHRlciAx",
        ai_response: { entities: [] },
        world_entity_ids: ["location_hangar"],
      }),
    ).resolves.toEqual(worldPreviewPayload);

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(fetchMock.mock.calls[0][0]).toBe(`https://api.aevryn.ai${API_PATHS.worldPreview}`);
    expect(init.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("sends JSON requests for character previews", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(characterPreviewPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.previewCharacters({
        source_id: "api_demo",
        filename: "chapter.txt",
        title: "API Demo",
        content_base64: "Q2hhcHRlciAx",
        ai_response: { entities: [] },
        character_ids: ["character_mark"],
      }),
    ).resolves.toEqual(characterPreviewPayload);

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(fetchMock.mock.calls[0][0]).toBe(`https://api.aevryn.ai${API_PATHS.charactersPreview}`);
    expect(init.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("sends JSON requests for timeline previews", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(timelinePreviewPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.previewTimeline({
        source_id: "api_demo",
        filename: "chapter.txt",
        title: "API Demo",
        content_base64: "Q2hhcHRlciAx",
        ai_response: { entities: [] },
      }),
    ).resolves.toEqual(timelinePreviewPayload);

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(fetchMock.mock.calls[0][0]).toBe(`https://api.aevryn.ai${API_PATHS.timelinePreview}`);
    expect(init.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("sends JSON requests for scene previews", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(scenePreviewPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.previewScene({
        source_id: "api_demo",
        filename: "chapter.txt",
        title: "API Demo",
        content_base64: "Q2hhcHRlciAx",
        ai_response: { entities: [] },
        character_ids: ["character_mark"],
      }),
    ).resolves.toEqual(scenePreviewPayload);

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(fetchMock.mock.calls[0][0]).toBe(`https://api.aevryn.ai${API_PATHS.scenesPreview}`);
    expect(init.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("sends JSON requests for prompt previews", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(promptPreviewPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.previewPrompts({
        source_id: "api_demo",
        filename: "chapter.txt",
        title: "API Demo",
        content_base64: "Q2hhcHRlciAx",
        ai_response: { entities: [] },
        character_ids: ["character_mark"],
      }),
    ).resolves.toEqual(promptPreviewPayload);

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(fetchMock.mock.calls[0][0]).toBe(`https://api.aevryn.ai${API_PATHS.promptsPreview}`);
    expect(init.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("sends JSON requests for export previews", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(exportPreviewPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.previewExport({
        source_id: "api_demo",
        filename: "chapter.txt",
        title: "API Demo",
        content_base64: "Q2hhcHRlciAx",
        ai_response: { entities: [] },
        character_ids: ["character_mark"],
        export_kind: "production_pack",
        export_format: "markdown",
      }),
    ).resolves.toEqual(exportPreviewPayload);

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(fetchMock.mock.calls[0][0]).toBe(`https://api.aevryn.ai${API_PATHS.exportsPreview}`);
    expect(init.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("sends JSON requests for continuity previews", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(continuityPreviewPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.previewContinuity({
        source_id: "api_demo",
        filename: "chapter.txt",
        title: "API Demo",
        content_base64: "Q2hhcHRlciAx",
        ai_response: { entities: [] },
      }),
    ).resolves.toEqual(continuityPreviewPayload);

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(fetchMock.mock.calls[0][0]).toBe(
      `https://api.aevryn.ai${API_PATHS.continuityPreview}`,
    );
    expect(init.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("sends JSON requests for authentication", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(sessionPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await client.login({
      email: "demo@example.com",
      password: "password",
      now: "2026-06-27T00:00:00.000Z",
    });

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(init.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("sends authenticated requests for durable projects", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ projects: [projectPayload] }), { status: 200 }),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify(projectPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(projectPayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.listProjects("session-token", "2026-06-27T00:00:00.000Z"),
    ).resolves.toEqual({
      projects: [projectPayload],
    });
    await expect(
      client.createProject(
        {
          project_id: "project_alpha",
          name: "Alpha",
          now: "2026-06-27T00:00:00.000Z",
        },
        "session-token",
        "2026-06-27T00:00:00.000Z",
      ),
    ).resolves.toEqual(projectPayload);
    await expect(
      client.getProject("project_alpha", "session-token", "2026-06-27T00:00:00.000Z"),
    ).resolves.toEqual(projectPayload);

    expect(fetchMock.mock.calls[0][0]).toBe(`https://api.aevryn.ai${API_PATHS.projects}`);
    expect(fetchMock.mock.calls[1][0]).toBe(`https://api.aevryn.ai${API_PATHS.projects}`);
    expect(fetchMock.mock.calls[1][1].method).toBe("POST");
    expect(fetchMock.mock.calls[2][0]).toBe(
      `https://api.aevryn.ai${API_PATHS.projects}/project_alpha`,
    );
    for (const [, init] of fetchMock.mock.calls) {
      const headers = init.headers as Headers;
      expect(headers.get("Authorization")).toBe("Bearer session-token");
      expect(headers.get("X-Aevryn-Now")).toBe("2026-06-27T00:00:00.000Z");
    }
  });

  it("sends authenticated requests for project settings", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(projectSettingsPayload), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ ...projectSettingsPayload, default_export_format: "json" }),
          { status: 200 },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.getProjectSettings(
        "project_alpha",
        "session-token",
        "2026-06-27T00:00:00.000Z",
      ),
    ).resolves.toEqual(projectSettingsPayload);
    await expect(
      client.updateProjectSettings(
        "project_alpha",
        { default_export_format: "json", locale: "en-US" },
        "session-token",
        "2026-06-27T00:00:00.000Z",
      ),
    ).resolves.toEqual({ ...projectSettingsPayload, default_export_format: "json" });

    for (const [input, init] of fetchMock.mock.calls) {
      expect(input).toBe(`https://api.aevryn.ai${API_PATHS.projects}/project_alpha/settings`);
      const headers = init.headers as Headers;
      expect(headers.get("Authorization")).toBe("Bearer session-token");
      expect(headers.get("X-Aevryn-Now")).toBe("2026-06-27T00:00:00.000Z");
    }
    expect(fetchMock.mock.calls[1][1].method).toBe("PUT");
  });

  it("sends authenticated requests for project stories", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ stories: [storyPayload] })))
      .mockResolvedValueOnce(new Response(JSON.stringify(storyPayload)));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.listStories("project_alpha", "session-token", "2026-06-27T00:00:00.000Z"),
    ).resolves.toEqual({ stories: [storyPayload] });
    await expect(
      client.createStory(
        "project_alpha",
        { story_id: "story_alpha", title: "Alpha", now: "2026-06-27T00:00:00.000Z" },
        "session-token",
        "2026-06-27T00:00:00.000Z",
      ),
    ).resolves.toEqual(storyPayload);

    for (const [input, init] of fetchMock.mock.calls) {
      expect(input).toBe(`https://api.aevryn.ai${API_PATHS.projects}/project_alpha/stories`);
      const headers = init.headers as Headers;
      expect(headers.get("Authorization")).toBe("Bearer session-token");
      expect(headers.get("X-Aevryn-Now")).toBe("2026-06-27T00:00:00.000Z");
    }
    expect(fetchMock.mock.calls[1][1].method).toBe("POST");
  });

  it("sends authenticated requests for story imports", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ imports: [importRecordPayload] })))
      .mockResolvedValueOnce(new Response(JSON.stringify(importRecordPayload)));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.listStoryImports(
        "project_alpha",
        "story_alpha",
        "session-token",
        "2026-06-27T00:00:00.000Z",
      ),
    ).resolves.toEqual({ imports: [importRecordPayload] });
    await expect(
      client.createStoryImport(
        "project_alpha",
        "story_alpha",
        {
          import_id: "import_alpha",
          source_id: "source_alpha",
          filename: "chapter_001.txt",
          title: "Alpha",
          content_base64: "Q2hhcHRlciAx",
          now: "2026-06-27T00:00:00.000Z",
        },
        "session-token",
        "2026-06-27T00:00:00.000Z",
      ),
    ).resolves.toEqual(importRecordPayload);

    for (const [input, init] of fetchMock.mock.calls) {
      expect(input).toBe(
        `https://api.aevryn.ai${API_PATHS.projects}/project_alpha/stories/story_alpha/imports`,
      );
      const headers = init.headers as Headers;
      expect(headers.get("Authorization")).toBe("Bearer session-token");
      expect(headers.get("X-Aevryn-Now")).toBe("2026-06-27T00:00:00.000Z");
    }
    expect(fetchMock.mock.calls[1][1].method).toBe("POST");
  });

  it("sends authenticated requests for project runs", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ runs: [engineRunPayload] })))
      .mockResolvedValueOnce(new Response(JSON.stringify(engineRunPayload)));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.listProjectRuns("project_alpha", "session-token", "2026-06-27T00:00:00.000Z"),
    ).resolves.toEqual({ runs: [engineRunPayload] });
    await expect(
      client.submitImportRun(
        "project_alpha",
        "story_alpha",
        "import_alpha",
        { run_id: "run_alpha", job_id: "job_alpha", now: "2026-06-27T00:00:00.000Z" },
        "session-token",
        "2026-06-27T00:00:00.000Z",
      ),
    ).resolves.toEqual(engineRunPayload);

    expect(fetchMock.mock.calls[0][0]).toBe(
      `https://api.aevryn.ai${API_PATHS.projects}/project_alpha/runs`,
    );
    expect(fetchMock.mock.calls[1][0]).toBe(
      `https://api.aevryn.ai${API_PATHS.projects}/project_alpha/stories/story_alpha/imports/import_alpha/runs`,
    );
    for (const [, init] of fetchMock.mock.calls) {
      const headers = init.headers as Headers;
      expect(headers.get("Authorization")).toBe("Bearer session-token");
      expect(headers.get("X-Aevryn-Now")).toBe("2026-06-27T00:00:00.000Z");
    }
    expect(fetchMock.mock.calls[1][1].method).toBe("POST");
  });

  it("sends authenticated requests for project status", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(projectStatusPayload)));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.projectStatus("project_alpha", "session-token", "2026-06-27T00:00:00.000Z"),
    ).resolves.toEqual(projectStatusPayload);

    expect(fetchMock.mock.calls[0][0]).toBe(
      `https://api.aevryn.ai${API_PATHS.projects}/project_alpha/status`,
    );
    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer session-token");
    expect(headers.get("X-Aevryn-Now")).toBe("2026-06-27T00:00:00.000Z");
  });

  it("sends authenticated requests for snapshots", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ snapshots: [snapshotPayload] })))
      .mockResolvedValueOnce(new Response(JSON.stringify({ snapshots: [snapshotPayload] })));
    vi.stubGlobal("fetch", fetchMock);

    const client = new AevrynApiClient("https://api.aevryn.ai");
    await expect(
      client.listProjectSnapshots("project_alpha", "session-token", "2026-06-27T00:00:00.000Z"),
    ).resolves.toEqual({ snapshots: [snapshotPayload] });
    await expect(
      client.listStorySnapshots(
        "project_alpha",
        "story_alpha",
        "session-token",
        "2026-06-27T00:00:00.000Z",
        "character_profile",
      ),
    ).resolves.toEqual({ snapshots: [snapshotPayload] });

    expect(fetchMock.mock.calls[0][0]).toBe(
      `https://api.aevryn.ai${API_PATHS.projects}/project_alpha/snapshots`,
    );
    expect(fetchMock.mock.calls[1][0]).toBe(
      `https://api.aevryn.ai${API_PATHS.projects}/project_alpha/stories/story_alpha/snapshots?snapshot_kind=character_profile`,
    );
    for (const [, init] of fetchMock.mock.calls) {
      const headers = init.headers as Headers;
      expect(headers.get("Authorization")).toBe("Bearer session-token");
      expect(headers.get("X-Aevryn-Now")).toBe("2026-06-27T00:00:00.000Z");
    }
  });

  it("normalizes API errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ error: "invalid_login", detail: "Invalid credentials." }), {
          status: 401,
        }),
      ),
    );

    const client = new AevrynApiClient("https://api.aevryn.ai");

    await expect(client.health()).rejects.toMatchObject({
      status: 401,
      code: "invalid_login",
      message: "Invalid credentials.",
    });
  });

  it("normalizes network failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("connection refused")));

    const client = new AevrynApiClient("https://api.aevryn.ai");

    await expect(client.health()).rejects.toMatchObject({
      status: 0,
      code: "network_error",
      message: "connection refused",
    });
  });

  it("rejects invalid JSON from successful responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("not json", { status: 200 })));

    const client = new AevrynApiClient("https://api.aevryn.ai");

    await expect(client.health()).rejects.toMatchObject({
      status: 200,
      code: "invalid_json",
    });
  });

  it("rejects unexpected successful response shapes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "ok" }))),
    );

    const client = new AevrynApiClient("https://api.aevryn.ai");

    await expect(client.health()).rejects.toMatchObject({
      status: 200,
      code: "invalid_response",
    });
  });
});

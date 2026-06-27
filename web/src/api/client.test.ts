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

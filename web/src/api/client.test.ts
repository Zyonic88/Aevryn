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

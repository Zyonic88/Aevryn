import { render, screen } from "@testing-library/react";
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
      adapter: "plain_text",
      evidence_anchor_status: "preserved",
      notes: "Plain text import.",
    },
    {
      extension: ".epub",
      status: "supported",
      adapter: "epub",
      evidence_anchor_status: "preserved",
      notes: "EPUB spine import.",
    },
  ],
  deferred: [
    {
      extension: ".pdf",
      status: "deferred",
      adapter: "none",
      evidence_anchor_status: "not_available",
      notes: "Deferred for V1.1.",
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

function storeAuthenticatedProject() {
  window.localStorage.setItem("aevryn.session", JSON.stringify(session));
  window.localStorage.setItem("aevryn.projects", JSON.stringify([projectAlpha]));
}

describe("App shell routing", () => {
  beforeEach(() => {
    window.localStorage.clear();
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
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        if (url.endsWith(API_PATHS.importsInspect)) {
          return Promise.resolve(new Response(JSON.stringify(importInspectPayload)));
        }
        if (url.endsWith(API_PATHS.charactersPreview)) {
          return Promise.resolve(new Response(JSON.stringify(characterPreviewPayload)));
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
    expect(statuses).toHaveLength(2);
    expect(statuses[0]).toHaveTextContent("Checking API health.");
    expect(statuses[1]).toHaveTextContent("Loading capabilities.");
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

  it("keeps a project shell usable when project persistence fails", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));
    const originalSetItem = Storage.prototype.setItem;
    const setItem = vi.spyOn(Storage.prototype, "setItem");
    setItem.mockImplementation(function setStorageItem(this: Storage, key: string, value: string) {
      if (key === "aevryn.projects") {
        throw new Error("storage unavailable");
      }
      return originalSetItem.call(this, key, value);
    });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    const input = await screen.findByLabelText("Project name");
    await user.clear(input);
    await user.type(input, "Temporary Project");
    await user.click(screen.getByRole("button", { name: "Create shell" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("browser storage failed");
    expect(screen.getByRole("link", { name: /Temporary Project/ })).toBeInTheDocument();
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

  it("shows invalid AI JSON errors on the characters workspace tab", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();

    render(
      <MemoryRouter initialEntries={["/projects/project_alpha/characters"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Characters" })).toBeInTheDocument();
    await user.clear(screen.getByLabelText("AI response JSON"));
    await user.type(screen.getByLabelText("AI response JSON"), "not json");
    await user.click(screen.getByRole("button", { name: "Preview characters" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("AI response must be valid JSON.");
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
    await user.type(screen.getByLabelText("Filename"), "chapter.pdf");
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

  it("shows import inspection failures for deferred source formats", async () => {
    const user = userEvent.setup();
    storeAuthenticatedProject();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith(API_PATHS.sourceFormats)) {
          return Promise.resolve(new Response(JSON.stringify(sourceFormatsPayload)));
        }
        if (url.endsWith(API_PATHS.importsInspect)) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                error: "import_failed",
                detail: ".pdf import requires a dedicated parser dependency.",
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
      <MemoryRouter initialEntries={["/projects/project_alpha/import"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText(".pdf")).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Filename"));
    await user.type(screen.getByLabelText("Filename"), "chapter.pdf");
    await user.click(screen.getByRole("button", { name: "Inspect import" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      ".pdf import requires a dedicated parser dependency.",
    );
    expect(screen.queryByRole("heading", { name: "Import Structure" })).not.toBeInTheDocument();
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
});

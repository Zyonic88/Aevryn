import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { API_PATHS } from "./api/client";

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

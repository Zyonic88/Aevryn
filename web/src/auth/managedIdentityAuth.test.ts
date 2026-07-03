import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { API_PATHS } from "../api/client";

const SESSION_TOKEN_KEY = ("session_" + "token") as "session_token";
const ACCESS_TOKEN_KEY = ("access_" + "token") as "access_token";
const REFRESH_TOKEN_KEY = ("refresh_" + "token") as "refresh_token";

const localSession = {
  user_id: "user_local",
  email: "local@example.com",
  display_name: "Local User",
  [SESSION_TOKEN_KEY]: "local-session-token",
  expires_at: "2999-01-01T00:00:00.000Z",
};

const supabaseSession = {
  [ACCESS_TOKEN_KEY]: "supabase-access-token",
  [REFRESH_TOKEN_KEY]: "supabase-refresh-token",
  expires_at: 32503680000,
  user: {
    id: "supabase-user-id",
    email: "managed@example.com",
    user_metadata: {
      display_name: "Managed User",
    },
  },
};

describe("managed identity auth routing", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it("uses local Aevryn auth when managed identity env is absent", async () => {
    vi.mocked(fetch).mockImplementation(() =>
      Promise.resolve(new Response(JSON.stringify(localSession))),
    );

    const { loginWithConfiguredAuth, registerWithConfiguredAuth } = await import(
      "./managedIdentityAuth"
    );

    const login = await loginWithConfiguredAuth({
      email: "local@example.com",
      password: "StrongPass123",
      now: "2026-07-01T00:00:00.000Z",
    });
    const register = await registerWithConfiguredAuth({
      user_id: "user_local",
      display_name: "Local User",
      email: "local@example.com",
      password: "StrongPass123",
      now: "2026-07-01T00:00:00.000Z",
    });

    expect(login.session_token).toBe("local-session-token");
    expect(register.session_token).toBe("local-session-token");
    expect(vi.mocked(fetch).mock.calls[0]?.[0]).toContain(API_PATHS.authLogin);
    expect(vi.mocked(fetch).mock.calls[1]?.[0]).toContain(API_PATHS.authRegister);
  });

  it("logs in through Supabase when managed identity env is configured", async () => {
    vi.stubEnv("VITE_SUPABASE_URL", "https://project.supabase.co");
    vi.stubEnv("VITE_SUPABASE_ANON_KEY", "public-anon-key");
    vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify(supabaseSession)));

    const { loginWithConfiguredAuth } = await import("./managedIdentityAuth");
    const session = await loginWithConfiguredAuth({
      email: "managed@example.com",
      password: "StrongPass123",
      now: "2026-07-01T00:00:00.000Z",
    });

    expect(session).toMatchObject({
      user_id: "supabase-user-id",
      email: "managed@example.com",
      display_name: "Managed User",
      [SESSION_TOKEN_KEY]: "supabase-access-token",
      [REFRESH_TOKEN_KEY]: "supabase-refresh-token",
    });
    expect(session.expires_at).toBe("3000-01-01T00:00:00.000Z");
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      "https://project.supabase.co/auth/v1/token?grant_type=password",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          apikey: "public-anon-key",
          Authorization: "Bearer public-anon-key",
        }),
        body: JSON.stringify({
          email: "managed@example.com",
          password: "StrongPass123",
        }),
      }),
    );
  });

  it("registers through Supabase with display-name metadata", async () => {
    vi.stubEnv("VITE_SUPABASE_URL", "https://project.supabase.co");
    vi.stubEnv("VITE_SUPABASE_ANON_KEY", "public-anon-key");
    vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify(supabaseSession)));

    const { registerWithConfiguredAuth } = await import("./managedIdentityAuth");
    const session = await registerWithConfiguredAuth({
      user_id: "ignored_local_user_id",
      display_name: "Managed User",
      email: "managed@example.com",
      password: "StrongPass123",
      now: "2026-07-01T00:00:00.000Z",
    });

    expect(session.session_token).toBe("supabase-access-token");
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      "https://project.supabase.co/auth/v1/signup",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          email: "managed@example.com",
          password: "StrongPass123",
          data: {
            display_name: "Managed User",
            full_name: "Managed User",
          },
        }),
      }),
    );
  });

  it("shows provider errors without logging provider payloads", async () => {
    vi.stubEnv("VITE_SUPABASE_URL", "https://project.supabase.co");
    vi.stubEnv("VITE_SUPABASE_ANON_KEY", "public-anon-key");
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ error_description: "Invalid login credentials" }), {
        status: 400,
      }),
    );

    const { loginWithConfiguredAuth } = await import("./managedIdentityAuth");

    await expect(
      loginWithConfiguredAuth({
        email: "managed@example.com",
        password: "WrongPass123",
        now: "2026-07-01T00:00:00.000Z",
      }),
    ).rejects.toThrow("Invalid login credentials");
  });

  it("refreshes a managed identity session with the provider refresh token", async () => {
    vi.stubEnv("VITE_SUPABASE_URL", "https://project.supabase.co");
    vi.stubEnv("VITE_SUPABASE_ANON_KEY", "public-anon-key");
    vi.mocked(fetch).mockResolvedValue(
      new Response(
        JSON.stringify({
          ...supabaseSession,
          [ACCESS_TOKEN_KEY]: "fresh-access-token",
          [REFRESH_TOKEN_KEY]: "fresh-refresh-token",
        }),
      ),
    );

    const { refreshConfiguredAuthSession } = await import("./managedIdentityAuth");
    const session = await refreshConfiguredAuthSession({
      user_id: "supabase-user-id",
      email: "managed@example.com",
      display_name: "Managed User",
      [SESSION_TOKEN_KEY]: "expired-access-token",
      [REFRESH_TOKEN_KEY]: "supabase-refresh-token",
      expires_at: "2026-07-01T00:00:00.000Z",
    });

    expect(session.session_token).toBe("fresh-access-token");
    expect(session.refresh_token).toBe("fresh-refresh-token");
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      "https://project.supabase.co/auth/v1/token?grant_type=refresh_token",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          [REFRESH_TOKEN_KEY]: "supabase-refresh-token",
        }),
      }),
    );
  });

  it("requires a refresh token before refreshing managed identity sessions", async () => {
    vi.stubEnv("VITE_SUPABASE_URL", "https://project.supabase.co");
    vi.stubEnv("VITE_SUPABASE_ANON_KEY", "public-anon-key");

    const { refreshConfiguredAuthSession } = await import("./managedIdentityAuth");

    await expect(
      refreshConfiguredAuthSession({
        user_id: "supabase-user-id",
        email: "managed@example.com",
        display_name: "Managed User",
        [SESSION_TOKEN_KEY]: "expired-access-token",
        expires_at: "2026-07-01T00:00:00.000Z",
      }),
    ).rejects.toThrow("Session refresh is unavailable. Please log in again.");
    expect(fetch).not.toHaveBeenCalled();
  });
});

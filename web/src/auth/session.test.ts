import { describe, expect, it } from "vitest";

import {
  clearStoredSession,
  isSessionRefreshable,
  isSessionExpired,
  readStoredSession,
  writeStoredSession,
} from "./session";

const session = {
  user_id: "user_demo",
  email: "demo@example.com",
  display_name: "Demo User",
  session_token: "session-token",
  expires_at: "2999-06-27T00:00:00.000Z",
};

describe("session storage", () => {
  it("round-trips a browser session", () => {
    writeStoredSession(session);

    expect(readStoredSession()).toEqual(session);
  });

  it("clears a browser session", () => {
    writeStoredSession(session);
    clearStoredSession();

    expect(readStoredSession()).toBeNull();
  });

  it("removes malformed session JSON", () => {
    window.localStorage.setItem("aevryn.session", "not json");

    expect(readStoredSession()).toBeNull();
    expect(window.localStorage.getItem("aevryn.session")).toBeNull();
  });

  it("removes sessions that do not match the API contract", () => {
    window.localStorage.setItem("aevryn.session", JSON.stringify({ user_id: "user_demo" }));

    expect(readStoredSession()).toBeNull();
    expect(window.localStorage.getItem("aevryn.session")).toBeNull();
  });

  it("removes expired sessions", () => {
    window.localStorage.setItem(
      "aevryn.session",
      JSON.stringify({ ...session, expires_at: "2026-06-27T00:00:00.000Z" }),
    );

    expect(readStoredSession(window.localStorage, new Date("2026-06-27T00:00:01.000Z"))).toBeNull();
    expect(window.localStorage.getItem("aevryn.session")).toBeNull();
  });

  it("keeps expired sessions when a refresh token is available", () => {
    const refreshableSession = {
      ...session,
      refresh_token: "refresh-token",
      expires_at: "2026-06-27T00:00:00.000Z",
    };
    window.localStorage.setItem("aevryn.session", JSON.stringify(refreshableSession));

    expect(readStoredSession(window.localStorage, new Date("2026-06-27T00:00:01.000Z"))).toEqual(
      refreshableSession,
    );
    expect(window.localStorage.getItem("aevryn.session")).not.toBeNull();
  });

  it("returns null when browser storage cannot be read", () => {
    expect(readStoredSession(throwingStorage())).toBeNull();
  });

  it("reports failed session writes without throwing", () => {
    expect(writeStoredSession(session, throwingStorage())).toBe(false);
  });

  it("reports failed session clears without throwing", () => {
    expect(clearStoredSession(throwingStorage())).toBe(false);
  });

  it("treats invalid expiration timestamps as expired", () => {
    expect(isSessionExpired({ ...session, expires_at: "not a date" })).toBe(true);
  });

  it("detects refreshable sessions", () => {
    expect(isSessionRefreshable({ ...session, refresh_token: "refresh-token" })).toBe(true);
    expect(isSessionRefreshable(session)).toBe(false);
  });
});

function throwingStorage(): Storage {
  return {
    length: 0,
    clear() {
      throw new Error("storage unavailable");
    },
    getItem() {
      throw new Error("storage unavailable");
    },
    key() {
      return null;
    },
    removeItem() {
      throw new Error("storage unavailable");
    },
    setItem() {
      throw new Error("storage unavailable");
    },
  };
}

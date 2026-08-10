import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "./AuthProvider";
import { useAuth } from "./useAuth";

const session = {
  user_id: "user_demo",
  email: "demo@example.com",
  display_name: "Demo User",
  session_token: "session-token",
  expires_at: "2999-06-27T00:00:00.000Z",
};

function SessionProbe() {
  const { isAuthenticated, session, sessionPersistenceError } = useAuth();
  return (
    <section aria-label="Session probe">
      <p>{isAuthenticated ? "authenticated" : "anonymous"}</p>
      <p>{session?.display_name ?? "no user"}</p>
      {sessionPersistenceError ? <p role="alert">{sessionPersistenceError}</p> : null}
    </section>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    window.localStorage.clear();
  });

  it("clears inactive browser sessions after thirty minutes", async () => {
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));

    render(
      <AuthProvider>
        <SessionProbe />
      </AuthProvider>,
    );

    expect(screen.getByText("authenticated")).toBeInTheDocument();
    expect(screen.getByText("Demo User")).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(30 * 60 * 1000);
    });

    expect(screen.getByText("anonymous")).toBeInTheDocument();
    expect(screen.getByText("no user")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "You were logged out after 30 minutes of inactivity.",
    );
    expect(window.localStorage.getItem("aevryn.session")).toBeNull();
    expect(document.body).not.toHaveTextContent("session-token");
  });

  it("resets the inactivity timer when the user is active", async () => {
    window.localStorage.setItem("aevryn.session", JSON.stringify(session));

    render(
      <AuthProvider>
        <SessionProbe />
      </AuthProvider>,
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(29 * 60 * 1000);
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab" }));
      await vi.advanceTimersByTimeAsync(2 * 60 * 1000);
    });

    expect(screen.getByText("authenticated")).toBeInTheDocument();
    expect(window.localStorage.getItem("aevryn.session")).not.toBeNull();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(28 * 60 * 1000);
    });

    expect(screen.getByText("anonymous")).toBeInTheDocument();
    expect(window.localStorage.getItem("aevryn.session")).toBeNull();
  });
});

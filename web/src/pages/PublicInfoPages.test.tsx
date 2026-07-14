import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../App";

describe("public information pages", () => {
  afterEach(() => {
    window.localStorage.clear();
  });

  it("renders the trust page without requiring authentication", () => {
    render(
      <MemoryRouter initialEntries={["/trust"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Your work belongs to you." })).toBeInTheDocument();
    expect(screen.getByText(/AI does not own truth\. Your story wins\./u)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Log in" })).not.toBeInTheDocument();
  });

  it("publishes verified support contacts with private-story redaction guidance", () => {
    render(
      <MemoryRouter initialEntries={["/support"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Need help with Aevryn?" })).toBeInTheDocument();
    expect(screen.getByText(/support@aevryn.ai/u)).toBeInTheDocument();
    expect(screen.getByText(/privacy@aevryn.ai/u)).toBeInTheDocument();
    expect(screen.getByText(/security@aevryn.ai/u)).toBeInTheDocument();
    expect(screen.getByText(/abuse@aevryn.ai/u)).toBeInTheDocument();
    expect(screen.getByText(/Please do not send full manuscripts/u)).toBeInTheDocument();
  });

  it("keeps legal-sensitive pages marked as drafts", () => {
    render(
      <MemoryRouter initialEntries={["/privacy"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByText("Draft for attorney review before public launch.")).toBeInTheDocument();
    expect(screen.getByText("Privacy questions should go to privacy@aevryn.ai.")).toBeInTheDocument();
  });

  it("links public pages from the login screen", () => {
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <App />
      </MemoryRouter>,
    );

    const publicNav = screen.getByRole("navigation", { name: "Public information" });
    expect(within(publicNav).getByRole("link", { name: "Trust" })).toHaveAttribute(
      "href",
      "/trust",
    );
    expect(within(publicNav).getByRole("link", { name: "Support" })).toHaveAttribute(
      "href",
      "/support",
    );
    expect(within(publicNav).getByRole("link", { name: "Privacy" })).toHaveAttribute(
      "href",
      "/privacy",
    );
  });
});

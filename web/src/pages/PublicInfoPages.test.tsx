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
    expect(screen.getByText(/up to 30 days for authorized disaster recovery only/u)).toBeInTheDocument();
    expect(screen.getByText(/Backups are not used for AI training, analytics/u)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "AI Providers" })).toBeInTheDocument();
    expect(screen.getByText(/The current provider candidate is OpenAI/u)).toBeInTheDocument();
    expect(screen.getByText(/extraction requests set store=false/u)).toBeInTheDocument();
    expect(screen.getByText(/OpenAI API inputs and outputs are not used for model training by default/u)).toBeInTheDocument();
    expect(screen.getByText(/abuse-monitoring logs may contain prompts and responses/u)).toBeInTheDocument();
    expect(screen.getByText(/does not represent Modified Abuse Monitoring/u)).toBeInTheDocument();
    expect(screen.getByText(/Provider output is not Canon/u)).toBeInTheDocument();
  });

  it("shows deletion and backup boundaries on the user rights page", () => {
    render(
      <MemoryRouter initialEntries={["/user-rights"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Deletion And Backups" })).toBeInTheDocument();
    expect(
      screen.getByText(/Deletion removes active Aevryn-owned project and story storage/u),
    ).toBeInTheDocument();
    expect(screen.getByText(/up to 30 days for authorized disaster recovery only/u)).toBeInTheDocument();
    expect(screen.getByText(/Backups are not used for AI training, analytics/u)).toBeInTheDocument();
  });

  it("publishes the 18 plus public beta and restricted explicit-content boundary", () => {
    render(
      <MemoryRouter initialEntries={["/content"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Public Beta" })).toBeInTheDocument();
    expect(screen.getByText("Aevryn V2 public beta is 18+ only.")).toBeInTheDocument();
    expect(
      screen.getByText(/Restricted explicit sexual content processing remains disabled/u),
    ).toBeInTheDocument();
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

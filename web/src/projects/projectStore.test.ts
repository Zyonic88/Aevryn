import { describe, expect, it } from "vitest";

import { createProjectShell, normalizeProjectName } from "./projectStore";

describe("project store", () => {
  it("normalizes project names", () => {
    expect(normalizeProjectName("  My    New\nNovel  ")).toBe("My New Novel");
  });

  it("rejects blank project names", () => {
    expect(() => createProjectShell("   ")).toThrow("Project name is required.");
  });

  it("creates project shells for API-backed project creation", () => {
    const project = createProjectShell(
      "  New   Novel  ",
      {
        now: new Date("2026-06-27T00:00:00.000Z"),
        randomUuid: "11111111-2222-4333-8444-555555555555",
      },
    );

    expect(project).toEqual({
      id: "project_11111111_2222_4333_8444_555555555555",
      name: "New Novel",
      updatedAt: "2026-06-27T00:00:00.000Z",
    });
  });
});

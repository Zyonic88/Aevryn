import { describe, expect, it } from "vitest";

import { createProject, normalizeProjectName, readProjects, writeProjects } from "./projectStore";

describe("project shell store", () => {
  it("persists project summaries", () => {
    const projects = [
      {
        id: "project_alpha",
        name: "Alpha",
        updatedAt: "2026-06-27T00:00:00.000Z",
      },
    ];

    writeProjects(projects);

    expect(readProjects()).toEqual(projects);
  });

  it("drops malformed project storage", () => {
    window.localStorage.setItem("aevryn.projects", "not json");

    expect(readProjects()).toEqual([]);
    expect(window.localStorage.getItem("aevryn.projects")).toBeNull();
  });

  it("drops non-array project storage", () => {
    window.localStorage.setItem("aevryn.projects", JSON.stringify({ id: "project_bad" }));

    expect(readProjects()).toEqual([]);
    expect(window.localStorage.getItem("aevryn.projects")).toBeNull();
  });

  it("filters malformed project records", () => {
    window.localStorage.setItem(
      "aevryn.projects",
      JSON.stringify([
        { id: "project_good", name: "Good", updatedAt: "2026-06-27T00:00:00.000Z" },
        { id: "bad", name: "Bad", updatedAt: "2026-06-27T00:00:00.000Z" },
        { id: "project_empty", name: " ", updatedAt: "2026-06-27T00:00:00.000Z" },
      ]),
    );

    expect(readProjects()).toEqual([
      { id: "project_good", name: "Good", updatedAt: "2026-06-27T00:00:00.000Z" },
    ]);
  });

  it("returns an empty list when browser storage cannot be read", () => {
    expect(readProjects(throwingStorage())).toEqual([]);
  });

  it("reports failed project writes without throwing", () => {
    expect(
      writeProjects(
        [{ id: "project_alpha", name: "Alpha", updatedAt: "2026-06-27T00:00:00.000Z" }],
        throwingStorage(),
      ),
    ).toBe(false);
  });

  it("normalizes project names", () => {
    expect(normalizeProjectName("  My    New\nNovel  ")).toBe("My New Novel");
  });

  it("rejects blank project names", () => {
    expect(() => createProject("   ", [])).toThrow("Project name is required.");
  });

  it("creates newest-first project shells", () => {
    const projects = createProject(
      "  New   Novel  ",
      [
        {
          id: "project_old",
          name: "Old Novel",
          updatedAt: "2026-06-26T00:00:00.000Z",
        },
      ],
      {
        now: new Date("2026-06-27T00:00:00.000Z"),
        randomUuid: "11111111-2222-4333-8444-555555555555",
      },
    );

    expect(projects[0]).toEqual({
      id: "project_11111111_2222_4333_8444_555555555555",
      name: "New Novel",
      updatedAt: "2026-06-27T00:00:00.000Z",
    });
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

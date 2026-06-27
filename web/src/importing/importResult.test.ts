import { describe, expect, it } from "vitest";

import type { ImportInspect } from "../api/schemas";
import {
  importResultTotalsLabel,
  importScenePreviewRows,
  importScenePreviewSummary,
} from "./importResult";

const baseResult: ImportInspect = {
  source_id: "source_demo",
  source_format: "txt",
  title: "Demo",
  chapters: 10,
  chapter_ids: [],
  scenes: 8,
  scene_ids: [],
  scene_map: Array.from({ length: 8 }, (_, index) => ({
    chapter_id: `chapter_${index + 1}`,
    chapter_index: index + 1,
    scene_id: `scene_${index + 1}`,
    scene_index: 1,
    title: `Scene ${index + 1}`,
  })),
  paragraphs: 20,
  evidence_anchors: 30,
  first_evidence_anchors: [],
};

describe("import result presentation helpers", () => {
  it("limits scene preview rows", () => {
    expect(importScenePreviewRows(baseResult).map((scene) => scene.scene_id)).toEqual([
      "scene_1",
      "scene_2",
      "scene_3",
      "scene_4",
      "scene_5",
      "scene_6",
    ]);
  });

  it("summarizes truncated scene previews", () => {
    expect(importScenePreviewSummary(baseResult)).toBe("Showing first 6 of 8 scenes.");
  });

  it("summarizes complete scene previews", () => {
    expect(
      importScenePreviewSummary({ ...baseResult, scene_map: baseResult.scene_map.slice(0, 2) }),
    ).toBe("Showing all 2 scenes.");
  });

  it("summarizes empty scene previews", () => {
    expect(importScenePreviewSummary({ ...baseResult, scene_map: [] })).toBe(
      "No scenes available.",
    );
  });

  it("formats import totals", () => {
    expect(importResultTotalsLabel(baseResult)).toBe("10 chapters, 8 scenes, 30 evidence anchors.");
  });

  it("formats singular import totals", () => {
    expect(
      importResultTotalsLabel({
        ...baseResult,
        chapters: 1,
        scenes: 1,
        evidence_anchors: 1,
      }),
    ).toBe("1 chapter, 1 scene, 1 evidence anchor.");
  });
});

import type { ImportInspect } from "../api/schemas";

export const MAX_IMPORT_SCENE_PREVIEW_ROWS = 6;

export function importScenePreviewRows(result: ImportInspect) {
  return result.scene_map.slice(0, MAX_IMPORT_SCENE_PREVIEW_ROWS);
}

export function importScenePreviewSummary(result: ImportInspect): string {
  const shown = Math.min(result.scene_map.length, MAX_IMPORT_SCENE_PREVIEW_ROWS);
  if (result.scene_map.length === 0) {
    return "No scenes available.";
  }
  if (result.scene_map.length === shown) {
    return `Showing all ${formatCount(result.scene_map.length, "scene")}.`;
  }
  return `Showing first ${shown.toLocaleString()} of ${formatCount(result.scene_map.length, "scene")}.`;
}

export function importResultTotalsLabel(result: ImportInspect): string {
  return `${formatCount(result.chapters, "chapter")}, ${formatCount(result.scenes, "scene")}, ${formatCount(result.evidence_anchors, "evidence anchor")}.`;
}

function formatCount(value: number, singularLabel: string): string {
  const label = value === 1 ? singularLabel : `${singularLabel}s`;
  return `${value.toLocaleString()} ${label}`;
}

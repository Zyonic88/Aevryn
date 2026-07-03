import type { ProjectOutputs } from "../api/schemas";

export type TranslationReviewItem =
  ProjectOutputs["language_identity"]["translation_review_items"][number];
export type IdentityReviewItem =
  ProjectOutputs["language_identity"]["identity_review_items"][number];

export function reviewItemCountLabel(count: number): string {
  return count === 1 ? "1 review item" : `${count.toLocaleString()} review items`;
}

export function translationReviewKey(item: TranslationReviewItem): string {
  return [
    item.issue_code,
    item.chapter_id,
    item.scene_id,
    item.evidence_anchor_count,
  ].join(":");
}

export function translationReviewDetails(
  item: TranslationReviewItem,
  fallbackReason = "Aevryn held this translation for review",
): string {
  const sourceLinkLabel =
    item.evidence_anchor_count === 1
      ? "1 source link preserved"
      : `${item.evidence_anchor_count.toLocaleString()} source links preserved`;
  return `${readableSceneScope(item)}; ${sourceLinkLabel}; ${item.reason || fallbackReason}`;
}

export function identityReviewKey(item: IdentityReviewItem): string {
  return [
    item.status,
    item.chapter_id,
    item.scene_id,
    item.evidence_anchor_id,
    item.reference_kind,
    item.reference_label,
    item.candidate_count,
  ].join(":");
}

export function identityReviewTitle(item: IdentityReviewItem): string {
  const kind = readableLabel(item.reference_kind || "reference");
  return `${kind}: ${item.reference_label || "Reference needing review"}`;
}

export function identityReviewDetails(
  item: IdentityReviewItem,
  actionLabel: string,
): string {
  const confidence = Math.round(item.confidence * 100);
  const confidenceLabel = confidence > 0 ? `; ${confidence}% confidence` : "";
  return `${readableSceneScope(item)}; ${identityCandidateLabel(item)}${confidenceLabel}; ${actionLabel}`;
}

export function identityReviewStatusLabel(status: string): string {
  if (status === "ambiguous") {
    return "Needs review";
  }
  if (status === "unresolved") {
    return "Unresolved reference";
  }
  return readableLabel(status);
}

export function identityCandidateLabel(item: IdentityReviewItem): string {
  if (item.candidate_count === 0) {
    return "no supported match";
  }
  if (item.candidate_count === 1) {
    return "1 possible match";
  }
  return `${item.candidate_count.toLocaleString()} possible matches`;
}

export function readableSceneScope(
  item: IdentityReviewItem | TranslationReviewItem,
): string {
  const sceneMatch = item.scene_id.match(/_chapter_(\d+)_scene_(\d+)$/);
  if (sceneMatch) {
    return `Chapter ${Number(sceneMatch[1])}, Scene ${Number(sceneMatch[2])}`;
  }
  const chapterMatch = item.chapter_id.match(/_chapter_(\d+)$/);
  if (chapterMatch) {
    return `Chapter ${Number(chapterMatch[1])}`;
  }
  return "Scene evidence";
}

export function readableLabel(value: string): string {
  return value
    .split("_")
    .filter(Boolean)
    .map((word) => `${word.charAt(0).toUpperCase()}${word.slice(1)}`)
    .join(" ");
}

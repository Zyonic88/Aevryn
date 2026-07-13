import type { ProjectOutputs } from "../api/schemas";

export type TranslationReviewItem =
  ProjectOutputs["language_identity"]["translation_review_items"][number];
export type IdentityReviewItem =
  ProjectOutputs["language_identity"]["identity_review_items"][number];
export type CompactIdentityReviewItem = IdentityReviewItem & {
  review_count?: number;
};

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

export function compactIdentityReviewItems(
  items: IdentityReviewItem[],
  limit: number,
): CompactIdentityReviewItem[] {
  const compacted = new Map<string, CompactIdentityReviewItem>();
  for (const item of items) {
    const key = [
      item.status,
      item.chapter_id,
      item.scene_id,
      item.reference_kind,
      item.reference_label,
      item.candidate_count,
      item.confidence,
      item.reason,
    ].join(":");
    const existing = compacted.get(key);
    const reviewCount = item.review_count || 1;
    if (existing) {
      existing.review_count = (existing.review_count || 1) + reviewCount;
    } else {
      compacted.set(key, { ...item, review_count: reviewCount });
    }
  }
  return Array.from(compacted.values()).slice(0, limit);
}

export function identityReviewKey(item: CompactIdentityReviewItem): string {
  return [
    item.status,
    item.chapter_id,
    item.scene_id,
    item.reference_kind,
    item.reference_label,
    item.candidate_count,
    item.review_count || 1,
  ].join(":");
}

export function identityReviewTitle(item: CompactIdentityReviewItem): string {
  const kind = readableLabel(item.reference_kind || "reference");
  return `${kind}: ${item.reference_label || "Reference needing review"}`;
}

export function identityReviewDetails(
  item: CompactIdentityReviewItem,
  actionLabel: string,
): string {
  const confidence = Math.round(item.confidence * 100);
  const confidenceLabel = confidence > 0 ? `; ${confidence}% confidence` : "";
  const reviewCountLabel =
    (item.review_count || 1) > 1 ? `${item.review_count?.toLocaleString()} similar references; ` : "";
  return `${readableSceneScope(item)}; ${reviewCountLabel}${identityCandidateLabel(item)}${confidenceLabel}; ${actionLabel}`;
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

export function identityCandidateLabel(item: CompactIdentityReviewItem): string {
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

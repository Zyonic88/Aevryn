import type { CharacterProfile } from "../api/schemas";
import { isInternalOutputPlaceholder } from "./readableOutput";

const MAX_DUPLICATE_CARD_REVIEW_ITEMS = 8;
const IDENTITY_TITLE_WORDS = new Set([
  "baron",
  "baroness",
  "captain",
  "chief",
  "commander",
  "doctor",
  "emperor",
  "empress",
  "engineer",
  "general",
  "king",
  "lady",
  "lord",
  "master",
  "officer",
  "prince",
  "princess",
  "professor",
  "queen",
  "sir",
  "student",
  "teacher",
]);

export type CharacterDuplicateReviewItem = {
  leftId: string;
  rightId: string;
  reason: string;
  reviewOnly: true;
};

export function characterDuplicateReviewItems(
  profiles: CharacterProfile[],
): CharacterDuplicateReviewItem[] {
  const items: CharacterDuplicateReviewItem[] = [];
  for (let leftIndex = 0; leftIndex < profiles.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < profiles.length; rightIndex += 1) {
      const reviewItem = characterDuplicateReviewItem(profiles[leftIndex], profiles[rightIndex]);
      if (reviewItem) {
        items.push(reviewItem);
      }
    }
  }
  return items.slice(0, MAX_DUPLICATE_CARD_REVIEW_ITEMS);
}

function characterDuplicateReviewItem(
  left: CharacterProfile,
  right: CharacterProfile,
): CharacterDuplicateReviewItem | null {
  if (left.character_id === right.character_id) {
    return null;
  }
  const leftSignals = characterIdentitySignals(left);
  const rightSignals = characterIdentitySignals(right);
  const sharedSignal = Array.from(leftSignals).find((signal) => rightSignals.has(signal));
  if (sharedSignal) {
    return duplicateReviewItem(left, right, duplicateReviewReason(sharedSignal));
  }
  if (titleQualifiedIdentityOverlap(leftSignals, rightSignals)) {
    return duplicateReviewItem(left, right, "Possible title/name overlap");
  }
  return null;
}

function duplicateReviewItem(
  left: CharacterProfile,
  right: CharacterProfile,
  reason: string,
): CharacterDuplicateReviewItem {
  return {
    leftId: left.character_id,
    rightId: right.character_id,
    reason,
    reviewOnly: true,
  };
}

function duplicateReviewReason(sharedSignal: string): string {
  if (sharedSignal.includes("::display")) {
    return "Possible matching display names";
  }
  if (sharedSignal.includes("::alias")) {
    return "Possible shared alias";
  }
  return "Possible shared name or alias";
}

function characterIdentitySignals(profile: CharacterProfile): Set<string> {
  const signals = new Set<string>();
  addIdentitySignal(signals, profile.display_name, "display");
  for (const item of profile.aliases.items) {
    addIdentitySignal(signals, item, "alias");
  }
  return signals;
}

function addIdentitySignal(signals: Set<string>, value: string, kind: "alias" | "display") {
  const normalized = normalizedIdentityPhrase(value);
  if (!normalized || normalized === "unknown") {
    return;
  }
  signals.add(`${normalized}::${kind}`);
  signals.add(normalized);
  const titleStripped = stripLeadingIdentityTitles(normalized);
  if (titleStripped !== normalized && titleStripped) {
    signals.add(`${titleStripped}::title-qualified`);
  }
}

function titleQualifiedIdentityOverlap(left: Set<string>, right: Set<string>): boolean {
  const leftBareNames = bareIdentityNames(left);
  const rightBareNames = bareIdentityNames(right);
  return (
    Array.from(left).some((signal) =>
      signal.endsWith("::title-qualified")
        ? rightBareNames.has(signal.replace(/::title-qualified$/u, ""))
        : false,
    ) ||
    Array.from(right).some((signal) =>
      signal.endsWith("::title-qualified")
        ? leftBareNames.has(signal.replace(/::title-qualified$/u, ""))
        : false,
    )
  );
}

function bareIdentityNames(signals: Set<string>): Set<string> {
  return new Set(
    Array.from(signals)
      .filter((signal) => signal.endsWith("::display") || signal.endsWith("::alias"))
      .map((signal) => signal.replace(/::(?:display|alias)$/u, "")),
  );
}

function normalizedIdentityPhrase(value: string): string {
  if (isInternalOutputPlaceholder(value)) {
    return "";
  }
  return value
    .toLowerCase()
    .replace(/['’]s\b/gu, "")
    .replace(/[^a-z0-9]+/gu, " ")
    .trim()
    .replace(/\s+/gu, " ");
}

function stripLeadingIdentityTitles(value: string): string {
  const words = value.split(" ").filter(Boolean);
  while (words.length > 1 && IDENTITY_TITLE_WORDS.has(words[0])) {
    words.shift();
  }
  return words.join(" ");
}

import { describe, expect, it } from "vitest";

import type { CharacterProfile, OutputSection } from "../api/schemas";
import { characterDuplicateReviewItems } from "./characterDuplicateReview";

const unknownSection = (title: string): OutputSection => ({ title, items: ["Unknown"] });

function profile(
  characterId: string,
  displayName: string,
  overrides: Partial<CharacterProfile> = {},
): CharacterProfile {
  return {
    character_id: characterId,
    display_name: displayName,
    subtitle: "Unknown",
    aliases: unknownSection("Aliases"),
    titles: unknownSection("Titles"),
    descriptions: unknownSection("Descriptions"),
    appearance: unknownSection("Appearance"),
    race: unknownSection("Race"),
    gender: unknownSection("Gender"),
    status: unknownSection("Status"),
    current_goal: unknownSection("Current Goal"),
    current_equipment: unknownSection("Current Equipment"),
    current_abilities: unknownSection("Current Abilities"),
    current_assets: unknownSection("Current Assets"),
    territory: unknownSection("Territory"),
    relationships: unknownSection("Relationships"),
    current_limitations: unknownSection("Current Limitations"),
    first_appearance: unknownSection("First Appearance"),
    latest_appearance: unknownSection("Latest Appearance"),
    timeline_history: unknownSection("Timeline History"),
    evidence_references: unknownSection("Evidence References"),
    recent_changes: unknownSection("Recent Changes"),
    evidence_summary: "0 verified facts",
    ...overrides,
  };
}

describe("characterDuplicateReviewItems", () => {
  it("flags exact duplicate display names without merging them", () => {
    const items = characterDuplicateReviewItems([
      profile("character_001", "Mira"),
      profile("character_002", "Mira"),
    ]);

    expect(items).toEqual([
      {
        leftId: "character_001",
        rightId: "character_002",
        reason: "Matching display names",
      },
    ]);
  });

  it("flags alias-to-display overlap across cards", () => {
    const items = characterDuplicateReviewItems([
      profile("character_001", "Mira", {
        aliases: { title: "Aliases", items: ["Captain Mira"] },
      }),
      profile("character_002", "Unknown character", {
        aliases: { title: "Aliases", items: ["Mira"] },
      }),
    ]);

    expect(items).toEqual([
      {
        leftId: "character_001",
        rightId: "character_002",
        reason: "Shared name or alias",
      },
    ]);
  });

  it("flags title-plus-name overlap without story-specific names", () => {
    const items = characterDuplicateReviewItems([
      profile("character_001", "Charlotte"),
      profile("character_002", "General Charlotte"),
    ]);

    expect(items).toEqual([
      {
        leftId: "character_001",
        rightId: "character_002",
        reason: "Title plus name may refer to an existing card",
      },
    ]);
  });

  it("does not flag unrelated cards that only share a generic title", () => {
    const items = characterDuplicateReviewItems([
      profile("character_001", "Captain Mira"),
      profile("character_002", "Captain Rowan"),
    ]);

    expect(items).toEqual([]);
  });
});

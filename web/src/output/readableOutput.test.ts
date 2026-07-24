import { describe, expect, it } from "vitest";

import {
  readableOutputItem,
  readableOutputItems,
  readablePromptPreview,
  readablePromptSummary,
  readablePromptText,
} from "./readableOutput";

describe("readableOutputItem", () => {
  it("removes all supported entity type prefixes from relationships", () => {
    expect(
      readableOutputItem(
        "character_zhao_chen bound_to_system system_super_starfleet",
      ),
    ).toBe("Zhao Chen bound to Super Starfleet");
    expect(
      readableOutputItem(
        "character_charlotte has_item weapon_obsidian_sword",
      ),
    ).toBe("Charlotte has Obsidian Sword");
  });

  it("renders accepted non-character entities without machine prefixes", () => {
    expect(readableOutputItem("Entity accepted: system_super_starfleet")).toBe(
      "New System: Super Starfleet",
    );
    expect(readableOutputItem("Entity accepted: creature_silver_dragon")).toBe(
      "New Creature: Silver Dragon",
    );
  });

  it("filters internal source and evidence identifiers before formatting", () => {
    expect(
      readableOutputItems([
        "Scene Summary: Zhao Chen reviews the starship blueprint",
        "Scene ID: source_alpha_chapter_001_scene_001",
        "Evidence Anchor: source_alpha_anchor_001",
        "Import ID: import_123_alpha",
        "aevryn_import_bundle_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
        "Setting: North Star Academy classroom",
      ]),
    ).toEqual([
      "Scene Summary: Zhao Chen reviews the starship blueprint",
      "Setting: North Star Academy classroom",
    ]);
  });

  it("keeps prompt display copy bounded to human canon details", () => {
    const section = {
      items: [
        "Generate this image using only accepted Aevryn canon",
        "Scene ID: source_alpha_chapter_001_scene_001",
        "Evidence Anchor: source_alpha_anchor_001",
        "Setting: North Star Academy classroom",
        "Character: character_zhao_chen",
        "source_alpha_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
      ],
    };

    expect(readablePromptPreview(section, { maxItems: 5 })).toEqual({
      items: [
        "Generate this image using only accepted Aevryn canon.",
        "Setting: North Star Academy classroom.",
        "Character: Zhao Chen.",
      ],
      hiddenCount: 0,
    });
    expect(readablePromptSummary(section)).toBe("3 prompt details ready.");
    expect(readablePromptText(section)).toBe(
      [
        "Generate this image using only accepted Aevryn canon.",
        "Setting: North Star Academy classroom.",
        "Character: Zhao Chen.",
      ].join("\n\n"),
    );
  });
});

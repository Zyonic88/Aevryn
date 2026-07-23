import { describe, expect, it } from "vitest";

import { readableOutputItem } from "./readableOutput";

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
});

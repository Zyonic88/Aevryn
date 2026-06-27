import { describe, expect, it } from "vitest";

import {
  buildCharacterPreviewPayload,
  buildWorldPreviewPayload,
  canBuildCharacterPreviewPayload,
  canBuildWorldPreviewPayload,
  canSubmitCharacterPreviewInput,
  canSubmitWorldPreviewInput,
} from "./previewPayload";

const validInput = {
  sourceId: "source_demo",
  filename: "chapter.txt",
  title: "Demo",
  sourceText: "Chapter 1\nMark carried a rusty dagger.",
  aiResponseText: JSON.stringify({ entities: [] }),
  characterIdsText: "character_mark, character_luna",
  sceneId: "source_demo_chapter_001_scene_001",
};

describe("preview payload helpers", () => {
  it("builds character preview payloads with UTF-8 source content and parsed AI JSON", () => {
    const payload = buildCharacterPreviewPayload({
      ...validInput,
      sourceText: "Chapter 1\nZhao Chen gained insight.",
      aiResponseText: '{"entities":[]}',
    });

    expect(payload).toMatchObject({
      source_id: "source_demo",
      filename: "chapter.txt",
      title: "Demo",
      ai_response: { entities: [] },
      character_ids: ["character_mark", "character_luna"],
      scene_id: "source_demo_chapter_001_scene_001",
    });
    expect(atob(payload.content_base64)).toContain("Zhao Chen");
  });

  it("omits optional scene IDs when blank", () => {
    const payload = buildCharacterPreviewPayload({ ...validInput, sceneId: " " });

    expect(payload).not.toHaveProperty("scene_id");
  });

  it("builds world preview payloads", () => {
    const payload = buildWorldPreviewPayload({
      ...validInput,
      worldEntityIdsText: "location_hangar building_fortress",
    });

    expect(payload).toMatchObject({
      ai_response: { entities: [] },
      world_entity_ids: ["location_hangar", "building_fortress"],
      scene_id: "source_demo_chapter_001_scene_001",
    });
  });

  it("accepts whitespace separated character IDs", () => {
    const payload = buildCharacterPreviewPayload({
      ...validInput,
      characterIdsText: "character_mark\ncharacter_luna",
    });

    expect(payload.character_ids).toEqual(["character_mark", "character_luna"]);
  });

  it("rejects invalid AI response JSON", () => {
    expect(() =>
      buildCharacterPreviewPayload({ ...validInput, aiResponseText: "not json" }),
    ).toThrow("AI response must be valid JSON.");
  });

  it("reports whether a character preview payload can be built", () => {
    expect(canBuildCharacterPreviewPayload(validInput)).toBe(true);
    expect(canBuildCharacterPreviewPayload({ ...validInput, sourceText: "" })).toBe(false);
    expect(canBuildCharacterPreviewPayload({ ...validInput, aiResponseText: "" })).toBe(false);
    expect(canBuildCharacterPreviewPayload({ ...validInput, aiResponseText: "not json" })).toBe(
      false,
    );
    expect(
      canBuildWorldPreviewPayload({
        ...validInput,
        worldEntityIdsText: "location_hangar",
        aiResponseText: "not json",
      }),
    ).toBe(false);
  });

  it("allows invalid JSON to be submitted so the form can show a precise error", () => {
    expect(canSubmitCharacterPreviewInput(validInput)).toBe(true);
    expect(canSubmitCharacterPreviewInput({ ...validInput, aiResponseText: "not json" })).toBe(
      true,
    );
    expect(canSubmitCharacterPreviewInput({ ...validInput, aiResponseText: "" })).toBe(false);
    expect(canSubmitCharacterPreviewInput({ ...validInput, sourceText: "" })).toBe(false);
    expect(
      canSubmitWorldPreviewInput({
        ...validInput,
        worldEntityIdsText: "location_hangar",
        aiResponseText: "not json",
      }),
    ).toBe(true);
  });
});

import { describe, expect, it } from "vitest";

import {
  buildCharacterPreviewPayload,
  buildContinuityPreviewPayload,
  buildExportPreviewPayload,
  buildPromptPreviewPayload,
  buildScenePreviewPayload,
  buildTimelinePreviewPayload,
  buildWorldPreviewPayload,
  canBuildCharacterPreviewPayload,
  canBuildContinuityPreviewPayload,
  canBuildExportPreviewPayload,
  canBuildPromptPreviewPayload,
  canBuildScenePreviewPayload,
  canBuildTimelinePreviewPayload,
  canBuildWorldPreviewPayload,
  canSubmitCharacterPreviewInput,
  canSubmitContinuityPreviewInput,
  canSubmitExportPreviewInput,
  canSubmitPromptPreviewInput,
  canSubmitScenePreviewInput,
  canSubmitTimelinePreviewInput,
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

  it("builds timeline preview payloads", () => {
    const payload = buildTimelinePreviewPayload(validInput);

    expect(payload).toMatchObject({
      source_id: "source_demo",
      filename: "chapter.txt",
      title: "Demo",
      ai_response: { entities: [] },
      scene_id: "source_demo_chapter_001_scene_001",
    });
  });

  it("builds scene preview payloads", () => {
    const payload = buildScenePreviewPayload(validInput);

    expect(payload).toMatchObject({
      source_id: "source_demo",
      filename: "chapter.txt",
      title: "Demo",
      ai_response: { entities: [] },
      character_ids: ["character_mark", "character_luna"],
      scene_id: "source_demo_chapter_001_scene_001",
    });
  });

  it("builds prompt preview payloads", () => {
    const payload = buildPromptPreviewPayload(validInput);

    expect(payload).toMatchObject({
      source_id: "source_demo",
      filename: "chapter.txt",
      title: "Demo",
      ai_response: { entities: [] },
      character_ids: ["character_mark", "character_luna"],
      scene_id: "source_demo_chapter_001_scene_001",
    });
  });

  it("builds export preview payloads", () => {
    const payload = buildExportPreviewPayload({
      ...validInput,
      exportKind: " Production_Pack ",
      exportFormat: " Markdown ",
      worldEntityIdsText: "location_hangar item_sword",
    });

    expect(payload).toMatchObject({
      source_id: "source_demo",
      filename: "chapter.txt",
      title: "Demo",
      ai_response: { entities: [] },
      export_kind: "production_pack",
      export_format: "markdown",
      character_ids: ["character_mark", "character_luna"],
      world_entity_ids: ["location_hangar", "item_sword"],
      scene_id: "source_demo_chapter_001_scene_001",
    });
  });

  it("builds continuity preview payloads", () => {
    const payload = buildContinuityPreviewPayload(validInput);

    expect(payload).toMatchObject({
      source_id: "source_demo",
      filename: "chapter.txt",
      title: "Demo",
      ai_response: { entities: [] },
      scene_id: "source_demo_chapter_001_scene_001",
    });
  });

  it("deduplicates repeated preview IDs while preserving first-seen order", () => {
    const characterPayload = buildCharacterPreviewPayload({
      ...validInput,
      characterIdsText: "character_mark character_mark,character_luna character_mark",
    });
    const worldPayload = buildWorldPreviewPayload({
      ...validInput,
      worldEntityIdsText: "location_hangar location_hangar building_fortress",
    });

    expect(characterPayload.character_ids).toEqual(["character_mark", "character_luna"]);
    expect(worldPayload.world_entity_ids).toEqual(["location_hangar", "building_fortress"]);
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
    expect(canBuildTimelinePreviewPayload({ ...validInput, aiResponseText: "not json" })).toBe(
      false,
    );
    expect(canBuildScenePreviewPayload({ ...validInput, aiResponseText: "not json" })).toBe(false);
    expect(canBuildPromptPreviewPayload({ ...validInput, aiResponseText: "not json" })).toBe(
      false,
    );
    expect(
      canBuildExportPreviewPayload({
        ...validInput,
        exportKind: "production_pack",
        exportFormat: "markdown",
        worldEntityIdsText: "",
        aiResponseText: "not json",
      }),
    ).toBe(false);
    expect(canBuildContinuityPreviewPayload({ ...validInput, aiResponseText: "not json" })).toBe(
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
    expect(canSubmitTimelinePreviewInput({ ...validInput, aiResponseText: "not json" })).toBe(
      true,
    );
    expect(canSubmitScenePreviewInput({ ...validInput, aiResponseText: "not json" })).toBe(true);
    expect(canSubmitPromptPreviewInput({ ...validInput, aiResponseText: "not json" })).toBe(true);
    expect(
      canSubmitExportPreviewInput({
        ...validInput,
        exportKind: "production_pack",
        exportFormat: "markdown",
        worldEntityIdsText: "",
        aiResponseText: "not json",
      }),
    ).toBe(true);
    expect(canSubmitContinuityPreviewInput({ ...validInput, aiResponseText: "not json" })).toBe(
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

import { describe, expect, it } from "vitest";

import {
  MAX_IMPORT_SOURCE_CHARACTERS,
  buildImportInspectPayload,
  canBuildImportInspectPayload,
  encodeUtf8Base64,
  importSourceCharacterCountLabel,
} from "./importPayload";

describe("import payload builder", () => {
  it("normalizes import metadata and preserves optional titles", () => {
    expect(
      buildImportInspectPayload({
        sourceId: " source_demo ",
        filename: " chapter_001.txt ",
        title: " Demo Story ",
        sourceText: "Chapter 1\nMark carried a dagger.",
      }),
    ).toMatchObject({
      source_id: "source_demo",
      filename: "chapter_001.txt",
      title: "Demo Story",
    });
  });

  it("omits blank optional titles", () => {
    expect(
      buildImportInspectPayload({
        sourceId: "source_demo",
        filename: "chapter_001.txt",
        title: "   ",
        sourceText: "Chapter 1",
      }),
    ).not.toHaveProperty("title");
  });

  it("rejects missing required fields", () => {
    expect(() =>
      buildImportInspectPayload({
        sourceId: "source_demo",
        filename: " ",
        title: "Demo",
        sourceText: "Chapter 1",
      }),
    ).toThrow("Source ID, filename, and source text are required.");
  });

  it("rejects oversized pasted source text", () => {
    expect(() =>
      buildImportInspectPayload({
        sourceId: "source_demo",
        filename: "chapter_001.txt",
        title: "Demo",
        sourceText: "a".repeat(MAX_IMPORT_SOURCE_CHARACTERS + 1),
      }),
    ).toThrow("Source text must be 500,000 characters or fewer.");
  });

  it("reports whether a payload can be built", () => {
    expect(
      canBuildImportInspectPayload({
        sourceId: "source_demo",
        filename: "chapter_001.txt",
        title: "",
        sourceText: "Chapter 1",
      }),
    ).toBe(true);
    expect(
      canBuildImportInspectPayload({
        sourceId: "source_demo",
        filename: "chapter_001.txt",
        title: "",
        sourceText: "   ",
      }),
    ).toBe(false);
    expect(
      canBuildImportInspectPayload({
        sourceId: "source_demo",
        filename: "chapter_001.txt",
        title: "",
        sourceText: "a".repeat(MAX_IMPORT_SOURCE_CHARACTERS + 1),
      }),
    ).toBe(false);
  });

  it("formats visible source character counts", () => {
    expect(importSourceCharacterCountLabel("Chapter 1")).toBe("9 / 500,000 characters");
  });

  it("encodes Unicode source text as UTF-8 base64", () => {
    const encoded = encodeUtf8Base64("fiancée 你好 星舰");
    const decoded = new TextDecoder().decode(
      Uint8Array.from(atob(encoded), (character) => character.charCodeAt(0)),
    );

    expect(decoded).toBe("fiancée 你好 星舰");
  });
});

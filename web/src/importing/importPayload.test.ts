import { describe, expect, it } from "vitest";

import {
  MAX_IMPORT_SOURCE_CHARACTERS,
  buildImportInspectPayload,
  canBuildImportInspectPayload,
  encodeUtf8Base64,
  encodeBytesBase64,
  importSourceCharacterCountLabel,
  sourceIdFromFilename,
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
    ).toThrow("Source ID, filename, and source content are required.");
  });

  it("builds payloads from selected file bytes", () => {
    expect(
      buildImportInspectPayload({
        sourceId: "source_demo",
        filename: "chapter_001.docx",
        title: "Demo",
        contentBase64: "AAEC",
      }),
    ).toMatchObject({
      source_id: "source_demo",
      filename: "chapter_001.docx",
      content_base64: "AAEC",
      title: "Demo",
    });
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
    expect(
      canBuildImportInspectPayload({
        sourceId: "source_demo",
        filename: "chapter_001.epub",
        title: "",
        contentBase64: "AAEC",
      }),
    ).toBe(true);
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

  it("encodes selected file bytes as base64", () => {
    expect(encodeBytesBase64(new Uint8Array([0, 1, 2, 255]))).toBe("AAEC/w==");
  });

  it("derives source IDs from filenames", () => {
    expect(sourceIdFromFilename("Chapter 001 - Arrival.md")).toBe("chapter_001_arrival");
    expect(sourceIdFromFilename("C:\\Stories\\Book One.epub")).toBe("book_one");
  });
});

import type { ImportInspectRequest } from "../api/client";

export const MAX_IMPORT_SOURCE_CHARACTERS = 500_000;

export type ImportPayloadInput = {
  sourceId: string;
  filename: string;
  title: string;
  sourceText: string;
};

export function buildImportInspectPayload(input: ImportPayloadInput): ImportInspectRequest {
  const sourceId = input.sourceId.trim();
  const filename = input.filename.trim();
  const sourceText = input.sourceText.trim();
  const title = input.title.trim();

  if (!sourceId || !filename || !sourceText) {
    throw new Error("Source ID, filename, and source text are required.");
  }
  if (input.sourceText.length > MAX_IMPORT_SOURCE_CHARACTERS) {
    throw new Error(
      `Source text must be ${MAX_IMPORT_SOURCE_CHARACTERS.toLocaleString()} characters or fewer.`,
    );
  }

  const payload: ImportInspectRequest = {
    source_id: sourceId,
    filename,
    content_base64: encodeUtf8Base64(input.sourceText),
  };
  if (title) {
    payload.title = title;
  }
  return payload;
}

export function canBuildImportInspectPayload(input: ImportPayloadInput): boolean {
  return Boolean(
    input.sourceId.trim() &&
    input.filename.trim() &&
    input.sourceText.trim() &&
    input.sourceText.length <= MAX_IMPORT_SOURCE_CHARACTERS,
  );
}

export function importSourceCharacterCountLabel(value: string): string {
  return `${value.length.toLocaleString()} / ${MAX_IMPORT_SOURCE_CHARACTERS.toLocaleString()} characters`;
}

export function encodeUtf8Base64(value: string): string {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary);
}

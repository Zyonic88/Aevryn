import type { ImportInspectRequest } from "../api/client";

export const MAX_IMPORT_SOURCE_CHARACTERS = 500_000;

export type ImportPayloadInput = {
  sourceId: string;
  filename: string;
  title: string;
  sourceText?: string;
  contentBase64?: string;
};

export function buildImportInspectPayload(input: ImportPayloadInput): ImportInspectRequest {
  const sourceId = input.sourceId.trim();
  const filename = input.filename.trim();
  const sourceText = input.sourceText?.trim() ?? "";
  const contentBase64 = input.contentBase64?.trim() ?? "";
  const title = input.title.trim();

  if (!sourceId || !filename || (!sourceText && !contentBase64)) {
    throw new Error("Source reference, filename, and source content are required.");
  }
  if (!contentBase64 && (input.sourceText?.length ?? 0) > MAX_IMPORT_SOURCE_CHARACTERS) {
    throw new Error(
      `Source text must be ${MAX_IMPORT_SOURCE_CHARACTERS.toLocaleString()} characters or fewer.`,
    );
  }

  const payload: ImportInspectRequest = {
    source_id: sourceId,
    filename,
    content_base64: contentBase64 || encodeUtf8Base64(input.sourceText ?? ""),
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
    ((input.sourceText?.trim() &&
      (input.sourceText?.length ?? 0) <= MAX_IMPORT_SOURCE_CHARACTERS) ||
      input.contentBase64?.trim()),
  );
}

export function importSourceCharacterCountLabel(value: string): string {
  return `${value.length.toLocaleString()} / ${MAX_IMPORT_SOURCE_CHARACTERS.toLocaleString()} characters`;
}

export function encodeUtf8Base64(value: string): string {
  const bytes = new TextEncoder().encode(value);
  return encodeBytesBase64(bytes);
}

export function encodeBytesBase64(bytes: Uint8Array): string {
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary);
}

export function sourceIdFromFilename(filename: string): string {
  const stem = filename.trim().replace(/\\/g, "/").split("/").pop()?.replace(/\.[^.]+$/u, "") ?? "";
  return stem.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

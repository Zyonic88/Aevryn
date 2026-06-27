import {
  buildImportInspectPayload,
  canBuildImportInspectPayload,
} from "../importing/importPayload";

export type CharacterPreviewPayload = ReturnType<typeof buildImportInspectPayload> & {
  ai_response: unknown;
  character_ids: string[];
  scene_id?: string;
};

export type CharacterPreviewInput = {
  sourceId: string;
  filename: string;
  title: string;
  sourceText: string;
  aiResponseText: string;
  characterIdsText: string;
  sceneId: string;
};

export function buildCharacterPreviewPayload(
  input: CharacterPreviewInput,
): CharacterPreviewPayload {
  const basePayload = buildImportInspectPayload(input);
  return {
    ...basePayload,
    ai_response: parseAiResponse(input.aiResponseText),
    character_ids: parseIdList(input.characterIdsText),
    ...(input.sceneId.trim() ? { scene_id: input.sceneId.trim() } : {}),
  };
}

export function canBuildCharacterPreviewPayload(input: CharacterPreviewInput): boolean {
  try {
    buildCharacterPreviewPayload(input);
    return true;
  } catch {
    return false;
  }
}

export function canSubmitCharacterPreviewInput(input: CharacterPreviewInput): boolean {
  return canBuildImportInspectPayload(input) && input.aiResponseText.trim().length > 0;
}

function parseAiResponse(value: string): unknown {
  const normalized = value.trim();
  if (!normalized) {
    throw new Error("AI response JSON is required.");
  }
  try {
    return JSON.parse(normalized) as unknown;
  } catch {
    throw new Error("AI response must be valid JSON.");
  }
}

function parseIdList(value: string): string[] {
  return value
    .split(/[\s,]+/u)
    .map((item) => item.trim())
    .filter(Boolean);
}

import {
  buildImportInspectPayload,
  canBuildImportInspectPayload,
} from "../importing/importPayload";

export type BasePreviewPayload = ReturnType<typeof buildImportInspectPayload> & {
  ai_response: unknown;
  scene_id?: string;
};

export type CharacterPreviewPayload = BasePreviewPayload & {
  character_ids: string[];
};

export type WorldPreviewPayload = BasePreviewPayload & {
  world_entity_ids: string[];
};

export type PreviewInput = {
  sourceId: string;
  filename: string;
  title: string;
  sourceText: string;
  aiResponseText: string;
  sceneId: string;
};

export type CharacterPreviewInput = PreviewInput & {
  characterIdsText: string;
};

export type WorldPreviewInput = PreviewInput & {
  worldEntityIdsText: string;
};

export function buildCharacterPreviewPayload(
  input: CharacterPreviewInput,
): CharacterPreviewPayload {
  return {
    ...buildBasePreviewPayload(input),
    character_ids: parseIdList(input.characterIdsText),
  };
}

export function buildWorldPreviewPayload(input: WorldPreviewInput): WorldPreviewPayload {
  return {
    ...buildBasePreviewPayload(input),
    world_entity_ids: parseIdList(input.worldEntityIdsText),
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

export function canBuildWorldPreviewPayload(input: WorldPreviewInput): boolean {
  try {
    buildWorldPreviewPayload(input);
    return true;
  } catch {
    return false;
  }
}

export function canSubmitCharacterPreviewInput(input: CharacterPreviewInput): boolean {
  return canSubmitPreviewInput(input);
}

export function canSubmitWorldPreviewInput(input: WorldPreviewInput): boolean {
  return canSubmitPreviewInput(input);
}

function buildBasePreviewPayload(input: PreviewInput): BasePreviewPayload {
  const basePayload = buildImportInspectPayload(input);
  return {
    ...basePayload,
    ai_response: parseAiResponse(input.aiResponseText),
    ...(input.sceneId.trim() ? { scene_id: input.sceneId.trim() } : {}),
  };
}

function canSubmitPreviewInput(input: PreviewInput): boolean {
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
  const uniqueIds: string[] = [];
  const seen = new Set<string>();
  for (const item of value.split(/[\s,]+/u)) {
    const id = item.trim();
    if (id && !seen.has(id)) {
      seen.add(id);
      uniqueIds.push(id);
    }
  }
  return uniqueIds;
}

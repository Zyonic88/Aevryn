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

export type TimelinePreviewPayload = BasePreviewPayload;

export type ScenePreviewPayload = BasePreviewPayload & {
  character_ids: string[];
};

export type PromptPreviewPayload = BasePreviewPayload & {
  character_ids: string[];
};

export type ContinuityPreviewPayload = BasePreviewPayload;

export type WorldPreviewPayload = BasePreviewPayload & {
  world_entity_ids: string[];
};

export type ExportPreviewPayload = BasePreviewPayload & {
  export_kind: string;
  export_format: string;
  character_ids: string[];
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

export type ScenePreviewInput = PreviewInput & {
  characterIdsText: string;
};

export type ExportPreviewInput = PreviewInput & {
  characterIdsText: string;
  exportFormat: string;
  exportKind: string;
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

export function buildTimelinePreviewPayload(input: PreviewInput): TimelinePreviewPayload {
  return buildBasePreviewPayload(input);
}

export function buildScenePreviewPayload(input: ScenePreviewInput): ScenePreviewPayload {
  return {
    ...buildBasePreviewPayload(input),
    character_ids: parseIdList(input.characterIdsText),
  };
}

export function buildPromptPreviewPayload(input: ScenePreviewInput): PromptPreviewPayload {
  return {
    ...buildBasePreviewPayload(input),
    character_ids: parseIdList(input.characterIdsText),
  };
}

export function buildContinuityPreviewPayload(
  input: PreviewInput,
): ContinuityPreviewPayload {
  return buildBasePreviewPayload(input);
}

export function buildWorldPreviewPayload(input: WorldPreviewInput): WorldPreviewPayload {
  return {
    ...buildBasePreviewPayload(input),
    world_entity_ids: parseIdList(input.worldEntityIdsText),
  };
}

export function buildExportPreviewPayload(input: ExportPreviewInput): ExportPreviewPayload {
  return {
    ...buildBasePreviewPayload(input),
    export_kind: normalizedRequiredToken(input.exportKind, "Export kind"),
    export_format: normalizedRequiredToken(input.exportFormat, "Export format"),
    character_ids: parseIdList(input.characterIdsText),
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

export function canBuildTimelinePreviewPayload(input: PreviewInput): boolean {
  try {
    buildTimelinePreviewPayload(input);
    return true;
  } catch {
    return false;
  }
}

export function canBuildScenePreviewPayload(input: ScenePreviewInput): boolean {
  try {
    buildScenePreviewPayload(input);
    return true;
  } catch {
    return false;
  }
}

export function canBuildPromptPreviewPayload(input: ScenePreviewInput): boolean {
  try {
    buildPromptPreviewPayload(input);
    return true;
  } catch {
    return false;
  }
}

export function canBuildContinuityPreviewPayload(input: PreviewInput): boolean {
  try {
    buildContinuityPreviewPayload(input);
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

export function canBuildExportPreviewPayload(input: ExportPreviewInput): boolean {
  try {
    buildExportPreviewPayload(input);
    return true;
  } catch {
    return false;
  }
}

export function canSubmitCharacterPreviewInput(input: CharacterPreviewInput): boolean {
  return canSubmitPreviewInput(input);
}

export function canSubmitTimelinePreviewInput(input: PreviewInput): boolean {
  return canSubmitPreviewInput(input);
}

export function canSubmitScenePreviewInput(input: ScenePreviewInput): boolean {
  return canSubmitPreviewInput(input);
}

export function canSubmitPromptPreviewInput(input: ScenePreviewInput): boolean {
  return canSubmitPreviewInput(input);
}

export function canSubmitContinuityPreviewInput(input: PreviewInput): boolean {
  return canSubmitPreviewInput(input);
}

export function canSubmitWorldPreviewInput(input: WorldPreviewInput): boolean {
  return canSubmitPreviewInput(input);
}

export function canSubmitExportPreviewInput(input: ExportPreviewInput): boolean {
  return (
    canSubmitPreviewInput(input) &&
    input.exportKind.trim().length > 0 &&
    input.exportFormat.trim().length > 0
  );
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

function normalizedRequiredToken(value: string, label: string): string {
  const normalized = value.trim().toLowerCase();
  if (!normalized) {
    throw new Error(`${label} is required.`);
  }
  return normalized;
}

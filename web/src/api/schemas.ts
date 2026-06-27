import { z } from "zod";

export const healthSchema = z.object({
  status: z.string(),
  api_version: z.string(),
  engine: z.string(),
});

export const routeCapabilitySchema = z.object({
  method: z.string(),
  path: z.string(),
  purpose: z.string(),
});

export const sourceFormatSchema = z.object({
  extension: z.string(),
  status: z.string(),
  adapter: z.string(),
  evidence_anchor_status: z.string(),
  notes: z.string(),
});

export const sourceFormatsSchema = z.object({
  supported: z.array(sourceFormatSchema),
  deferred: z.array(sourceFormatSchema),
});

export const exportCapabilitySchema = z.object({
  export_kind: z.string(),
  formats: z.array(z.string()),
});

export const capabilitiesSchema = z.object({
  api_version: z.string(),
  engine: z.string(),
  phase: z.string(),
  routes: z.array(routeCapabilitySchema),
  source_formats: sourceFormatsSchema,
  export_capabilities: z.array(exportCapabilitySchema),
  platform_limits: z.array(z.string()),
});

export const authSessionSchema = z.object({
  user_id: z.string(),
  email: z.string(),
  display_name: z.string(),
  session_token: z.string(),
  expires_at: z.string(),
});

export const authMeSchema = z.object({
  user_id: z.string(),
  email: z.string(),
  display_name: z.string(),
});

export const evidenceAnchorPreviewSchema = z.object({
  anchor_id: z.string(),
  chapter_id: z.string(),
  scene_id: z.string(),
  paragraph_index: z.number(),
  sentence_index: z.number(),
});

export const sceneMapEntrySchema = z.object({
  chapter_id: z.string(),
  chapter_index: z.number(),
  scene_id: z.string(),
  scene_index: z.number(),
  title: z.string(),
});

export const importInspectSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  title: z.string(),
  chapters: z.number(),
  chapter_ids: z.array(z.string()),
  scenes: z.number(),
  scene_ids: z.array(z.string()),
  scene_map: z.array(sceneMapEntrySchema),
  paragraphs: z.number(),
  evidence_anchors: z.number(),
  first_evidence_anchors: z.array(evidenceAnchorPreviewSchema),
});

export const outputSectionSchema = z.object({
  title: z.string(),
  items: z.array(z.string()),
});

export const characterProfileSchema = z.object({
  character_id: z.string(),
  display_name: z.string(),
  subtitle: z.string(),
  status: outputSectionSchema,
  current_goal: outputSectionSchema,
  current_equipment: outputSectionSchema,
  current_abilities: outputSectionSchema,
  current_assets: outputSectionSchema,
  territory: outputSectionSchema,
  relationships: outputSectionSchema,
  current_limitations: outputSectionSchema,
  recent_changes: outputSectionSchema,
  evidence_summary: z.string(),
});

export const characterPreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  scene_id: z.string(),
  character_profiles: z.array(characterProfileSchema),
});

export const worldSheetSchema = z.object({
  chapter_label: z.string(),
  entity_sections: z.array(outputSectionSchema),
  evidence_summary: z.string(),
});

export const worldPreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  scene_id: z.string(),
  world_sheet: worldSheetSchema,
});

export type ApiHealth = z.infer<typeof healthSchema>;
export type ApiCapabilities = z.infer<typeof capabilitiesSchema>;
export type SourceFormats = z.infer<typeof sourceFormatsSchema>;
export type ImportInspect = z.infer<typeof importInspectSchema>;
export type OutputSection = z.infer<typeof outputSectionSchema>;
export type CharacterProfile = z.infer<typeof characterProfileSchema>;
export type CharacterPreview = z.infer<typeof characterPreviewSchema>;
export type WorldSheet = z.infer<typeof worldSheetSchema>;
export type WorldPreview = z.infer<typeof worldPreviewSchema>;
export type AuthSession = z.infer<typeof authSessionSchema>;
export type AuthUser = z.infer<typeof authMeSchema>;

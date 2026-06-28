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

export const projectSchema = z.object({
  project_id: z.string(),
  name: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const projectListSchema = z.object({
  projects: z.array(projectSchema),
});

export const projectSettingsSchema = z.object({
  project_id: z.string(),
  default_export_format: z.string(),
  locale: z.string(),
});

export const storySchema = z.object({
  story_id: z.string(),
  project_id: z.string(),
  title: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const storyListSchema = z.object({
  stories: z.array(storySchema),
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

export const timelinePreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  current_scene_id: z.string(),
  chapter_ids: z.array(z.string()),
  scene_map: z.array(sceneMapEntrySchema),
  accepted_state_change_ids: z.array(z.string()),
});

export const sceneSheetSchema = z.object({
  scene_id: z.string(),
  title: z.string(),
  chapter_label: z.string(),
  location: outputSectionSchema,
  characters_present: outputSectionSchema,
  mood: outputSectionSchema,
  purpose: outputSectionSchema,
  visual_highlights: outputSectionSchema,
  continuity_changes: outputSectionSchema,
  environment: outputSectionSchema,
  evidence_summary: z.string(),
});

export const scenePreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  scene_id: z.string(),
  scene_sheet: sceneSheetSchema,
});

export const productionPackSchema = z.object({
  scene: sceneSheetSchema,
  image_prompt: outputSectionSchema,
  narration_prompt: outputSectionSchema,
  camera_prompt: outputSectionSchema,
  animation_prompt: outputSectionSchema,
});

export const promptPreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  scene_id: z.string(),
  production_pack: productionPackSchema,
});

export const exportPreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  scene_id: z.string(),
  export_kind: z.string(),
  export_format: z.string(),
  filename: z.string(),
  content_type: z.string(),
  content: z.string(),
});

export const continuityRecordSchema = z.object({
  record_id: z.string(),
  record_type: z.string(),
  description: z.string(),
  evidence_id: z.string(),
  chapter_id: z.string(),
  scene_id: z.string(),
});

export const continuitySceneSchema = z.object({
  scene_id: z.string(),
  new: z.array(continuityRecordSchema),
  updated: z.array(continuityRecordSchema),
  still_known: z.array(continuityRecordSchema),
  invalidated: z.array(continuityRecordSchema),
});

export const continuityReportSchema = z.object({
  source_id: z.string(),
  scenes: z.array(continuitySceneSchema),
});

export const continuityPreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  continuity_report: continuityReportSchema,
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
export type SceneMapEntry = z.infer<typeof sceneMapEntrySchema>;
export type OutputSection = z.infer<typeof outputSectionSchema>;
export type CharacterProfile = z.infer<typeof characterProfileSchema>;
export type CharacterPreview = z.infer<typeof characterPreviewSchema>;
export type TimelinePreview = z.infer<typeof timelinePreviewSchema>;
export type SceneSheet = z.infer<typeof sceneSheetSchema>;
export type ScenePreview = z.infer<typeof scenePreviewSchema>;
export type ProductionPack = z.infer<typeof productionPackSchema>;
export type PromptPreview = z.infer<typeof promptPreviewSchema>;
export type ExportPreview = z.infer<typeof exportPreviewSchema>;
export type ContinuityRecord = z.infer<typeof continuityRecordSchema>;
export type ContinuityScene = z.infer<typeof continuitySceneSchema>;
export type ContinuityReport = z.infer<typeof continuityReportSchema>;
export type ContinuityPreview = z.infer<typeof continuityPreviewSchema>;
export type WorldSheet = z.infer<typeof worldSheetSchema>;
export type WorldPreview = z.infer<typeof worldPreviewSchema>;
export type AuthSession = z.infer<typeof authSessionSchema>;
export type AuthUser = z.infer<typeof authMeSchema>;
export type Project = z.infer<typeof projectSchema>;
export type ProjectList = z.infer<typeof projectListSchema>;
export type ProjectSettings = z.infer<typeof projectSettingsSchema>;
export type Story = z.infer<typeof storySchema>;
export type StoryList = z.infer<typeof storyListSchema>;

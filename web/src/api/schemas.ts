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

export type ApiHealth = z.infer<typeof healthSchema>;
export type ApiCapabilities = z.infer<typeof capabilitiesSchema>;
export type AuthSession = z.infer<typeof authSessionSchema>;
export type AuthUser = z.infer<typeof authMeSchema>;

import { z } from "zod";

import {
  authMeSchema,
  authSessionSchema,
  capabilitiesSchema,
  characterPreviewSchema,
  healthSchema,
  importInspectSchema,
  sourceFormatsSchema,
  type ApiCapabilities,
  type ApiHealth,
  type AuthSession,
  type AuthUser,
  type CharacterPreview,
  type ImportInspect,
  type SourceFormats,
} from "./schemas";

export const API_PATHS = {
  health: "/v2/health",
  capabilities: "/v2/capabilities",
  sourceFormats: "/v2/source-formats",
  importsInspect: "/v2/imports/inspect",
  charactersPreview: "/v2/characters/preview",
  authRegister: "/v2/auth/register",
  authLogin: "/v2/auth/login",
  authMe: "/v2/auth/me",
} as const;

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export type LoginRequest = {
  email: string;
  password: string;
  now: string;
};

export type RegisterRequest = LoginRequest & {
  user_id: string;
  display_name: string;
};

export type ImportInspectRequest = {
  source_id: string;
  filename: string;
  content_base64: string;
  title?: string;
};

export type CharacterPreviewRequest = ImportInspectRequest & {
  ai_response: unknown;
  character_ids?: string[];
  scene_id?: string;
};

export class AevrynApiClient {
  readonly baseUrl: string;

  constructor(baseUrl: string = import.meta.env.VITE_AEVRYN_API_URL ?? "") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  health(): Promise<ApiHealth> {
    return this.request(API_PATHS.health, healthSchema);
  }

  capabilities(): Promise<ApiCapabilities> {
    return this.request(API_PATHS.capabilities, capabilitiesSchema);
  }

  sourceFormats(): Promise<SourceFormats> {
    return this.request(API_PATHS.sourceFormats, sourceFormatsSchema);
  }

  inspectImport(payload: ImportInspectRequest): Promise<ImportInspect> {
    return this.request(API_PATHS.importsInspect, importInspectSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  previewCharacters(payload: CharacterPreviewRequest): Promise<CharacterPreview> {
    return this.request(API_PATHS.charactersPreview, characterPreviewSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  register(payload: RegisterRequest): Promise<AuthSession> {
    return this.request(API_PATHS.authRegister, authSessionSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  login(payload: LoginRequest): Promise<AuthSession> {
    return this.request(API_PATHS.authLogin, authSessionSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  me(sessionToken: string, now: string): Promise<AuthUser> {
    return this.request(API_PATHS.authMe, authMeSchema, {
      headers: {
        Authorization: `Bearer ${sessionToken}`,
        "X-Aevryn-Now": now,
      },
    });
  }

  private async request<T>(path: string, schema: z.ZodType<T>, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (init.body) {
      headers.set("Content-Type", "application/json");
    }

    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, { ...init, headers });
    } catch (error) {
      throw new ApiError(
        messageFromUnknown(error, "Aevryn API is unreachable."),
        0,
        "network_error",
      );
    }

    const payload = await readJsonPayload(response);
    if (!response.ok) {
      const errorPayload = z
        .object({ error: z.string().optional(), detail: z.string().optional() })
        .safeParse(payload);
      throw new ApiError(
        errorPayload.data?.detail ?? "Aevryn API request failed.",
        response.status,
        errorPayload.data?.error ?? "request_failed",
      );
    }

    const parsed = schema.safeParse(payload);
    if (!parsed.success) {
      throw new ApiError(
        "Aevryn API returned an unexpected response shape.",
        response.status,
        "invalid_response",
      );
    }
    return parsed.data;
  }
}

async function readJsonPayload(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    if (response.ok) {
      throw new ApiError("Aevryn API returned invalid JSON.", response.status, "invalid_json");
    }
    return {};
  }
}

function messageFromUnknown(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

export const apiClient = new AevrynApiClient();

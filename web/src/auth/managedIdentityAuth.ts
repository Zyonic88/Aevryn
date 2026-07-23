import { apiClient, postJson, type LoginRequest, type RegisterRequest } from "../api/client";
import { authSessionSchema, type AuthSession } from "../api/schemas";

type SupabaseAuthUser = {
  id?: unknown;
  email?: unknown;
  user_metadata?: unknown;
};

type SupabaseAuthResponse = {
  access_token?: unknown;
  refresh_token?: unknown;
  expires_at?: unknown;
  expires_in?: unknown;
  user?: SupabaseAuthUser | null;
  error?: unknown;
  error_description?: unknown;
  msg?: unknown;
};

const SUPABASE_URL = normalizeBaseUrl(import.meta.env.VITE_SUPABASE_URL);
const SUPABASE_ANON_KEY = String(import.meta.env.VITE_SUPABASE_ANON_KEY ?? "").trim();

export function isManagedIdentityAuthConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
}

export function loginWithConfiguredAuth(payload: LoginRequest): Promise<AuthSession> {
  if (!isManagedIdentityAuthConfigured()) {
    return apiClient.login(payload);
  }
  return supabasePasswordAuth({
    path: "/auth/v1/token?grant_type=password",
    body: {
      email: payload.email,
      password: payload.password,
    },
    fallbackEmail: payload.email,
  });
}

export function registerWithConfiguredAuth(payload: RegisterRequest): Promise<AuthSession> {
  if (!isManagedIdentityAuthConfigured()) {
    return apiClient.register(payload);
  }
  return supabasePasswordAuth({
    path: "/auth/v1/signup",
    body: {
      email: payload.email,
      password: payload.password,
      data: {
        display_name: payload.display_name,
        full_name: payload.display_name,
      },
    },
    fallbackEmail: payload.email,
    fallbackDisplayName: payload.display_name,
  });
}

export async function refreshConfiguredAuthSession(session: AuthSession): Promise<AuthSession> {
  if (!isManagedIdentityAuthConfigured()) {
    return session;
  }
  const refreshToken = textValue(session.refresh_token);
  if (!refreshToken) {
    throw new Error("Session refresh is unavailable. Please log in again.");
  }
  return supabasePasswordAuth({
    path: "/auth/v1/token?grant_type=refresh_token",
    body: {
      refresh_token: refreshToken,
    },
    fallbackEmail: session.email,
    fallbackDisplayName: session.display_name,
  });
}

export async function requestConfiguredPasswordRecovery({
  email,
  redirectTo,
}: {
  email: string;
  redirectTo: string;
}): Promise<void> {
  if (!isManagedIdentityAuthConfigured()) {
    throw new Error("Password recovery requires the managed identity provider.");
  }

  const response = await supabaseAuthRequest({
    path: `/auth/v1/recover?redirect_to=${encodeURIComponent(redirectTo)}`,
    body: { email },
    authorizationToken: SUPABASE_ANON_KEY,
  });
  if (!response.ok) {
    throw new Error(supabaseErrorMessage(readSupabasePayload(response.payload)));
  }
}

export async function completeConfiguredPasswordRecovery({
  accessToken,
  password,
}: {
  accessToken: string;
  password: string;
}): Promise<void> {
  if (!isManagedIdentityAuthConfigured()) {
    throw new Error("Password recovery requires the managed identity provider.");
  }
  const token = textValue(accessToken);
  if (!token) {
    throw new Error("Password recovery link is invalid or expired.");
  }

  const response = await supabaseAuthRequest({
    path: "/auth/v1/user",
    method: "PUT",
    body: { password },
    authorizationToken: token,
  });
  if (!response.ok) {
    throw new Error(supabaseErrorMessage(readSupabasePayload(response.payload)));
  }
}

async function supabasePasswordAuth({
  path,
  body,
  fallbackEmail,
  fallbackDisplayName,
}: {
  path: string;
  body: Record<string, unknown>;
  fallbackEmail: string;
  fallbackDisplayName?: string;
}): Promise<AuthSession> {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    throw new Error("Managed identity provider is not configured.");
  }

  try {
    const response = await supabaseAuthRequest({
      path,
      body,
      authorizationToken: SUPABASE_ANON_KEY,
    });
    const payload = readSupabasePayload(response.payload);
    if (!response.ok) {
      throw new Error(supabaseErrorMessage(payload));
    }

    const session = authSessionFromSupabase(payload, {
      fallbackEmail,
      fallbackDisplayName,
    });
    const parsed = authSessionSchema.safeParse(session);
    if (!parsed.success) {
      throw new Error(
        "Managed identity provider did not return a usable session. Check email confirmation settings.",
      );
    }
    return parsed.data;
  } catch (error) {
    if (error instanceof Error && error.message) {
      throw error;
    }
    throw new Error("Managed identity provider is unreachable.");
  }
}

async function supabaseAuthRequest({
  path,
  body,
  authorizationToken,
  method = "POST",
}: {
  path: string;
  body: Record<string, unknown>;
  authorizationToken: string;
  method?: "POST" | "PUT";
}) {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    throw new Error("Managed identity provider is not configured.");
  }
  const response = await postJson(`${SUPABASE_URL}${path}`, {
    method,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${authorizationToken}`,
    },
    body,
  });
  return response;
}

function readSupabasePayload(payload: unknown): SupabaseAuthResponse {
  return typeof payload === "object" && payload !== null
    ? (payload as SupabaseAuthResponse)
    : {};
}

function authSessionFromSupabase(
  payload: SupabaseAuthResponse,
  {
    fallbackEmail,
    fallbackDisplayName,
  }: {
    fallbackEmail: string;
    fallbackDisplayName?: string;
  },
): AuthSession {
  const accessToken = textValue(payload.access_token);
  const user = typeof payload.user === "object" && payload.user !== null ? payload.user : {};
  const email = textValue(user.email) || fallbackEmail;
  const displayName = displayNameFromUser(user, fallbackDisplayName, email);
  return {
    user_id: textValue(user.id),
    email,
    display_name: displayName,
    session_token: accessToken,
    refresh_token: textValue(payload.refresh_token),
    expires_at: expiresAtFromSupabase(payload),
  };
}

function displayNameFromUser(
  user: SupabaseAuthUser,
  fallbackDisplayName: string | undefined,
  email: string,
): string {
  const metadata = user.user_metadata;
  if (typeof metadata === "object" && metadata !== null) {
    const values = metadata as Record<string, unknown>;
    for (const key of ["display_name", "full_name", "name"]) {
      const value = textValue(values[key]);
      if (value) {
        return value;
      }
    }
  }
  if (fallbackDisplayName?.trim()) {
    return fallbackDisplayName.trim();
  }
  return email.split("@", 1)[0] || "Aevryn User";
}

function expiresAtFromSupabase(payload: SupabaseAuthResponse): string {
  if (typeof payload.expires_at === "number" && Number.isFinite(payload.expires_at)) {
    return new Date(payload.expires_at * 1000).toISOString();
  }
  if (typeof payload.expires_in === "number" && Number.isFinite(payload.expires_in)) {
    return new Date(Date.now() + payload.expires_in * 1000).toISOString();
  }
  return new Date(Date.now() + 60 * 60 * 1000).toISOString();
}

function supabaseErrorMessage(payload: SupabaseAuthResponse): string {
  return (
    textValue(payload.error_description) ||
    textValue(payload.msg) ||
    textValue(payload.error) ||
    "Managed identity provider rejected the request."
  );
}

function textValue(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function normalizeBaseUrl(value: unknown): string {
  if (typeof value !== "string") {
    return "";
  }
  const trimmed = value.trim().replace(/\/$/, "");
  if (!trimmed) {
    return "";
  }
  try {
    const parsed = new URL(trimmed);
    return parsed.protocol === "https:" ? parsed.toString().replace(/\/$/, "") : "";
  } catch {
    return "";
  }
}

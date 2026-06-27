import { authSessionSchema, type AuthSession } from "../api/schemas";

const SESSION_STORAGE_KEY = "aevryn.session";

export type StoredSession = AuthSession;

export function readStoredSession(
  storage: Storage = window.localStorage,
  now: Date = new Date(),
): StoredSession | null {
  const rawSession = safeGetItem(storage, SESSION_STORAGE_KEY);
  if (!rawSession) {
    return null;
  }
  try {
    const parsedSession = authSessionSchema.safeParse(JSON.parse(rawSession));
    if (!parsedSession.success || isSessionExpired(parsedSession.data, now)) {
      safeRemoveItem(storage, SESSION_STORAGE_KEY);
      return null;
    }
    return parsedSession.data;
  } catch {
    safeRemoveItem(storage, SESSION_STORAGE_KEY);
    return null;
  }
}

export function writeStoredSession(
  session: StoredSession,
  storage: Storage = window.localStorage,
): boolean {
  return safeSetItem(storage, SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function clearStoredSession(storage: Storage = window.localStorage): boolean {
  return safeRemoveItem(storage, SESSION_STORAGE_KEY);
}

export function isSessionExpired(session: StoredSession, now: Date = new Date()): boolean {
  const expiresAt = Date.parse(session.expires_at);
  if (Number.isNaN(expiresAt)) {
    return true;
  }
  return expiresAt <= now.getTime();
}

function safeGetItem(storage: Storage, key: string): string | null {
  try {
    return storage.getItem(key);
  } catch {
    return null;
  }
}

function safeSetItem(storage: Storage, key: string, value: string): boolean {
  try {
    storage.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

function safeRemoveItem(storage: Storage, key: string): boolean {
  try {
    storage.removeItem(key);
    return true;
  } catch {
    return false;
  }
}

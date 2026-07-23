import { useEffect, useMemo, useState, type PropsWithChildren } from "react";

import type { AuthSession } from "../api/schemas";
import { AuthContext, type AuthContextValue } from "./authContext";
import { refreshConfiguredAuthSession } from "./managedIdentityAuth";
import {
  clearStoredSession,
  isSessionExpired,
  isSessionRefreshable,
  readStoredSession,
  writeStoredSession,
} from "./session";

const SESSION_PERSISTENCE_ERROR =
  "Session storage failed. You are signed in for this tab, but may need to log in again after refresh.";
const SESSION_REFRESH_ERROR = "Your session expired. Please log in again.";
const SESSION_REFRESH_LEEWAY_MS = 5 * 60 * 1000;

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSessionState] = useState<AuthSession | null>(() => readStoredSession());
  const [sessionPersistenceError, setSessionPersistenceError] = useState<string | null>(null);
  const [isSessionRestoring, setIsSessionRestoring] = useState(() =>
    shouldRefreshSession(readStoredSession()),
  );

  useEffect(() => {
    if (!session || !isSessionRefreshable(session)) {
      return;
    }

    let canceled = false;
    const timeout = window.setTimeout(() => {
      if (canceled) {
        return;
      }
      setIsSessionRestoring(isSessionExpired(session));
      void refreshConfiguredAuthSession(session)
        .then((nextSession) => {
          if (canceled) {
            return;
          }
          const persisted = writeStoredSession(nextSession);
          setSessionPersistenceError(persisted ? null : SESSION_PERSISTENCE_ERROR);
          setSessionState(nextSession);
          setIsSessionRestoring(false);
        })
        .catch(() => {
          if (canceled) {
            return;
          }
          clearStoredSession();
          setSessionPersistenceError(SESSION_REFRESH_ERROR);
          setSessionState(null);
          setIsSessionRestoring(false);
        });
    }, refreshDelayMs(session));

    return () => {
      canceled = true;
      window.clearTimeout(timeout);
    };
  }, [session]);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      isAuthenticated: session !== null,
      isSessionRestoring,
      sessionPersistenceError,
      clearSessionPersistenceError() {
        setSessionPersistenceError(null);
      },
      invalidateSession(reason) {
        clearStoredSession();
        setSessionPersistenceError(reason);
        setIsSessionRestoring(false);
        setSessionState(null);
      },
      setSession(nextSession) {
        const persisted = writeStoredSession(nextSession);
        setSessionPersistenceError(persisted ? null : SESSION_PERSISTENCE_ERROR);
        setIsSessionRestoring(false);
        setSessionState(nextSession);
      },
      logout() {
        clearStoredSession();
        setSessionPersistenceError(null);
        setIsSessionRestoring(false);
        setSessionState(null);
      },
    }),
    [session, isSessionRestoring, sessionPersistenceError],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function shouldRefreshSession(session: AuthSession | null): boolean {
  return Boolean(session && isSessionRefreshable(session) && isSessionExpired(session));
}

function refreshDelayMs(session: AuthSession): number {
  const expiresAt = Date.parse(session.expires_at);
  if (Number.isNaN(expiresAt)) {
    return 0;
  }
  return Math.max(0, expiresAt - Date.now() - SESSION_REFRESH_LEEWAY_MS);
}

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
const SESSION_INACTIVITY_ERROR = "You were logged out after 30 minutes of inactivity.";
const SESSION_REFRESH_LEEWAY_MS = 5 * 60 * 1000;
const SESSION_INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000;
const SESSION_ACTIVITY_EVENTS = ["pointerdown", "keydown", "scroll", "focus"] as const;

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

  useEffect(() => {
    if (!session) {
      return;
    }

    let timeout = window.setTimeout(expireInactiveSession, SESSION_INACTIVITY_TIMEOUT_MS);

    function resetInactivityTimer() {
      window.clearTimeout(timeout);
      timeout = window.setTimeout(expireInactiveSession, SESSION_INACTIVITY_TIMEOUT_MS);
    }

    function expireInactiveSession() {
      clearStoredSession();
      setSessionPersistenceError(SESSION_INACTIVITY_ERROR);
      setIsSessionRestoring(false);
      setSessionState(null);
    }

    for (const eventName of SESSION_ACTIVITY_EVENTS) {
      window.addEventListener(eventName, resetInactivityTimer, { passive: true });
    }

    return () => {
      window.clearTimeout(timeout);
      for (const eventName of SESSION_ACTIVITY_EVENTS) {
        window.removeEventListener(eventName, resetInactivityTimer);
      }
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

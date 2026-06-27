import { useMemo, useState, type PropsWithChildren } from "react";

import type { AuthSession } from "../api/schemas";
import { AuthContext, type AuthContextValue } from "./authContext";
import { clearStoredSession, readStoredSession, writeStoredSession } from "./session";

const SESSION_PERSISTENCE_ERROR =
  "Session storage failed. You are signed in for this tab, but may need to log in again after refresh.";

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSessionState] = useState<AuthSession | null>(() => readStoredSession());
  const [sessionPersistenceError, setSessionPersistenceError] = useState<string | null>(null);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      isAuthenticated: session !== null,
      sessionPersistenceError,
      clearSessionPersistenceError() {
        setSessionPersistenceError(null);
      },
      setSession(nextSession) {
        const persisted = writeStoredSession(nextSession);
        setSessionPersistenceError(persisted ? null : SESSION_PERSISTENCE_ERROR);
        setSessionState(nextSession);
      },
      logout() {
        clearStoredSession();
        setSessionPersistenceError(null);
        setSessionState(null);
      },
    }),
    [session, sessionPersistenceError],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

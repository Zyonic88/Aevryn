import { createContext } from "react";

import type { AuthSession } from "../api/schemas";

export type AuthContextValue = {
  session: AuthSession | null;
  isAuthenticated: boolean;
  sessionPersistenceError: string | null;
  clearSessionPersistenceError: () => void;
  setSession: (session: AuthSession) => void;
  logout: () => void;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

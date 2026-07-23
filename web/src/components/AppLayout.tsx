import { useLayoutEffect } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";

import { setAuthenticationFailureHandler } from "../api/client";
import { useAuth } from "../auth/useAuth";
import { ErrorMessage } from "./Feedback";

const AUTHENTICATION_RECOVERY_MESSAGE = "Your session expired. Please log in again.";

export function AppLayout() {
  const navigate = useNavigate();
  const { session, sessionPersistenceError, invalidateSession, logout } = useAuth();

  useLayoutEffect(() => {
    setAuthenticationFailureHandler(() => {
      invalidateSession(AUTHENTICATION_RECOVERY_MESSAGE);
      void navigate("/login", { replace: true });
    });
    return () => setAuthenticationFailureHandler(null);
  }, [invalidateSession, navigate]);

  function submitLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-frame">
      <header className="topbar">
        <Link to="/" className="brand" aria-label="Aevryn dashboard">
          <span className="brand-mark">A</span>
          <span>
            <strong>Aevryn</strong>
            <small>Evidence in. Canon out.</small>
          </span>
        </Link>
        <nav className="topnav" aria-label="Primary navigation">
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/trust">Trust</NavLink>
          <NavLink to="/support">Support</NavLink>
        </nav>
        <div className="account-chip">
          <span>{session?.display_name}</span>
          <button type="button" className="ghost-button" onClick={submitLogout}>
            Log out
          </button>
        </div>
      </header>
      {sessionPersistenceError ? (
        <div className="shell-alert">
          <ErrorMessage>{sessionPersistenceError}</ErrorMessage>
        </div>
      ) : null}
      <main className="main-surface">
        <Outlet />
      </main>
    </div>
  );
}

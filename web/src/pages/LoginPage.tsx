import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import type { LoginRequest } from "../api/client";
import { buildLoginPayload } from "../auth/formValidation";
import { loginWithConfiguredAuth } from "../auth/managedIdentityAuth";
import { useAuth } from "../auth/useAuth";
import { ErrorMessage } from "../components/Feedback";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { clearSessionPersistenceError, sessionPersistenceError, setSession } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const loginMessage = loginMessageFromLocationState(location.state);

  const login = useMutation({
    mutationFn: (payload: LoginRequest) => loginWithConfiguredAuth(payload),
    onSuccess(session) {
      setSession(session);
      navigate("/dashboard");
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const payload = buildLoginPayload({ email, password });
      setFormError(null);
      clearSessionPersistenceError();
      login.mutate({ ...payload, now: new Date().toISOString() });
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Login form is invalid.");
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-panel">
        <div>
          <p className="eyebrow">Aevryn</p>
          <h1>Log in</h1>
        </div>
        <form onSubmit={submit} className="form-stack">
          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {formError ? <ErrorMessage>{formError}</ErrorMessage> : null}
          {sessionPersistenceError ? <ErrorMessage>{sessionPersistenceError}</ErrorMessage> : null}
          {login.error ? <ErrorMessage>{login.error.message}</ErrorMessage> : null}
          {loginMessage ? (
            <p className="success-note" role="status">
              {loginMessage}
            </p>
          ) : null}
          <button type="submit" className="primary-button" disabled={login.isPending}>
            {login.isPending ? "Logging in" : "Log in"}
          </button>
        </form>
        <p className="auth-switch">
          New to Aevryn? <Link to="/register">Create an account</Link>
        </p>
        <p className="auth-switch">
          Need access? <Link to="/password-recovery">Reset your password</Link>
        </p>
        <nav className="auth-links" aria-label="Public information">
          <Link to="/trust">Trust</Link>
          <Link to="/support">Support</Link>
          <Link to="/privacy">Privacy</Link>
        </nav>
      </section>
    </main>
  );
}

function loginMessageFromLocationState(state: unknown): string | null {
  if (typeof state !== "object" || state === null || !("message" in state)) {
    return null;
  }
  const message = (state as { message?: unknown }).message;
  return typeof message === "string" && message.trim() ? message.trim() : null;
}

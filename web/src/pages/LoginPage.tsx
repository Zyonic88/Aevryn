import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import type { LoginRequest } from "../api/client";
import { buildLoginPayload } from "../auth/formValidation";
import { loginWithConfiguredAuth } from "../auth/managedIdentityAuth";
import { recoveryPath } from "../auth/recoveryPath";
import { useAuth } from "../auth/useAuth";
import { ErrorMessage } from "../components/Feedback";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setSession } = useAuth();
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const login = useMutation({
    mutationFn: (payload: LoginRequest) => loginWithConfiguredAuth(payload),
    onSuccess(session) {
      setSession(session);
      navigate(recoveryPath(location.state));
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const payload = buildLoginPayload({ email, password });
      setFormError(null);
      login.mutate({ ...payload, now: new Date().toISOString() });
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Login form is invalid.");
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-panel">
        <div>
          <p className="eyebrow">Aevryn Web Alpha Shell</p>
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
          {login.error ? <ErrorMessage>{login.error.message}</ErrorMessage> : null}
          <button type="submit" className="primary-button" disabled={login.isPending}>
            {login.isPending ? "Logging in" : "Log in"}
          </button>
        </form>
        <p className="auth-switch">
          New to Aevryn? <Link to="/register">Create an account</Link>
        </p>
      </section>
    </main>
  );
}

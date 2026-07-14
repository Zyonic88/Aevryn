import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import type { RegisterRequest } from "../api/client";
import { buildRegisterPayload } from "../auth/formValidation";
import { registerWithConfiguredAuth } from "../auth/managedIdentityAuth";
import { useAuth } from "../auth/useAuth";
import { ErrorMessage } from "../components/Feedback";

export function RegisterPage() {
  const navigate = useNavigate();
  const { setSession } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const register = useMutation({
    mutationFn: (payload: RegisterRequest) => registerWithConfiguredAuth(payload),
    onSuccess(session) {
      setSession(session);
      navigate("/dashboard");
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const payload = buildRegisterPayload({ displayName, email, password });
      setFormError(null);
      register.mutate({
        user_id: payload.userId,
        display_name: payload.displayName,
        email: payload.email,
        password: payload.password,
        now: new Date().toISOString(),
      });
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Registration form is invalid.");
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-panel">
        <div>
          <p className="eyebrow">Aevryn</p>
          <h1>Create account</h1>
        </div>
        <form onSubmit={submit} className="form-stack">
          <label>
            Display name
            <input
              autoComplete="name"
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
            />
          </label>
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
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {formError ? <ErrorMessage>{formError}</ErrorMessage> : null}
          {register.error ? <ErrorMessage>{register.error.message}</ErrorMessage> : null}
          <button type="submit" className="primary-button" disabled={register.isPending}>
            {register.isPending ? "Creating account" : "Create account"}
          </button>
        </form>
        <p className="auth-switch">
          Already have access? <Link to="/login">Log in</Link>
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

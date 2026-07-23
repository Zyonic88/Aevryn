import { useMutation } from "@tanstack/react-query";
import { FormEvent, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import {
  buildPasswordRecoveryPayload,
  buildPasswordUpdatePayload,
} from "../auth/formValidation";
import {
  completeConfiguredPasswordRecovery,
  requestConfiguredPasswordRecovery,
} from "../auth/managedIdentityAuth";
import { useAuth } from "../auth/useAuth";
import { ErrorMessage } from "../components/Feedback";

const RECOVERY_SENT_MESSAGE =
  "If an account exists for that email, Aevryn will send a password reset link.";

export function PasswordRecoveryPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const recoveryToken = useMemo(() => recoveryTokenFromLocation(location), [location]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [requestSent, setRequestSent] = useState(false);

  const requestRecovery = useMutation({
    mutationFn: (payload: { email: string; redirectTo: string }) =>
      requestConfiguredPasswordRecovery(payload),
    onSuccess() {
      setRequestSent(true);
    },
  });
  const completeRecovery = useMutation({
    mutationFn: (payload: { accessToken: string; password: string }) =>
      completeConfiguredPasswordRecovery(payload),
    onSuccess() {
      logout();
      navigate("/login", {
        replace: true,
        state: { message: "Password updated. Log in with your new password." },
      });
    },
  });

  function submitRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const payload = buildPasswordRecoveryPayload({ email });
      setFormError(null);
      setRequestSent(false);
      requestRecovery.mutate({
        email: payload.email,
        redirectTo: `${window.location.origin}/password-recovery`,
      });
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Password recovery form is invalid.");
    }
  }

  function submitNewPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const payload = buildPasswordUpdatePayload({ password, confirmPassword });
      setFormError(null);
      completeRecovery.mutate({ accessToken: recoveryToken ?? "", password: payload.password });
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Password reset form is invalid.");
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-panel">
        <div>
          <p className="eyebrow">Aevryn</p>
          <h1>{recoveryToken ? "Set new password" : "Recover password"}</h1>
        </div>
        {recoveryToken ? (
          <form onSubmit={submitNewPassword} className="form-stack" noValidate>
            <label>
              New password
              <input
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <label>
              Confirm password
              <input
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
              />
            </label>
            {formError ? <ErrorMessage>{formError}</ErrorMessage> : null}
            {completeRecovery.error ? (
              <ErrorMessage>{completeRecovery.error.message}</ErrorMessage>
            ) : null}
            <button
              type="submit"
              className="primary-button"
              disabled={completeRecovery.isPending}
            >
              {completeRecovery.isPending ? "Updating password" : "Update password"}
            </button>
          </form>
        ) : (
          <form onSubmit={submitRequest} className="form-stack" noValidate>
            <label>
              Email
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            {formError ? <ErrorMessage>{formError}</ErrorMessage> : null}
            {requestRecovery.error ? <ErrorMessage>{requestRecovery.error.message}</ErrorMessage> : null}
            {requestSent ? (
              <p className="success-note" role="status">
                {RECOVERY_SENT_MESSAGE}
              </p>
            ) : null}
            <button
              type="submit"
              className="primary-button"
              disabled={requestRecovery.isPending}
            >
              {requestRecovery.isPending ? "Sending reset link" : "Send reset link"}
            </button>
          </form>
        )}
        <p className="auth-switch">
          Remembered it? <Link to="/login">Log in</Link>
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

function recoveryTokenFromLocation(location: ReturnType<typeof useLocation>): string | null {
  const hashToken = tokenFromSearchParams(location.hash.replace(/^#/, ""));
  if (hashToken) {
    return hashToken;
  }
  return tokenFromSearchParams(location.search.replace(/^\?/, ""));
}

function tokenFromSearchParams(paramsText: string): string | null {
  const params = new URLSearchParams(paramsText);
  const type = params.get("type");
  const token = params.get("access_token");
  if (type === "recovery" && token) {
    return token;
  }
  return null;
}

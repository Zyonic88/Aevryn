import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiClient, type ProjectSettingsRequest } from "../api/client";
import type { ProjectSettings } from "../api/schemas";
import { useAuth } from "../auth/useAuth";
import { ErrorMessage, LoadingMessage } from "../components/Feedback";
import type { ProjectSummary } from "../projects/projectStore";

export function SettingsWorkspaceView({ project }: { project: ProjectSummary }) {
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const [defaultExportFormat, setDefaultExportFormat] = useState("markdown");
  const [locale, setLocale] = useState("en-US");
  const [formError, setFormError] = useState<string | null>(null);
  const [savedSettings, setSavedSettings] = useState<ProjectSettings | null>(null);

  const settingsQuery = useQuery({
    queryKey: projectSettingsQueryKey(project.id, session?.session_token),
    queryFn: () =>
      apiClient.getProjectSettings(
        project.id,
        requireSessionToken(session),
        new Date().toISOString(),
      ),
    enabled: session !== null,
  });
  const updateSettings = useMutation({
    mutationFn: (payload: ProjectSettingsRequest) =>
      apiClient.updateProjectSettings(
        project.id,
        payload,
        requireSessionToken(session),
        new Date().toISOString(),
      ),
    onSuccess(result) {
      setSavedSettings(result);
      setFormError(null);
      queryClient.setQueryData(projectSettingsQueryKey(project.id, session?.session_token), result);
    },
    onError() {
      setSavedSettings(null);
    },
  });

  useEffect(() => {
    if (!settingsQuery.data) {
      return;
    }
    setDefaultExportFormat(settingsQuery.data.default_export_format);
    setLocale(settingsQuery.data.locale);
  }, [settingsQuery.data]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = {
      default_export_format: defaultExportFormat.trim(),
      locale: locale.trim(),
    };
    if (!payload.default_export_format || !payload.locale) {
      setSavedSettings(null);
      setFormError("Project settings fields cannot be blank.");
      return;
    }
    setFormError(null);
    setSavedSettings(null);
    updateSettings.mutate(payload);
  }

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">Settings</p>
        <h2>Settings</h2>
        <p className="field-note">
          Project behavior, workspace preferences, account context, privacy controls, and diagnostics
          live here without changing Canon truth.
        </p>
      </div>

      <section className="project-panel">
        <h2>Settings Areas</h2>
        <div className="settings-scope-grid" aria-label="Settings areas">
          <a href="#project-settings">
            <strong>Project</strong>
            <span>Defaults that belong to this story workspace.</span>
          </a>
          <a href="#workspace-preferences">
            <strong>Workspace</strong>
            <span>How Aevryn opens, organizes, and reveals tools.</span>
          </a>
          <a href="#account-settings">
            <strong>Account</strong>
            <span>Managed login and profile context.</span>
          </a>
          <a href="#privacy-data-settings">
            <strong>Privacy & Data</strong>
            <span>Ownership, deletion, and AI-training boundaries.</span>
          </a>
          <a href="#diagnostics-settings">
            <strong>Diagnostics</strong>
            <span>Support metadata only, never source prose or secrets.</span>
          </a>
        </div>
      </section>

      <section className="project-panel" id="project-settings">
        <h2>Project Settings</h2>
        <p className="field-note">
          Project settings affect output preferences. They do not override extracted Canon, evidence
          controls, or engine truth rules.
        </p>
        {settingsQuery.isLoading ? <LoadingMessage>Loading settings.</LoadingMessage> : null}
        {settingsQuery.error ? <ErrorMessage>{settingsQuery.error.message}</ErrorMessage> : null}
        <form className="import-form" onSubmit={submit}>
          <label>
            Default export format
            <select
              value={defaultExportFormat}
              onChange={(event) => setDefaultExportFormat(event.target.value)}
            >
              <option value="markdown">Markdown</option>
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
            </select>
          </label>
          <label>
            Locale
            <input value={locale} onChange={(event) => setLocale(event.target.value)} />
          </label>
          {formError ? <ErrorMessage>{formError}</ErrorMessage> : null}
          {updateSettings.error ? <ErrorMessage>{updateSettings.error.message}</ErrorMessage> : null}
          {savedSettings ? <p role="status">Settings saved.</p> : null}
          <button
            type="submit"
            className="primary-button"
            disabled={settingsQuery.isLoading || updateSettings.isPending}
          >
            {updateSettings.isPending ? "Saving settings" : "Save settings"}
          </button>
        </form>
      </section>

      <section className="project-panel" id="workspace-preferences">
        <h2>Workspace Preferences</h2>
        <dl className="settings-summary-list">
          <div>
            <dt>Login destination</dt>
            <dd>Dashboard</dd>
          </div>
          <div>
            <dt>Monitoring</dt>
            <dd>Hidden unless explicitly opened</dd>
          </div>
          <div>
            <dt>Prompt and output bodies</dt>
            <dd>Collapsed by default where the content is long</dd>
          </div>
          <div>
            <dt>Developer previews</dt>
            <dd>Collapsed behind review controls</dd>
          </div>
        </dl>
      </section>

      <section className="project-panel" id="account-settings">
        <h2>Account</h2>
        <dl className="settings-summary-list">
          <div>
            <dt>Signed in as</dt>
            <dd>{session?.display_name ?? "Unknown user"}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{session?.email ?? "Unknown email"}</dd>
          </div>
          <div>
            <dt>Identity provider</dt>
            <dd>Managed identity provider</dd>
          </div>
          <div>
            <dt>Profile editing</dt>
            <dd>Planned for the finished website account surface</dd>
          </div>
        </dl>
      </section>

      <section className="project-panel" id="privacy-data-settings">
        <h2>Privacy & Data</h2>
        <dl className="settings-summary-list">
          <div>
            <dt>Story ownership</dt>
            <dd>Your stories, Canon, exports, and generated assets belong to you.</dd>
          </div>
          <div>
            <dt>AI training</dt>
            <dd>Off by default. Opt-in only. No live training pipeline is active.</dd>
          </div>
          <div>
            <dt>Opt-in meaning</dt>
            <dd>Future consent allows scoped product improvement review; it does not give Aevryn ownership.</dd>
          </div>
          <div>
            <dt>Project deletion</dt>
            <dd>
              Available from the <Link to="/dashboard">Dashboard project list</Link>.
            </dd>
          </div>
          <div>
            <dt>Account deletion</dt>
            <dd>Handled by support until self-service deletion is implemented.</dd>
          </div>
        </dl>
      </section>

      <details className="diagnostics-panel settings-diagnostics" id="diagnostics-settings">
        <summary>Diagnostics</summary>
        <dl className="settings-summary-list">
          <div>
            <dt>Project</dt>
            <dd>{project.name}</dd>
          </div>
          <div>
            <dt>Project ID</dt>
            <dd>{project.id}</dd>
          </div>
          <div>
            <dt>Settings API</dt>
            <dd>{settingsQuery.data ? "API-backed" : "Waiting for settings"}</dd>
          </div>
          <div>
            <dt>Workflow monitoring</dt>
            <dd>
              <Link to={`/projects/${project.id}/monitoring`}>Open monitoring</Link>
            </dd>
          </div>
        </dl>
      </details>
    </div>
  );
}

function projectSettingsQueryKey(projectId: string, sessionToken: string | undefined) {
  return ["project-settings", projectId, sessionToken] as const;
}

function requireSessionToken(session: { session_token: string } | null): string {
  if (!session) {
    throw new Error("Aevryn session is required.");
  }
  return session.session_token;
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";

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
      </div>

      <section className="project-panel">
        <h2>Project Settings</h2>
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

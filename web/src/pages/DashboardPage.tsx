import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { countAuthRoutes } from "../api/capabilitySelectors";
import { apiClient } from "../api/client";
import { useAuth } from "../auth/useAuth";
import { EmptyState, ErrorMessage, LoadingMessage, StatusPanel } from "../components/Feedback";
import { formatDateTime } from "../formatting/display";
import { projectSummaryFromApiProject } from "../projects/projectMapping";
import {
  createProjectShell,
  defaultProjectName,
  normalizeProjectName,
} from "../projects/projectStore";

export function DashboardPage() {
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [projectName, setProjectName] = useState(defaultProjectName());
  const [projectError, setProjectError] = useState<string | null>(null);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);
  const health = useQuery({ queryKey: ["api-health"], queryFn: () => apiClient.health() });
  const capabilities = useQuery({
    queryKey: ["api-capabilities"],
    queryFn: () => apiClient.capabilities(),
  });
  const projectsQuery = useQuery({
    queryKey: ["projects", session?.session_token],
    queryFn: () => apiClient.listProjects(requireSessionToken(session), new Date().toISOString()),
    enabled: session !== null,
  });
  const createProjectMutation = useMutation({
    mutationFn: (name: string) => {
      const now = new Date();
      const shell = createProjectShell(name, { now });
      return apiClient.createProject(
        { project_id: shell.id, name: shell.name, now: shell.updatedAt },
        requireSessionToken(session),
        shell.updatedAt,
      );
    },
    onSuccess(project) {
      setProjectName(defaultProjectName());
      setProjectError(null);
      const existingProjects = projectsQuery.data?.projects ?? [];
      queryClient.setQueryData(["projects", session?.session_token], {
        projects: [
          project,
          ...existingProjects.filter((candidate) => candidate.project_id !== project.project_id),
        ],
      });
      queryClient.setQueryData(["project", project.project_id, session?.session_token], project);
      void navigate(`/projects/${project.project_id}`);
    },
    onError(error) {
      setProjectError(
        error instanceof Error ? error.message : "Project could not be created.",
      );
    },
  });
  const deleteProjectMutation = useMutation({
    mutationFn: (projectId: string) =>
      apiClient.deleteProject(
        projectId,
        requireSessionToken(session),
        new Date().toISOString(),
      ),
    onSuccess(_result, projectId) {
      queryClient.setQueryData(["projects", session?.session_token], {
        projects: (projectsQuery.data?.projects ?? []).filter(
          (project) => project.project_id !== projectId,
        ),
      });
      queryClient.removeQueries({ queryKey: ["project", projectId] });
    },
  });

  const authRouteCount = useMemo(
    () => (capabilities.data ? countAuthRoutes(capabilities.data) : 0),
    [capabilities.data],
  );

  const normalizedProjectName = normalizeProjectName(projectName);
  const projects = useMemo(
    () =>
      (projectsQuery.data?.projects ?? [])
        .map(projectSummaryFromApiProject)
        .sort(compareProjectActivity),
    [projectsQuery.data?.projects],
  );

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createProjectMutation.mutate(projectName);
  }

  function requestProjectDeletion(projectId: string, projectTitle: string) {
    if (!window.confirm(`Delete project ${projectTitle}?`)) {
      return;
    }
    if (!window.confirm("Project data will be lost forever, are you sure?")) {
      return;
    }
    deleteProjectMutation.mutate(projectId);
  }

  return (
    <div className="dashboard-grid">
      <section className="page-heading">
        <p className="eyebrow">Workspace</p>
        <h1>Dashboard</h1>
      </section>

      <section className="project-panel">
        <div className="section-title-row">
          <h2>Projects</h2>
          <span>{projectCountLabel(projects.length)}</span>
        </div>
        <p className="field-note">
          Open a project to continue working, or create a new story workspace.
        </p>
        <form className="inline-form" onSubmit={submit}>
          <label>
            Project name
            <input
              value={projectName}
              maxLength={120}
              onChange={(event) => setProjectName(event.target.value)}
            />
          </label>
          <button
            type="submit"
            className="primary-button"
            disabled={!normalizedProjectName || createProjectMutation.isPending}
          >
            {createProjectMutation.isPending ? "Creating..." : "Create project"}
          </button>
        </form>
        {projectError ? <ErrorMessage>{projectError}</ErrorMessage> : null}
        {projectsQuery.isLoading ? <LoadingMessage>Loading projects.</LoadingMessage> : null}
        {projectsQuery.error ? <ErrorMessage>{projectsQuery.error.message}</ErrorMessage> : null}
        {deleteProjectMutation.error ? (
          <ErrorMessage>{deleteProjectMutation.error.message}</ErrorMessage>
        ) : null}
        {!projectsQuery.isLoading && !projectsQuery.error && projects.length === 0 ? (
          <EmptyState title="No projects yet">
            Create a project to import chapters and build Canon-backed workspace output.
          </EmptyState>
        ) : null}
        {projects.length > 0 ? (
          <div className="project-list">
            {projects.map((project) => (
              <div key={project.id} className="project-row project-row-action">
                <Link to={`/projects/${project.id}`} className="project-select-link">
                  <strong>{project.name}</strong>
                  <span>Updated {formatDateTime(project.updatedAt)}</span>
                  <small>Open workspace</small>
                </Link>
                <button
                  type="button"
                  className="icon-button danger-button"
                  aria-label={`Delete project ${project.name}`}
                  title={`Delete project ${project.name}`}
                  disabled={deleteProjectMutation.isPending}
                  onClick={() => requestProjectDeletion(project.id, project.name)}
                >
                  <span aria-hidden="true">×</span>
                </button>
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <details
        className="diagnostics-panel"
        onToggle={(event) => setDiagnosticsOpen(event.currentTarget.open)}
      >
        <summary>Diagnostics</summary>
        {diagnosticsOpen ? (
          <div className="diagnostics-grid">
            <StatusPanel title="API Health">
              {health.isLoading ? <LoadingMessage>Checking API health.</LoadingMessage> : null}
              {health.error ? <ErrorMessage>{health.error.message}</ErrorMessage> : null}
              {health.data ? (
                <dl className="metric-grid">
                  <div>
                    <dt>Status</dt>
                    <dd>{health.data.status}</dd>
                  </div>
                  <div>
                    <dt>Engine</dt>
                    <dd>{health.data.engine}</dd>
                  </div>
                  <div>
                    <dt>API</dt>
                    <dd>{health.data.api_version}</dd>
                  </div>
                  <div>
                    <dt>Storage</dt>
                    <dd>{health.data.storage.project_storage}</dd>
                  </div>
                </dl>
              ) : null}
            </StatusPanel>

            <StatusPanel title="API Capabilities">
              {capabilities.isLoading ? (
                <LoadingMessage>Loading capabilities.</LoadingMessage>
              ) : null}
              {capabilities.error ? <ErrorMessage>{capabilities.error.message}</ErrorMessage> : null}
              {capabilities.data ? (
                <dl className="metric-grid">
                  <div>
                    <dt>Routes</dt>
                    <dd>{capabilities.data.routes.length}</dd>
                  </div>
                  <div>
                    <dt>Auth routes</dt>
                    <dd>{authRouteCount}</dd>
                  </div>
                  <div>
                    <dt>Formats</dt>
                    <dd>{capabilities.data.source_formats.supported.length}</dd>
                  </div>
                </dl>
              ) : null}
            </StatusPanel>
          </div>
        ) : null}
      </details>
    </div>
  );
}

function projectCountLabel(count: number): string {
  if (count === 0) {
    return "No projects";
  }
  if (count === 1) {
    return "1 project";
  }
  return `${count.toLocaleString()} projects`;
}

function compareProjectActivity(
  firstProject: { name: string; updatedAt: string },
  secondProject: { name: string; updatedAt: string },
): number {
  const firstUpdated = Date.parse(firstProject.updatedAt);
  const secondUpdated = Date.parse(secondProject.updatedAt);
  if (Number.isFinite(firstUpdated) && Number.isFinite(secondUpdated)) {
    return secondUpdated - firstUpdated;
  }
  if (Number.isFinite(secondUpdated)) {
    return 1;
  }
  if (Number.isFinite(firstUpdated)) {
    return -1;
  }
  return firstProject.name.localeCompare(secondProject.name);
}

function requireSessionToken(session: { session_token: string } | null): string {
  if (!session) {
    throw new Error("Aevryn session is required.");
  }
  return session.session_token;
}

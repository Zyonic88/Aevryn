import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { countAuthRoutes } from "../api/capabilitySelectors";
import { apiClient } from "../api/client";
import { useAuth } from "../auth/useAuth";
import { EmptyState, ErrorMessage, LoadingMessage, StatusPanel } from "../components/Feedback";
import { projectSummaryFromApiProject } from "../projects/projectMapping";
import {
  createProjectShell,
  defaultProjectName,
  normalizeProjectName,
} from "../projects/projectStore";

export function DashboardPage() {
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const [projectName, setProjectName] = useState(defaultProjectName());
  const [projectError, setProjectError] = useState<string | null>(null);
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
    },
    onError(error) {
      setProjectError(
        error instanceof Error ? error.message : "Project shell could not be created.",
      );
    },
  });

  const authRouteCount = useMemo(
    () => (capabilities.data ? countAuthRoutes(capabilities.data) : 0),
    [capabilities.data],
  );

  const normalizedProjectName = normalizeProjectName(projectName);
  const projects = (projectsQuery.data?.projects ?? []).map(projectSummaryFromApiProject);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createProjectMutation.mutate(projectName);
  }

  return (
    <div className="dashboard-grid">
      <section className="page-heading">
        <p className="eyebrow">App Shell</p>
        <h1>Dashboard</h1>
      </section>

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
        {capabilities.isLoading ? <LoadingMessage>Loading capabilities.</LoadingMessage> : null}
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

      <section className="project-panel">
        <div className="section-title-row">
          <h2>Projects</h2>
        </div>
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
            {createProjectMutation.isPending ? "Creating..." : "Create shell"}
          </button>
        </form>
        {projectError ? <ErrorMessage>{projectError}</ErrorMessage> : null}
        {projectsQuery.isLoading ? <LoadingMessage>Loading projects.</LoadingMessage> : null}
        {projectsQuery.error ? <ErrorMessage>{projectsQuery.error.message}</ErrorMessage> : null}
        {!projectsQuery.isLoading && !projectsQuery.error && projects.length === 0 ? (
          <EmptyState title="No projects yet">
            Create a placeholder shell to test routing.
          </EmptyState>
        ) : null}
        {projects.length > 0 ? (
          <div className="project-list">
            {projects.map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`} className="project-row">
                <strong>{project.name}</strong>
                <span>{project.updatedAt}</span>
              </Link>
            ))}
          </div>
        ) : null}
      </section>
    </div>
  );
}

function requireSessionToken(session: { session_token: string } | null): string {
  if (!session) {
    throw new Error("Aevryn session is required.");
  }
  return session.session_token;
}

import { useQuery } from "@tanstack/react-query";
import { FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { countAuthRoutes } from "../api/capabilitySelectors";
import { apiClient } from "../api/client";
import { EmptyState, ErrorMessage, LoadingMessage, StatusPanel } from "../components/Feedback";
import {
  createProject,
  defaultProjectName,
  normalizeProjectName,
  readProjects,
  writeProjects,
  type ProjectSummary,
} from "../projects/projectStore";

export function DashboardPage() {
  const [projectName, setProjectName] = useState(defaultProjectName());
  const [projects, setProjects] = useState<ProjectSummary[]>(() => readProjects());
  const [projectError, setProjectError] = useState<string | null>(null);
  const health = useQuery({ queryKey: ["api-health"], queryFn: () => apiClient.health() });
  const capabilities = useQuery({
    queryKey: ["api-capabilities"],
    queryFn: () => apiClient.capabilities(),
  });

  const authRouteCount = useMemo(
    () => (capabilities.data ? countAuthRoutes(capabilities.data) : 0),
    [capabilities.data],
  );

  const normalizedProjectName = normalizeProjectName(projectName);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const nextProjects = createProject(projectName, projects);
      const persisted = writeProjects(nextProjects);
      setProjects(nextProjects);
      setProjectName(defaultProjectName());
      setProjectError(
        persisted
          ? null
          : "Project shell is available for this session, but browser storage failed.",
      );
    } catch (error) {
      setProjectError(
        error instanceof Error ? error.message : "Project shell could not be created.",
      );
    }
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
          <button type="submit" className="primary-button" disabled={!normalizedProjectName}>
            Create shell
          </button>
        </form>
        {projectError ? <ErrorMessage>{projectError}</ErrorMessage> : null}
        {projects.length === 0 ? (
          <EmptyState title="No projects yet">
            Create a placeholder shell to test routing.
          </EmptyState>
        ) : (
          <div className="project-list">
            {projects.map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`} className="project-row">
                <strong>{project.name}</strong>
                <span>{project.updatedAt}</span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

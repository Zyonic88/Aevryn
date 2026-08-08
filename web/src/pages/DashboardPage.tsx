import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { countAuthRoutes } from "../api/capabilitySelectors";
import { apiClient } from "../api/client";
import type { ProjectList } from "../api/schemas";
import { useAuth } from "../auth/useAuth";
import { EmptyState, ErrorMessage, LoadingMessage, StatusPanel } from "../components/Feedback";
import { formatDateTime } from "../formatting/display";
import { projectSummaryFromApiProject } from "../projects/projectMapping";
import {
  createProjectShell,
  defaultProjectName,
  normalizeProjectName,
  type ProjectSummary,
} from "../projects/projectStore";

export function DashboardPage() {
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [projectName, setProjectName] = useState(defaultProjectName());
  const [projectError, setProjectError] = useState<string | null>(null);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);
  const [deletedProjectIds, setDeletedProjectIds] = useState<ReadonlySet<string>>(() => new Set());
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
    mutationFn: (shell: ProjectSummary) => {
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
      setProjectError(error instanceof Error ? error.message : "Project could not be created.");
    },
  });
  const deleteProjectMutation = useMutation({
    mutationFn: (projectId: string) =>
      apiClient.deleteProject(
        projectId,
        requireSessionToken(session),
        new Date().toISOString(),
      ),
    async onMutate(projectId) {
      const projectListQueryKey = ["projects", session?.session_token] as const;
      await queryClient.cancelQueries({ queryKey: projectListQueryKey });
      const previousProjects = queryClient.getQueryData<ProjectList>(projectListQueryKey);
      setDeletedProjectIds((currentIds) => new Set(currentIds).add(projectId));
      queryClient.setQueryData<ProjectList>(projectListQueryKey, (currentProjects) => {
        const projects = currentProjects?.projects ?? [];
        return {
          projects: projects.filter((project) => project.project_id !== projectId),
        };
      });
      return { previousProjects, projectListQueryKey };
    },
    onError(_error, projectId, context) {
      setDeletedProjectIds((currentIds) => {
        const nextIds = new Set(currentIds);
        nextIds.delete(projectId);
        return nextIds;
      });
      if (context?.previousProjects) {
        queryClient.setQueryData(context.projectListQueryKey, context.previousProjects);
      }
    },
    onSuccess(_result, projectId) {
      queryClient.removeQueries({ queryKey: ["project", projectId] });
      queryClient.removeQueries({ queryKey: ["project-status", projectId] });
      queryClient.removeQueries({ queryKey: ["project-outputs", projectId] });
    },
    onSettled(_result, _error, _projectId, context) {
      void queryClient.invalidateQueries({
        queryKey: context?.projectListQueryKey ?? ["projects", session?.session_token],
      });
    },
  });

  const authRouteCount = useMemo(
    () => (capabilities.data ? countAuthRoutes(capabilities.data) : 0),
    [capabilities.data],
  );

  const normalizedProjectName = normalizeProjectName(projectName);
  const pendingProjectId = createProjectMutation.isPending
    ? createProjectMutation.variables?.id
    : undefined;
  const projects = useMemo(
    () => {
      const confirmedProjects = (projectsQuery.data?.projects ?? [])
        .map(projectSummaryFromApiProject)
        .filter((project) => !deletedProjectIds.has(project.id))
        .sort(compareProjectActivity);
      const pendingProject = createProjectMutation.variables;
      if (
        !createProjectMutation.isPending ||
        !pendingProject ||
        confirmedProjects.some((project) => project.id === pendingProject.id)
      ) {
        return confirmedProjects;
      }
      return [pendingProject, ...confirmedProjects];
    },
    [
      createProjectMutation.isPending,
      createProjectMutation.variables,
      deletedProjectIds,
      projectsQuery.data?.projects,
    ],
  );

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createProjectMutation.mutate(createProjectShell(projectName, { now: new Date() }));
  }

  function requestProjectDeletion(projectId: string, projectTitle: string) {
    if (!window.confirm(`Delete project ${projectTitle}?`)) {
      return;
    }
    if (!window.confirm("Story data will be lost forever, are you sure?")) {
      return;
    }
    deleteProjectMutation.mutate(projectId);
  }

  return (
    <div className="dashboard-grid">
      <section className="page-heading dashboard-heading">
        <div>
          <p className="eyebrow">Workspace</p>
          <h1>Project Dashboard</h1>
        </div>
        <div className="dashboard-signal-row" aria-label="Workspace status">
          <span>Canon</span>
          <span>Continuity</span>
          <span>Prompt Packs</span>
        </div>
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
            aria-busy={createProjectMutation.isPending}
            disabled={!normalizedProjectName || createProjectMutation.isPending}
          >
            {createProjectMutation.isPending ? "Creating..." : "Create project"}
          </button>
        </form>
        {createProjectMutation.isPending && createProjectMutation.variables ? (
          <LoadingMessage>
            Creating workspace for {createProjectMutation.variables.name}.
          </LoadingMessage>
        ) : null}
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
              <div
                key={project.id}
                className={`project-row project-row-action${
                  project.id === pendingProjectId ? " project-row-pending" : ""
                }`}
              >
                {project.id === pendingProjectId ? (
                  <div className="project-select-link" aria-label={`${project.name} creating`}>
                    <strong>{project.name}</strong>
                    <span>Started {formatDateTime(project.updatedAt)}</span>
                    <small>Creating workspace</small>
                  </div>
                ) : (
                  <>
                    <Link
                      to={`/projects/${project.id}`}
                      className="project-select-link"
                      aria-label={`${project.name} Updated ${formatDateTime(project.updatedAt)} Open workspace`}
                    >
                      <span className="project-row-title">
                        <strong>{project.name}</strong>
                        <small>Open workspace</small>
                      </span>
                      <span>Updated {formatDateTime(project.updatedAt)}</span>
                    </Link>
                    <button
                      type="button"
                      className="icon-button danger-button"
                      aria-label={`Delete project ${project.name}`}
                      title={`Delete project ${project.name}`}
                      disabled={deleteProjectMutation.isPending}
                      onClick={() => requestProjectDeletion(project.id, project.name)}
                    />
                  </>
                )}
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

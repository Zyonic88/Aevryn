import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../api/client";
import type { ProjectStatus } from "../api/schemas";
import { useAuth } from "../auth/useAuth";
import { EmptyState, ErrorMessage, LoadingMessage } from "../components/Feedback";
import type { ProjectSummary } from "../projects/projectStore";

export function MonitoringWorkspaceView({ project }: { project: ProjectSummary }) {
  const { session } = useAuth();
  const healthQuery = useQuery({
    queryKey: ["api-health"],
    queryFn: () => apiClient.health(),
  });
  const statusQuery = useQuery({
    queryKey: projectStatusQueryKey(project.id, session?.session_token),
    queryFn: () =>
      apiClient.projectStatus(
        project.id,
        requireSessionToken(session),
        new Date().toISOString(),
      ),
    enabled: session !== null,
  });
  const status = statusQuery.data;

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">Monitoring</p>
        <h2>Monitoring</h2>
      </div>

      <section className="project-panel" aria-label="API health">
        <h2>API Health</h2>
        {healthQuery.isLoading ? <LoadingMessage>Checking API health.</LoadingMessage> : null}
        {healthQuery.error ? <ErrorMessage>{healthQuery.error.message}</ErrorMessage> : null}
        {healthQuery.data ? (
          <dl className="metric-grid">
            <div>
              <dt>Status</dt>
              <dd>{healthQuery.data.status}</dd>
            </div>
            <div>
              <dt>Engine</dt>
              <dd>{healthQuery.data.engine}</dd>
            </div>
            <div>
              <dt>API</dt>
              <dd>{healthQuery.data.api_version}</dd>
            </div>
          </dl>
        ) : null}
      </section>

      <section className="project-panel" aria-label="Current project run state">
        <h2>Current Project Run State</h2>
        {statusQuery.isLoading ? <LoadingMessage>Loading project status.</LoadingMessage> : null}
        {statusQuery.error ? <ErrorMessage>{statusQuery.error.message}</ErrorMessage> : null}
        {status ? <ProjectStatusSummary status={status} /> : null}
      </section>

      {status ? (
        <>
          <section className="project-panel" aria-label="Latest failure">
            <h2>Latest Failure</h2>
            {status.latest_failure_summary ? (
              <p className="monitoring-note">{status.latest_failure_summary}</p>
            ) : (
              <EmptyState title="No recent failure">
                The status API is not reporting a current failure for this project.
              </EmptyState>
            )}
          </section>

          <section className="project-panel" aria-label="Snapshot availability">
            <h2>Snapshot Availability</h2>
            <dl className="metric-grid">
              <div>
                <dt>Available</dt>
                <dd>{status.snapshots.available ? "yes" : "no"}</dd>
              </div>
              <div>
                <dt>Count</dt>
                <dd>{status.snapshots.count}</dd>
              </div>
              <div>
                <dt>Latest</dt>
                <dd>{status.snapshots.latest_snapshot_kind ?? "none"}</dd>
              </div>
            </dl>
            {status.snapshots.latest_snapshot_id ? (
              <p className="field-note">{status.snapshots.latest_snapshot_id}</p>
            ) : null}
          </section>

          <section className="project-panel" aria-label="Export availability">
            <h2>Export Availability</h2>
            <dl className="metric-grid">
              <div>
                <dt>Available</dt>
                <dd>{status.exports.available ? "yes" : "no"}</dd>
              </div>
              <div>
                <dt>Count</dt>
                <dd>{status.exports.count}</dd>
              </div>
              <div>
                <dt>Latest</dt>
                <dd>{status.exports.latest_export_format ?? "none"}</dd>
              </div>
            </dl>
            {status.exports.latest_export_id ? (
              <p className="field-note">
                {status.exports.latest_export_id} / {status.exports.latest_export_kind}
              </p>
            ) : null}
          </section>

          <section className="project-panel" aria-label="Recent workflow events">
            <h2>Recent Workflow Events</h2>
            {status.recent_workflow_events.length === 0 ? (
              <EmptyState title="No workflow events">
                The status API has no recent workflow events for this project.
              </EmptyState>
            ) : (
              <div className="monitoring-event-list">
                {status.recent_workflow_events.map((event) => (
                  <div
                    key={`${event.event_type}-${event.occurred_at}-${event.summary}`}
                    className="monitoring-event-row"
                  >
                    <strong>{event.event_type}</strong>
                    <span>{event.status}</span>
                    <span>{event.occurred_at}</span>
                    <span>{event.summary}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}

function ProjectStatusSummary({ status }: { status: ProjectStatus }) {
  return (
    <div className="monitoring-stack">
      <dl className="metric-grid">
        <div>
          <dt>Status</dt>
          <dd>{status.status}</dd>
        </div>
        <div>
          <dt>Stories</dt>
          <dd>{status.story_count}</dd>
        </div>
        <div>
          <dt>Runs</dt>
          <dd>{status.run_count}</dd>
        </div>
      </dl>

      <dl className="monitoring-detail-grid">
        <div>
          <dt>Latest import</dt>
          <dd>{status.latest_import?.filename ?? "none"}</dd>
        </div>
        <div>
          <dt>Latest run</dt>
          <dd>{status.latest_engine_run?.run_id ?? "none"}</dd>
        </div>
        <div>
          <dt>Run state</dt>
          <dd>{status.latest_engine_run?.status ?? "none"}</dd>
        </div>
        <div>
          <dt>Worker</dt>
          <dd>{status.worker.state}</dd>
        </div>
        <div>
          <dt>Queued jobs</dt>
          <dd>{status.worker.queued_jobs}</dd>
        </div>
        <div>
          <dt>Running jobs</dt>
          <dd>{status.worker.running_jobs}</dd>
        </div>
      </dl>
    </div>
  );
}

function projectStatusQueryKey(projectId: string, sessionToken: string | undefined) {
  return ["project-status", projectId, sessionToken] as const;
}

function requireSessionToken(session: { session_token: string } | null): string {
  if (!session) {
    throw new Error("Aevryn session is required.");
  }
  return session.session_token;
}

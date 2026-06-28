import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiClient } from "../api/client";
import { useAuth } from "../auth/useAuth";
import { EmptyState, ErrorMessage, LoadingMessage } from "../components/Feedback";
import type { ProjectSummary } from "../projects/projectStore";
import { readActiveStoryId, saveActiveStoryId } from "../stories/activeStory";

export function StoryWorkspaceView({ project }: { project: ProjectSummary }) {
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const [title, setTitle] = useState(defaultStoryTitle(project.name));
  const [selectedStoryId, setSelectedStoryId] = useState(() => readActiveStoryId(project.id));
  const [formError, setFormError] = useState<string | null>(null);

  const storiesQuery = useQuery({
    queryKey: storyQueryKey(project.id, session?.session_token),
    queryFn: () =>
      apiClient.listStories(project.id, requireSessionToken(session), new Date().toISOString()),
    enabled: session !== null,
  });
  const createStory = useMutation({
    mutationFn: (storyTitle: string) => {
      const now = new Date().toISOString();
      return apiClient.createStory(
        project.id,
        { story_id: createStoryId(storyTitle), title: storyTitle.trim(), now },
        requireSessionToken(session),
        now,
      );
    },
    onSuccess(story) {
      setTitle(defaultStoryTitle(project.name));
      setFormError(null);
      const existingStories = storiesQuery.data?.stories ?? [];
      queryClient.setQueryData(storyQueryKey(project.id, session?.session_token), {
        stories: [
          story,
          ...existingStories.filter((candidate) => candidate.story_id !== story.story_id),
        ],
      });
    },
    onError() {
      setFormError(null);
    },
  });
  const deleteStory = useMutation({
    mutationFn: (storyId: string) =>
      apiClient.deleteStory(
        project.id,
        storyId,
        requireSessionToken(session),
        new Date().toISOString(),
      ),
    onSuccess(_result, storyId) {
      const remainingStories = (storiesQuery.data?.stories ?? []).filter(
        (story) => story.story_id !== storyId,
      );
      const nextStoryId = remainingStories[0]?.story_id ?? "";
      setSelectedStoryId(nextStoryId);
      saveActiveStoryId(project.id, nextStoryId);
      queryClient.setQueryData(storyQueryKey(project.id, session?.session_token), {
        stories: remainingStories,
      });
      void queryClient.invalidateQueries({ queryKey: ["story-imports", project.id] });
      void queryClient.invalidateQueries({ queryKey: ["story-snapshots", project.id] });
      void queryClient.invalidateQueries({ queryKey: ["project-runs", project.id] });
      void queryClient.invalidateQueries({ queryKey: ["project-status", project.id] });
      void queryClient.invalidateQueries({ queryKey: ["project-outputs", project.id] });
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedTitle = title.trim().replace(/\s+/g, " ");
    if (!normalizedTitle) {
      setFormError("Story title is required.");
      return;
    }
    setFormError(null);
    createStory.mutate(normalizedTitle);
  }

  const stories = storiesQuery.data?.stories ?? [];
  const activeStoryId = stories.some((story) => story.story_id === selectedStoryId)
    ? selectedStoryId
    : stories[0]?.story_id ?? "";

  function selectStory(storyId: string) {
    setSelectedStoryId(storyId);
    saveActiveStoryId(project.id, storyId);
  }

  function requestStoryDeletion(storyId: string, storyTitle: string) {
    if (!window.confirm(`Delete project ${storyTitle}?`)) {
      return;
    }
    if (!window.confirm("Story data will be lost forever, are you sure?")) {
      return;
    }
    deleteStory.mutate(storyId);
  }

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">Story</p>
        <h2>Story</h2>
      </div>

      <section className="project-panel">
        <h2>Stories</h2>
        <form className="inline-form" onSubmit={submit}>
          <label>
            Story title
            <input value={title} maxLength={120} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <button type="submit" className="primary-button" disabled={createStory.isPending}>
            {createStory.isPending ? "Creating story" : "Create story"}
          </button>
        </form>
        {formError ? <ErrorMessage>{formError}</ErrorMessage> : null}
        {createStory.error ? <ErrorMessage>{createStory.error.message}</ErrorMessage> : null}
        {deleteStory.error ? <ErrorMessage>{deleteStory.error.message}</ErrorMessage> : null}
        {storiesQuery.isLoading ? <LoadingMessage>Loading stories.</LoadingMessage> : null}
        {storiesQuery.error ? <ErrorMessage>{storiesQuery.error.message}</ErrorMessage> : null}
        {!storiesQuery.isLoading && !storiesQuery.error && stories.length === 0 ? (
          <EmptyState title="No stories yet">
            Create story metadata before importing chapters.
          </EmptyState>
        ) : null}
        {stories.length > 0 ? (
          <div className="project-list">
            {stories.map((story) => (
              <div key={story.story_id} className="project-row project-row-action">
                <button
                  type="button"
                  className="text-button story-select-button"
                  aria-pressed={activeStoryId === story.story_id}
                  onClick={() => selectStory(story.story_id)}
                >
                  <strong>{story.title}</strong>
                  <span>{activeStoryId === story.story_id ? "Selected story" : "Select story"}</span>
                </button>
                <span>{story.updated_at}</span>
                <button
                  type="button"
                  className="icon-button danger-button"
                  aria-label={`Delete ${story.title}`}
                  disabled={deleteStory.isPending}
                  onClick={() => requestStoryDeletion(story.story_id, story.title)}
                >
                  x
                </button>
              </div>
            ))}
          </div>
        ) : null}
      </section>
    </div>
  );
}

function storyQueryKey(projectId: string, sessionToken: string | undefined) {
  return ["project-stories", projectId, sessionToken] as const;
}

function defaultStoryTitle(projectName: string): string {
  return `${projectName} Story`;
}

function createStoryId(title: string): string {
  const slug = title
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 80);
  return `story_${slug || "untitled"}`;
}

function requireSessionToken(session: { session_token: string } | null): string {
  if (!session) {
    throw new Error("Aevryn session is required.");
  }
  return session.session_token;
}

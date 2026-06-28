const ACTIVE_STORY_STORAGE_PREFIX = "aevryn.activeStory.";

export function readActiveStoryId(projectId: string, storage: Storage = window.localStorage): string {
  try {
    return storage.getItem(activeStoryKey(projectId)) ?? "";
  } catch {
    return "";
  }
}

export function saveActiveStoryId(
  projectId: string,
  storyId: string,
  storage: Storage = window.localStorage,
): void {
  try {
    const key = activeStoryKey(projectId);
    if (storyId) {
      storage.setItem(key, storyId);
    } else {
      storage.removeItem(key);
    }
  } catch {
    // Selection persistence is helpful, not required for workspace correctness.
  }
}

export function activeStoryKey(projectId: string): string {
  return `${ACTIVE_STORY_STORAGE_PREFIX}${projectId}`;
}

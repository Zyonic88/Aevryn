export function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
  }
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date);
}

export function formatRunStatus(value: string): string {
  const normalized = value.trim().toLowerCase();
  if (!normalized) {
    return "Unknown";
  }
  return `${normalized.charAt(0).toUpperCase()}${normalized.slice(1)}`;
}

export function formatSceneScope(sceneId: string): string {
  const sceneMatch = sceneId.match(/(?:^|_)chapter_(\d+)_scene_(\d+)$/iu);
  if (sceneMatch) {
    return `Chapter ${Number(sceneMatch[1])}, Scene ${Number(sceneMatch[2])}`;
  }

  const simpleSceneMatch = sceneId.match(/^scene_(\d+)$/iu);
  if (simpleSceneMatch) {
    return `Scene ${Number(simpleSceneMatch[1])}`;
  }

  return "Scene";
}

export function formatChapterScope(chapterId: string): string {
  const chapterMatch = chapterId.match(/(?:^|_)chapter_(\d+)$/iu);
  if (chapterMatch) {
    return `Chapter ${Number(chapterMatch[1])}`;
  }

  return "Chapter";
}

export function formatEvidenceScope({
  chapter_id,
  scene_id,
}: {
  chapter_id: string;
  scene_id: string;
}): string {
  const sceneScope = formatSceneScope(scene_id);
  if (sceneScope !== "Scene") {
    return sceneScope;
  }
  return formatChapterScope(chapter_id);
}

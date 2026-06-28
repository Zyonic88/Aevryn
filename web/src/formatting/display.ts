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

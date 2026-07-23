import type { OutputSection } from "../api/schemas";

export function promptDownloadFilename(section: OutputSection): string {
  const slug = section.title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `aevryn-${slug || "prompt"}.txt`;
}

export function downloadPromptText(section: OutputSection, promptText: string) {
  const blob = new Blob([promptText], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = promptDownloadFilename(section);
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

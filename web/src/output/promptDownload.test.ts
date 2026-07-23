import { afterEach, describe, expect, it, vi } from "vitest";

import type { OutputSection } from "../api/schemas";
import { downloadPromptText, promptDownloadFilename } from "./promptDownload";

function section(title: string): OutputSection {
  return { title, items: ["Prompt line"] };
}

describe("prompt downloads", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("builds stable text filenames from prompt titles", () => {
    expect(promptDownloadFilename(section("Image Prompt"))).toBe(
      "aevryn-image-prompt.txt",
    );
    expect(promptDownloadFilename(section("Camera / Animation Prompt"))).toBe(
      "aevryn-camera-animation-prompt.txt",
    );
  });

  it("downloads prompt text without exposing source data to a backend", () => {
    const click = vi.fn();
    const remove = vi.fn();
    const anchor = document.createElement("a");
    anchor.click = click;
    anchor.remove = remove;
    vi.spyOn(document, "createElement").mockReturnValue(anchor);
    const append = vi.spyOn(document.body, "append");
    const createObjectURL = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:aevryn-prompt");
    const revokeObjectURL = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});

    downloadPromptText(section("Image Prompt"), "Canon-backed prompt body.");

    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
    expect(anchor.href).toBe("blob:aevryn-prompt");
    expect(anchor.download).toBe("aevryn-image-prompt.txt");
    expect(append).toHaveBeenCalledWith(anchor);
    expect(click).toHaveBeenCalledTimes(1);
    expect(remove).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:aevryn-prompt");
  });
});

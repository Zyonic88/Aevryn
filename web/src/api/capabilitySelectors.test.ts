import { describe, expect, it } from "vitest";

import type { ApiCapabilities } from "./schemas";
import { countAuthRoutes } from "./capabilitySelectors";

const capabilities: ApiCapabilities = {
  api_version: "v2",
  engine: "Aevryn",
  phase: "v2_phase_1_backend_api",
  routes: [
    { method: "GET", path: "/v2/health", purpose: "Health" },
    { method: "POST", path: "/v2/auth/login", purpose: "Login" },
    { method: "POST", path: "/v2/auth/register", purpose: "Register" },
  ],
  source_formats: { supported: [], deferred: [] },
  export_capabilities: [],
  platform_limits: [],
};

describe("capability selectors", () => {
  it("keeps route interpretation in the API layer", () => {
    expect(countAuthRoutes(capabilities)).toBe(2);
  });
});

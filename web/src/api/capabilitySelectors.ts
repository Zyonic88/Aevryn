import type { ApiCapabilities } from "./schemas";

const AUTH_ROUTE_PREFIX = "/v2/auth/";

export function countAuthRoutes(capabilities: ApiCapabilities): number {
  return capabilities.routes.filter((route) => route.path.startsWith(AUTH_ROUTE_PREFIX)).length;
}

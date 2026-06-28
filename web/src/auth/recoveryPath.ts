export function recoveryPath(state: unknown): string {
  if (!isLocationState(state)) {
    return "/dashboard";
  }
  const { pathname, search = "", hash = "" } = state.from;
  if (!pathname.startsWith("/")) {
    return "/dashboard";
  }
  return `${pathname}${search}${hash}`;
}

function isLocationState(
  state: unknown,
): state is { from: { pathname: string; search?: string; hash?: string } } {
  if (typeof state !== "object" || state === null || !("from" in state)) {
    return false;
  }
  const from = (state as { from?: unknown }).from;
  if (typeof from !== "object" || from === null) {
    return false;
  }
  const candidate = from as { pathname?: unknown; search?: unknown; hash?: unknown };
  return (
    typeof candidate.pathname === "string" &&
    (candidate.search === undefined || typeof candidate.search === "string") &&
    (candidate.hash === undefined || typeof candidate.hash === "string")
  );
}

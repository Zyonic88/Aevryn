/* eslint-disable react-refresh/only-export-components */
import {
  AnchorHTMLAttributes,
  Children,
  ReactElement,
  ReactNode,
  createContext,
  isValidElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

type LocationState = {
  pathname: string;
  search: string;
  hash: string;
  state: unknown;
};

type NavigateOptions = {
  replace?: boolean;
  state?: unknown;
};

type RouterContextValue = {
  location: LocationState;
  navigate: (to: string, options?: NavigateOptions) => void;
};

type RouteDefinition = {
  path?: string;
  index?: boolean;
  element?: ReactNode;
  children: RouteDefinition[];
};

type RouteMatch = {
  route: RouteDefinition;
  params: Record<string, string>;
  child: RouteMatch | null;
};

type RouteProps = {
  path?: string;
  index?: boolean;
  element?: ReactNode;
  children?: ReactNode;
};

type LinkProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> & {
  to: string;
  replace?: boolean;
  state?: unknown;
};

type NavLinkProps = Omit<LinkProps, "className"> & {
  className?: string | ((props: { isActive: boolean }) => string | undefined);
};

const RouterContext = createContext<RouterContextValue | null>(null);
const OutletContext = createContext<ReactNode>(null);
const ParamsContext = createContext<Record<string, string>>({});

export function BrowserRouter({ children }: { children: ReactNode }) {
  const [location, setLocation] = useState<LocationState>(() =>
    locationFromWindow(window.history.state),
  );

  useEffect(() => {
    function syncLocation(event: PopStateEvent) {
      setLocation(locationFromWindow(event.state));
    }
    window.addEventListener("popstate", syncLocation);
    return () => window.removeEventListener("popstate", syncLocation);
  }, []);

  const navigate = useCallback((to: string, options?: NavigateOptions) => {
    const target = resolveAppPath(to, window.location.pathname);
    const method = options?.replace ? "replaceState" : "pushState";
    window.history[method](options?.state ?? null, "", target);
    setLocation(locationFromWindow(options?.state ?? null));
  }, []);

  const value = useMemo(() => ({ location, navigate }), [location, navigate]);

  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>;
}

export function MemoryRouter({
  children,
  initialEntries = ["/"],
}: {
  children: ReactNode;
  initialEntries?: string[];
}) {
  const [location, setLocation] = useState<LocationState>(() =>
    locationFromPath(initialEntries[0] ?? "/", null),
  );

  const navigate = useCallback((to: string, options?: NavigateOptions) => {
    setLocation(locationFromPath(resolveAppPath(to, location.pathname), options?.state ?? null));
  }, [location.pathname]);

  const value = useMemo(() => ({ location, navigate }), [location, navigate]);

  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>;
}

export function Routes({ children }: { children: ReactNode }) {
  const { location } = useRouterContext();
  const routes = useMemo(() => routeDefinitionsFromChildren(children), [children]);
  const match = matchRoutes(routes, location.pathname);

  return match ? renderRouteMatch(match, {}) : null;
}

export function Route(props: RouteProps) {
  void props;
  return null;
}

export function Navigate({
  to,
  replace = false,
  state,
}: {
  to: string;
  replace?: boolean;
  state?: unknown;
}) {
  const navigate = useNavigate();

  useEffect(() => {
    navigate(to, { replace, state });
  }, [navigate, replace, state, to]);

  return null;
}

export function Outlet() {
  return <>{useContext(OutletContext)}</>;
}

export function Link({
  to,
  replace = false,
  state,
  onClick,
  children,
  ...props
}: LinkProps) {
  const { location, navigate } = useRouterContext();
  const href = resolveAppPath(to, location.pathname);

  return (
    <a
      {...props}
      href={href}
      onClick={(event) => {
        onClick?.(event);
        if (event.defaultPrevented || shouldLetBrowserHandleClick(event)) {
          return;
        }
        event.preventDefault();
        navigate(to, { replace, state });
      }}
    >
      {children}
    </a>
  );
}

export function NavLink({ className, to, ...props }: NavLinkProps) {
  const { location } = useRouterContext();
  const href = resolveAppPath(to, location.pathname);
  const isActive = isActivePath(location.pathname, href);
  const resolvedClassName =
    typeof className === "function"
      ? className({ isActive })
      : [className, isActive ? "active" : ""].filter(Boolean).join(" ");

  return (
    <Link
      {...props}
      aria-current={isActive ? "page" : undefined}
      className={resolvedClassName || undefined}
      to={to}
    />
  );
}

export function useNavigate() {
  return useRouterContext().navigate;
}

export function useLocation() {
  return useRouterContext().location;
}

export function useParams() {
  return useContext(ParamsContext);
}

function useRouterContext(): RouterContextValue {
  const context = useContext(RouterContext);
  if (!context) {
    throw new Error("Aevryn router hooks must be used inside a router.");
  }
  return context;
}

function routeDefinitionsFromChildren(children: ReactNode): RouteDefinition[] {
  return Children.toArray(children).flatMap((child) => {
    if (!isValidElement<RouteProps>(child)) {
      return [];
    }
    if (child.type !== Route) {
      return [];
    }
    return [
      {
        path: child.props.path,
        index: child.props.index,
        element: child.props.element,
        children: routeDefinitionsFromChildren(child.props.children),
      },
    ];
  });
}

function matchRoutes(routes: RouteDefinition[], pathname: string): RouteMatch | null {
  for (const route of routes) {
    const match = matchRoute(route, pathname);
    if (match) {
      return match;
    }
  }
  return null;
}

function matchRoute(route: RouteDefinition, pathname: string): RouteMatch | null {
  if (route.children.length > 0 && route.path === undefined && !route.index) {
    const childMatch = matchRoutes(route.children, pathname);
    return childMatch ? { route, params: {}, child: childMatch } : null;
  }

  const params = routeParams(route, pathname);
  if (params === null) {
    return null;
  }

  if (route.children.length === 0) {
    return { route, params, child: null };
  }

  const childMatch = matchRoutes(route.children, pathname);
  return childMatch ? { route, params, child: childMatch } : null;
}

function routeParams(route: RouteDefinition, pathname: string): Record<string, string> | null {
  if (route.index) {
    return normalizePathname(pathname) === "/" ? {} : null;
  }
  if (route.path === "*") {
    return {};
  }
  if (!route.path) {
    return {};
  }

  const routeSegments = pathSegments(route.path);
  const locationSegments = pathSegments(pathname);
  if (routeSegments.length !== locationSegments.length) {
    return null;
  }

  const params: Record<string, string> = {};
  for (let index = 0; index < routeSegments.length; index += 1) {
    const routeSegment = routeSegments[index];
    const locationSegment = locationSegments[index];
    if (routeSegment.startsWith(":")) {
      params[routeSegment.slice(1)] = decodeURIComponent(locationSegment);
    } else if (routeSegment !== locationSegment) {
      return null;
    }
  }
  return params;
}

function renderRouteMatch(match: RouteMatch, parentParams: Record<string, string>): ReactNode {
  const params = { ...parentParams, ...match.params };
  const child = match.child ? renderRouteMatch(match.child, params) : null;
  const element = match.route.element;

  if (!isValidElement(element)) {
    return child;
  }

  return (
    <ParamsContext.Provider value={params}>
      <OutletContext.Provider value={child}>{element as ReactElement}</OutletContext.Provider>
    </ParamsContext.Provider>
  );
}

function locationFromWindow(state: unknown): LocationState {
  return {
    pathname: window.location.pathname,
    search: window.location.search,
    hash: window.location.hash,
    state,
  };
}

function locationFromPath(path: string, state: unknown): LocationState {
  const url = new URL(path, "https://aevryn.local");
  return {
    pathname: url.pathname,
    search: url.search,
    hash: url.hash,
    state,
  };
}

function resolveAppPath(to: string, currentPathname: string): string {
  if (!to || to.includes("\\") || to.startsWith("//")) {
    return "/dashboard";
  }

  const origin = window.location.origin || "https://aevryn.local";
  const url = new URL(to, origin);
  if (url.origin !== origin) {
    return "/dashboard";
  }

  if (!to.startsWith("/") && !to.startsWith("?") && !to.startsWith("#")) {
    const base = currentPathname.endsWith("/")
      ? currentPathname
      : currentPathname.slice(0, currentPathname.lastIndexOf("/") + 1);
    const relativeUrl = new URL(`${base}${to}`, origin);
    return `${relativeUrl.pathname}${relativeUrl.search}${relativeUrl.hash}`;
  }

  return `${url.pathname}${url.search}${url.hash}`;
}

function shouldLetBrowserHandleClick(event: React.MouseEvent<HTMLAnchorElement>) {
  return (
    event.button !== 0 ||
    event.metaKey ||
    event.altKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.currentTarget.target === "_blank"
  );
}

function isActivePath(pathname: string, href: string): boolean {
  const target = normalizePathname(new URL(href, "https://aevryn.local").pathname);
  const current = normalizePathname(pathname);
  return current === target || (target !== "/" && current.startsWith(`${target}/`));
}

function normalizePathname(pathname: string): string {
  return pathname === "" ? "/" : pathname.replace(/\/+$/, "") || "/";
}

function pathSegments(path: string): string[] {
  return normalizePathname(path).split("/").filter(Boolean);
}

import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../auth/useAuth";

export function PublicOnlyRoute() {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

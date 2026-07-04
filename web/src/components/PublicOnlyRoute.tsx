import { Navigate, Outlet, useLocation } from "react-router-dom";

import { recoveryPath } from "../auth/recoveryPath";
import { useAuth } from "../auth/useAuth";

export function PublicOnlyRoute() {
  const { isAuthenticated, isSessionRestoring } = useAuth();
  const location = useLocation();

  if (isSessionRestoring) {
    return null;
  }

  if (isAuthenticated) {
    return <Navigate to={recoveryPath(location.state)} replace />;
  }

  return <Outlet />;
}

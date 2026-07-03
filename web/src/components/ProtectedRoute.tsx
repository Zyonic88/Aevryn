import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth/useAuth";

export function ProtectedRoute() {
  const { isAuthenticated, isSessionRestoring } = useAuth();
  const location = useLocation();

  if (isSessionRestoring) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

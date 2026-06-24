import { isAxiosError } from "axios";
import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useCurrentUser } from "../hooks/useCurrentUser";

type AuthBootstrapProps = {
  children: ReactNode;
};

export function AuthBootstrap({ children }: AuthBootstrapProps) {
  const { isLoading, isError, error } = useCurrentUser();

  if (isLoading) {
    return <div className="auth-bootstrap">Loading account...</div>;
  }

  if (isError) {
    if (isAxiosError(error) && error.response?.status === 404) {
      return <Navigate to="/sign-up" replace />;
    }

    return (
      <div className="auth-bootstrap auth-bootstrap--error">
        Could not load your account. Please sign in again or contact support.
      </div>
    );
  }

  return children;
}

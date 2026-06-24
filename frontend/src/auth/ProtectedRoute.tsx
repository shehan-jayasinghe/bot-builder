import { RedirectToSignIn, SignedIn, SignedOut, useUser } from "@clerk/clerk-react";
import { Navigate, Outlet } from "react-router-dom";

function SignedInGate() {
  const { isLoaded, user } = useUser();

  if (!isLoaded) {
    return <div className="auth-bootstrap">Loading...</div>;
  }

  const primaryEmail = user?.primaryEmailAddress?.emailAddress;
  const emailVerified = user?.primaryEmailAddress?.verification?.status === "verified";

  if (!emailVerified) {
    return (
      <Navigate
        to="/verify-email"
        replace
        state={{ email: primaryEmail ?? undefined }}
      />
    );
  }

  return <Outlet />;
}

export function ProtectedRoute() {
  return (
    <>
      <SignedIn>
        <SignedInGate />
      </SignedIn>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </>
  );
}

import { SignIn } from "@clerk/clerk-react";
import { useLocation } from "react-router-dom";

type SignInLocationState = {
  email?: string;
  verified?: boolean;
};

export function SignInPage() {
  const location = useLocation();
  const state = (location.state ?? {}) as SignInLocationState;

  return (
    <div className="auth-page">
      <div className="auth-page__stack">
        {state.verified && (
          <div className="auth-page__notice auth-page__notice--success">
            Email verified. Sign in to continue.
          </div>
        )}
        <SignIn
          routing="path"
          path="/sign-in"
          signUpUrl="/sign-up"
          fallbackRedirectUrl="/"
          initialValues={state.email ? { emailAddress: state.email } : undefined}
        />
      </div>
    </div>
  );
}

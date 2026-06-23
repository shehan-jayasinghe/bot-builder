import { SignIn } from "@clerk/clerk-react";

export function SignInPage() {
  return (
    <div className="auth-page">
      <SignIn routing="path" path="/sign-in" signUpUrl="/sign-in" />
    </div>
  );
}

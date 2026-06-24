import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { resendVerificationEmail, verifyEmailCode } from "../../api/auth";

type VerifyEmailLocationState = {
  email?: string;
  verificationSent?: boolean;
  verificationId?: string;
};

export function VerifyEmailPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = (location.state ?? {}) as VerifyEmailLocationState;
console.log(state,"sdsss");
  const emailFromQuery = new URLSearchParams(location.search).get("email") ?? undefined;
  const email = state.email ?? emailFromQuery ?? "";

  const [verificationId, setVerificationId] = useState(state.verificationId ?? "");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState<string | null>(
    state.verificationSent === false
      ? "Account created, but we could not send the verification code. Please resend it below."
      : "We sent a 6-digit verification code to your email. Enter it below.",
  );
  const [error, setError] = useState<string | null>(null);

  const verifyMutation = useMutation({
    mutationFn: () => verifyEmailCode(email, code, verificationId),
    onSuccess: (data) => {
      setError(null);
      navigate("/sign-in", {
        replace: true,
        state: { email, verified: data.email_verified },
      });
    },
    onError: (err: unknown) => {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setError(detail ?? "Invalid or expired verification code.");
    },
  });

  const resendMutation = useMutation({
    mutationFn: () => resendVerificationEmail(email),
    onSuccess: (data) => {
      setError(null);
      setMessage(data.message);
      if (data.verification_id) {
        setVerificationId(data.verification_id);
      }
    },
    onError: (err: unknown) => {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setError(detail ?? "Could not resend verification code.");
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email) {
      setError("Email address is missing. Please register again.");
      return;
    }
    if (!verificationId) {
      setError("Verification session expired. Please resend the code.");
      return;
    }
    if (code.length !== 6) {
      setError("Enter the 6-digit verification code.");
      return;
    }
    setError(null);
    verifyMutation.mutate();
  }

  function handleResend() {
    if (!email) {
      setError("Email address is missing. Please register again.");
      return;
    }
    setError(null);
    resendMutation.mutate();
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <p className="auth-card__eyebrow">EMAIL VERIFICATION</p>
        <h1 className="auth-card__title">Enter verification code</h1>
        <p className="auth-card__subtitle">
          {email ? (
            <>
              Enter the 6-digit code sent to <strong>{email}</strong>.
            </>
          ) : (
            "Enter the 6-digit code sent to your email."
          )}
        </p>

        {message && <p className="auth-page__notice auth-page__notice--success">{message}</p>}
        {error && <p className="auth-form__error">{error}</p>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-form__field">
            <span>Verification code</span>
            <input
              required
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="\d{6}"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder="123456"
            />
          </label>

          <button
            type="submit"
            className="btn btn--primary auth-form__submit"
            disabled={!email || !verificationId || code.length !== 6 || verifyMutation.isPending}
          >
            {verifyMutation.isPending ? "Verifying..." : "Verify email"}
          </button>

          <button
            type="button"
            className="btn auth-form__submit"
            onClick={handleResend}
            disabled={!email || resendMutation.isPending}
          >
            {resendMutation.isPending ? "Sending..." : "Resend code"}
          </button>
        </form>

        <p className="auth-card__footer">
          Wrong email?{" "}
          <Link to="/sign-up" className="auth-card__link">
            Register again
          </Link>
        </p>
      </div>
    </div>
  );
}

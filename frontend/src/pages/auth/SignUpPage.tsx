import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { registerUser, type RegisterRequest } from "../../api/auth";
import { AuthPageLayout } from "./AuthPageLayout";

const INDUSTRIES = [
  { value: "financial_services", label: "Financial Services" },
  { value: "logistics", label: "Logistics" },
  { value: "travel", label: "Travel" },
  { value: "healthcare", label: "Healthcare" },
  { value: "insurance", label: "Insurance" },
  { value: "other", label: "Other" },
];

export function SignUpPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState<RegisterRequest>({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    organization_name: "",
    industry: "",
  });
  const [error, setError] = useState<string | null>(null);

  const registerMutation = useMutation({
    mutationFn: registerUser,
    onSuccess: (data) => {
      console.log(data,"data");
      navigate("/verify-email", {
        replace: true,
        state: {
          email: form.email,
          verificationSent: data.verification_sent,
          verificationId: data.verification_id ?? undefined,
        },
      });
    },
    onError: (err: unknown) => {
      const message =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setError(message ?? "Registration failed. Please try again.");
    },
  });

  function handleChange(field: keyof RegisterRequest, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    registerMutation.mutate({
      ...form,
      industry: form.industry || undefined,
    });
  }

  return (
    <AuthPageLayout
      title="Create your account"
      subtitle="Set up your organization and root user to start building agents."
      footerText="Already have an account?"
      footerLinkText="Sign in"
      footerLinkTo="/sign-in"
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="auth-form__field">
          <span>First name</span>
          <input
            required
            value={form.first_name}
            onChange={(e) => handleChange("first_name", e.target.value)}
            placeholder="Amanda"
          />
        </label>

        <label className="auth-form__field">
          <span>Last name</span>
          <input
            required
            value={form.last_name}
            onChange={(e) => handleChange("last_name", e.target.value)}
            placeholder="Jayasinghe"
          />
        </label>

        <label className="auth-form__field">
          <span>Email</span>
          <input
            required
            type="email"
            value={form.email}
            onChange={(e) => handleChange("email", e.target.value)}
            placeholder="you@company.com"
          />
        </label>

        <label className="auth-form__field">
          <span>Password</span>
          <input
            required
            type="password"
            minLength={8}
            value={form.password}
            onChange={(e) => handleChange("password", e.target.value)}
            placeholder="Minimum 8 characters"
          />
        </label>

        <label className="auth-form__field">
          <span>Organization name</span>
          <input
            required
            value={form.organization_name}
            onChange={(e) => handleChange("organization_name", e.target.value)}
            placeholder="abc bank"
          />
        </label>

        <label className="auth-form__field">
          <span>Industry</span>
          <select value={form.industry ?? ""} onChange={(e) => handleChange("industry", e.target.value)}>
            <option value="">Select your industry</option>
            {INDUSTRIES.map((industry) => (
              <option key={industry.value} value={industry.value}>
                {industry.label}
              </option>
            ))}
          </select>
        </label>

        {error && <p className="auth-form__error">{error}</p>}

        <button type="submit" className="btn btn--primary auth-form__submit" disabled={registerMutation.isPending}>
          {registerMutation.isPending ? "Creating account..." : "Create account"}
        </button>
      </form>
    </AuthPageLayout>
  );
}

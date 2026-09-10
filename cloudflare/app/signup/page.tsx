import { createAccount } from "./actions";

import "../auth.css";

export default function SignUpPage() {
  return (
    <main className="auth">
      <a href="/">
        <img className="auth__logo" src="/brand/agentforge-logo.svg" alt="AgentForge" />
      </a>
      <div className="auth__card">
        <p className="auth__eyebrow">AGENTFORGE</p>
        <h1 className="auth__title">Create your account</h1>
        <p className="auth__subtitle">Set up your organization and start building agents.</p>
        <form action={createAccount}>
          <label className="auth__field">
            Organization name
            <input name="organization_name" required placeholder="Acme Inc" />
          </label>
          <label className="auth__field">
            Name
            <input name="name" required placeholder="Amanda Jayasinghe" />
          </label>
          <label className="auth__field">
            Email
            <input name="email" type="email" required placeholder="you@company.com" />
          </label>
          <label className="auth__field">
            Password
            <input name="password" type="password" required minLength={8} />
          </label>
          <button className="auth__submit" type="submit">
            Create account
          </button>
        </form>
        <p className="auth__footer">
          Already have an account? <a href="/signin">Sign in</a>
        </p>
      </div>
    </main>
  );
}

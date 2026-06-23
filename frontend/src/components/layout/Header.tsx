import { UserButton } from "@clerk/clerk-react";

export function Header() {
  return (
    <header className="header">
      <div className="header__left" />
      <div className="header__actions">
        <button type="button" className="btn btn--ghost">
          ▷ Preview
        </button>
        <button type="button" className="btn btn--primary">
          🚀 Publish
        </button>
        <a className="header__link" href="https://docs.example.com" target="_blank" rel="noreferrer">
          Docs
        </a>
        <UserButton afterSignOutUrl="/sign-in" />
      </div>
    </header>
  );
}

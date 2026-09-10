import { signOut } from "@/auth";

export function Header() {
  return (
    <header className="header">
      <div className="header__left" />
      <div className="header__actions">
        <a
          className="header__link"
          href="https://docs.example.com"
          target="_blank"
          rel="noreferrer"
        >
          Docs
        </a>
        <form
          action={async () => {
            "use server";
            await signOut({ redirectTo: "/signin" });
          }}
        >
          <button className="header__link" type="submit">
            Sign out
          </button>
        </form>
      </div>
    </header>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";

import { signOutAction } from "./actions";

type HeaderProps = {
  userName?: string | null;
  userEmail?: string | null;
};

export function Header({ userName = "User", userEmail = "" }: HeaderProps) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const avatarLetter = userName?.charAt(0)?.toUpperCase() || "?";

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <header className="header">
      <div className="header__left" />
      <div className="header__actions" ref={menuRef}>
        <button
          type="button"
          className="header__user-trigger"
          aria-expanded={open}
          aria-haspopup="menu"
          onClick={() => setOpen((value) => !value)}
        >
          <span className="header__user-avatar">{avatarLetter}</span>
          <span className="header__user-meta">
            <span className="header__user-name">{userName}</span>
            {userEmail ? <span className="header__user-email">{userEmail}</span> : null}
          </span>
          <span className="header__user-chevron" aria-hidden="true">
            ▾
          </span>
        </button>

        {open ? (
          <div className="header__menu" role="menu">
            <a
              className="header__menu-item"
              href="https://docs.example.com"
              target="_blank"
              rel="noreferrer"
              role="menuitem"
              onClick={() => setOpen(false)}
            >
              Docs
            </a>
            <form action={signOutAction}>
              <button className="header__menu-item" type="submit" role="menuitem">
                Sign out
              </button>
            </form>
          </div>
        ) : null}
      </div>
    </header>
  );
}

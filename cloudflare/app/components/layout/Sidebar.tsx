"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { MAIN_NAV } from "@/lib/constants/navigation";

type SidebarProps = {
  organizationName?: string | null;
  userName?: string | null;
  userEmail?: string | null;
};

export function Sidebar({
  organizationName = "Organization",
  userName = "User",
  userEmail = "",
}: SidebarProps) {
  const pathname = usePathname();
  const avatarLetter = userName?.charAt(0)?.toUpperCase() || "?";

  return (
    <aside className="sidebar">
      <div className="sidebar__top">
        <div className="sidebar__brand">
          <span className="sidebar__brand-icon" aria-hidden="true">
            ◉
          </span>
          <span className="sidebar__brand-name">{organizationName}</span>
          <span className="sidebar__brand-chevron" aria-hidden="true">
            ▾
          </span>
        </div>

        <nav className="sidebar-nav">
          {MAIN_NAV.map((item) => {
            const isActive =
              pathname === item.path || pathname.startsWith(`${item.path}/`);

            return (
              <Link
                key={item.path}
                href={item.path}
                className={[
                  "sidebar-nav__item",
                  isActive ? "sidebar-nav__item--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="sidebar__footer">
        <div className="sidebar__user">
          <span className="sidebar__user-avatar">{avatarLetter}</span>
          <div>
            <div className="sidebar__user-name">{userName}</div>
            {userEmail ? <div className="sidebar__user-email">{userEmail}</div> : null}
          </div>
        </div>
      </div>
    </aside>
  );
}

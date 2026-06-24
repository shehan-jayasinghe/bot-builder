import { NavLink } from "react-router-dom";

import { MAIN_NAV } from "../../constants/navigation";
import { useCurrentUser } from "../../hooks/useCurrentUser";
import { NavIcon } from "../ui/NavIcon";

type SidebarNavItemProps = {
  label: string;
  path: string;
  icon?: string;
  nested?: boolean;
};

function SidebarNavItem({ label, path, icon, nested = false }: SidebarNavItemProps) {
  return (
    <NavLink
      to={path}
      end={path === "/"}
      className={({ isActive }) =>
        ["sidebar-nav__item", nested && "sidebar-nav__item--nested", isActive && "sidebar-nav__item--active"]
          .filter(Boolean)
          .join(" ")
      }
    >
      {icon ? <NavIcon name={icon} className="sidebar-nav__icon" /> : null}
      <span>{label}</span>
    </NavLink>
  );
}

export function Sidebar() {
  const { data } = useCurrentUser();
  const user = data?.user;
  const organization = data?.organization;
  const avatarLetter = user?.first_name?.charAt(0)?.toUpperCase() ?? "?";

  return (
    <aside className="sidebar">
      <div className="sidebar__top">
        <div className="sidebar__brand">
          <span className="sidebar__brand-icon" aria-hidden="true">
            ◉
          </span>
          <span className="sidebar__brand-name">{organization?.name ?? "Organization"}</span>
          <span className="sidebar__brand-chevron" aria-hidden="true">
            ▾
          </span>
        </div>

        <nav className="sidebar-nav">
          {MAIN_NAV.map((item) => {
            const isWorkflows = item.label === "Workflows";

            return (
              <div key={item.path} className="sidebar-nav__group">
                <SidebarNavItem label={item.label} path={item.path} icon={item.icon} />
                {isWorkflows && (
                  <div className="sidebar-nav__children">
                    <button type="button" className="sidebar-nav__create">
                      + Create
                    </button>
                    {item.children?.map((child) => (
                      <SidebarNavItem key={child.path} label={child.label} path={child.path} nested />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </div>

      <div className="sidebar__footer">
        <div className="sidebar__user">
          <span className="sidebar__user-avatar" aria-hidden="true">
            {avatarLetter}
          </span>
          <div>
            <div className="sidebar__user-name">{user?.full_name ?? "User"}</div>
            <div className="sidebar__user-email">{user?.email ?? ""}</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

import { NavLink } from "react-router-dom";

import { MAIN_NAV } from "../../constants/navigation";

type SidebarNavItemProps = {
  label: string;
  path: string;
  nested?: boolean;
};

function SidebarNavItem({ label, path, nested = false }: SidebarNavItemProps) {
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
      {label}
    </NavLink>
  );
}

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar__top">
        <div className="sidebar__brand">
          <span className="sidebar__brand-icon" aria-hidden="true">
            ◉
          </span>
          <span className="sidebar__brand-name">abc bank</span>
          <span className="sidebar__brand-chevron" aria-hidden="true">
            ▾
          </span>
        </div>

        <nav className="sidebar-nav">
          {MAIN_NAV.map((item) => {
            const isWorkflows = item.label === "Workflows";

            return (
              <div key={item.path} className="sidebar-nav__group">
                <SidebarNavItem label={item.label} path={item.path} />
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
            A
          </span>
          <div>
            <div className="sidebar__user-name">Amanda</div>
            <div className="sidebar__user-email">amanda@example.com</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

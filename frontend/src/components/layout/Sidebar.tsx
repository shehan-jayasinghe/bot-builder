import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink, useNavigate } from "react-router-dom";

import { createWorkflow, listWorkflows } from "../../api/workflows";
import { MAIN_NAV } from "../../constants/navigation";
import { MAX_WORKFLOWS_PER_ORG } from "../../constants/workflows";
import { useCurrentUser } from "../../hooks/useCurrentUser";
import { getApiError } from "../../utils/apiError";
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
      end={path === "/workflows"}
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
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data } = useCurrentUser();
  const user = data?.user;
  const organization = data?.organization;
  const avatarLetter = user?.first_name?.charAt(0)?.toUpperCase() ?? "?";

  const workflowsQuery = useQuery({
    queryKey: ["workflows"],
    queryFn: () => listWorkflows(),
  });

  const createMutation = useMutation({
    mutationFn: createWorkflow,
    onSuccess: (workflow) => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      navigate(`/workflows/${workflow.id}`);
    },
    onError: (error) => {
      window.alert(getApiError(error));
    },
  });

  const workflowItems = workflowsQuery.data?.items ?? [];
  const atWorkflowLimit = (workflowsQuery.data?.total ?? 0) >= MAX_WORKFLOWS_PER_ORG;

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
                    <button
                      type="button"
                      className={["sidebar-nav__create", atWorkflowLimit && "sidebar-nav__create--disabled"]
                        .filter(Boolean)
                        .join(" ")}
                      disabled={atWorkflowLimit || createMutation.isPending}
                      title={atWorkflowLimit ? `Maximum of ${MAX_WORKFLOWS_PER_ORG} workflows` : "Create workflow"}
                      onClick={() => createMutation.mutate({})}
                    >
                      {createMutation.isPending ? "Creating…" : "+ Create"}
                    </button>
                    {workflowItems.map((workflow) => (
                      <SidebarNavItem
                        key={workflow.id}
                        label={workflow.name}
                        path={`/workflows/${workflow.id}`}
                        nested
                      />
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

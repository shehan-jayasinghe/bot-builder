export type NavItem = {
  label: string;
  path: string;
  icon: string;
};

export const MAIN_NAV: NavItem[] = [
  { label: "Agent", path: "/agent", icon: "agent" },
  { label: "Workflows", path: "/workflows", icon: "workflows" },
  { label: "Data Sources", path: "/data-sources", icon: "data-sources" },
  { label: "Channels", path: "/channels", icon: "channels" },
  { label: "Conversations", path: "/conversations", icon: "conversations" },
  { label: "Analytics", path: "/analytics", icon: "analytics" },
  { label: "Schedulers", path: "/schedulers", icon: "schedulers" },
  { label: "Settings", path: "/settings", icon: "settings" },
];

import type { NavItem } from "../types/navigation";

export const MAIN_NAV: NavItem[] = [
  { label: "Agent", path: "/agent" },
  {
    label: "Workflows",
    path: "/workflows",
    children: [{ label: "Welcome", path: "/" }],
  },
  { label: "Data Sources", path: "/data-sources" },
  { label: "Channels", path: "/channels" },
  { label: "Conversations", path: "/conversations" },
  { label: "Analytics", path: "/analytics" },
  { label: "Schedulers", path: "/schedulers" },
  { label: "Settings", path: "/settings" },
];

import type { NavItem } from "../types/navigation";

export const MAIN_NAV: NavItem[] = [
  { label: "Agent", path: "/agent", icon: "agent" },
  {
    label: "Workflows",
    path: "/workflows",
    icon: "workflows",
    children: [{ label: "Welcome", path: "/" }],
  },
  { label: "Data Sources", path: "/data-sources", icon: "data-sources" },
  { label: "Channels", path: "/channels", icon: "channels" },
  { label: "Conversations", path: "/conversations", icon: "conversations" },
  { label: "Analytics", path: "/analytics", icon: "analytics" },
  { label: "Schedulers", path: "/schedulers", icon: "schedulers" },
  { label: "Settings", path: "/settings", icon: "settings" },
];

export const AGENT_DETAIL_TABS = [
  { label: "Agent", icon: "agent" },
  { label: "Sub Agents", icon: "sub-agents" },
  { label: "Skills", icon: "skills" },
  { label: "Memory", icon: "memory" },
  { label: "LLM", icon: "llm" },
] as const;

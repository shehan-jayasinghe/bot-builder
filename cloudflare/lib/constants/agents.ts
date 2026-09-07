import "server-only";

export const AgentStatus = {
  Draft: "draft",
  Published: "published",
} as const;

export type AgentStatus = (typeof AgentStatus)[keyof typeof AgentStatus];

import "server-only";

export const WorkflowStatus = {
  Draft: "draft",
  Published: "published",
} as const;

export type WorkflowStatus = (typeof WorkflowStatus)[keyof typeof WorkflowStatus];

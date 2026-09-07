import "server-only";

export const ToolStatus = {
  Active: "active",
  Inactive: "inactive",
} as const;

export type ToolStatus = (typeof ToolStatus)[keyof typeof ToolStatus];

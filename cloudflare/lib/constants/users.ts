import "server-only";

export const UserRole = {
  Owner: "owner",
  Admin: "admin",
  Member: "member",
} as const;

export type UserRole = (typeof UserRole)[keyof typeof UserRole];

import "server-only";

export const ChannelStatus = {
  Active: "active",
  Inactive: "inactive",
} as const;

export type ChannelStatus = (typeof ChannelStatus)[keyof typeof ChannelStatus];

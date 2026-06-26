import type { ExecutorName } from "./executor";

export type Tool = {
  id: string;
  name: string;
  description: string;
  executor: ExecutorName;
  connector_id: string;
  config: Record<string, unknown>;
  status: string;
  agent_id: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
};

export type ToolListItem = Tool;

export type ListToolsResponse = {
  items: ToolListItem[];
  total: number;
};

export type CreateToolPayload = {
  name: string;
  description: string;
  executor: ExecutorName;
  connector_id: string;
  config: Record<string, unknown>;
};

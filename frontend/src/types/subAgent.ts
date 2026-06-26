export type SubAgentStatus = "active" | "disabled";

export type CreateSubAgentPayload = {
  name: string;
  description?: string | null;
  instructions: string;
  tool_ids?: string[];
  knowledge_base_ids?: string[];
  workflow_ids?: string[];
  parameters?: [];
};

export type SubAgent = {
  id: string;
  name: string;
  description?: string | null;
  instructions: string;
  tool_ids: string[];
  knowledge_base_ids: string[];
  workflow_ids: string[];
  parameters: [];
  status: SubAgentStatus | string;
  agent_id: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
};

export type SubAgentListItem = {
  id: string;
  name: string;
  description?: string | null;
  status: SubAgentStatus | string;
  tool_count: number;
  knowledge_base_count: number;
  workflow_count: number;
  parameter_count: number;
  agent_id: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
};

export type ListSubAgentsResponse = {
  items: SubAgentListItem[];
  total: number;
};

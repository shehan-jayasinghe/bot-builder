export type WorkflowNodeType =
  | "start"
  | "message"
  | "input"
  | "output"
  | "action"
  | "dev"
  | "flow"
  | "variable";

export type WorkflowNode = {
  id: string;
  type: WorkflowNodeType | string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
};

export type WorkflowEdge = {
  id: string;
  source: string;
  target: string;
};

export type Workflow = {
  id: string;
  name: string;
  description?: string | null;
  agent_id?: string | null;
  status: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  organization_id: string;
  created_at: string;
  updated_at: string;
};

export type WorkflowListItem = {
  id: string;
  name: string;
  description?: string | null;
  agent_id?: string | null;
  status: string;
  node_count: number;
  organization_id: string;
  created_at: string;
  updated_at: string;
};

export type ListWorkflowsResponse = {
  items: WorkflowListItem[];
  total: number;
};

export type CreateWorkflowPayload = {
  name?: string;
  description?: string;
  agent_id?: string;
  nodes?: WorkflowNode[];
  edges?: WorkflowEdge[];
};

export type UpdateWorkflowPayload = {
  name?: string;
  description?: string | null;
  agent_id?: string | null;
  nodes?: WorkflowNode[];
  edges?: WorkflowEdge[];
};

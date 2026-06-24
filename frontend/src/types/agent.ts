export type Industry =
  | "financial_services"
  | "logistics"
  | "travel"
  | "healthcare"
  | "insurance"
  | "other";

export type AgentType =
  | "payment_collections"
  | "customer_onboarding"
  | "customer_support_triage";

export type AgentStatus = "draft" | "published";

export type GuardrailItem = {
  key: string;
  label: string;
  instruction: string;
  enabled: boolean;
};

export type LLMConfig = {
  model_id: string;
  region: string;
  temperature: number;
  max_output_tokens: number;
};

export type CreateAgentRequest = {
  name: string;
  description?: string | null;
  industry: Industry;
  agent_type?: AgentType | null;
  guardrails?: GuardrailItem[] | null;
};

export type Agent = {
  id: string;
  name: string;
  description?: string | null;
  industry: Industry;
  agent_type?: AgentType | null;
  system_prompt: string;
  personality: string;
  tone: string;
  guardrails: GuardrailItem[];
  llm_config: LLMConfig;
  status: AgentStatus | string;
  organization_id: string;
  created_at: string;
};

export type AgentListItem = {
  id: string;
  name: string;
  description?: string | null;
  industry: Industry;
  agent_type?: AgentType | null;
  status: AgentStatus | string;
  organization_id: string;
  created_at: string;
};

export type ListAgentsResponse = {
  items: AgentListItem[];
  total: number;
};

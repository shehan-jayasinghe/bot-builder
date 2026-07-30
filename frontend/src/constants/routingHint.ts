export type CapabilityKind = "tool" | "knowledgebase" | "workflow" | "sub_agent";

export const ROUTING_HINT_MAX_LENGTH = 500;

const PLACEHOLDERS: Record<CapabilityKind, string> = {
  tool: "Use when the user asks about account balance or loyalty points.",
  knowledgebase: "Search when the user asks about product docs, policies, or FAQs.",
  workflow: "Run when greeting a new user or collecting onboarding details.",
  sub_agent: "Delegate when the user has billing disputes or payment issues.",
};

const LABELS: Record<CapabilityKind, string> = {
  tool: "tool",
  knowledgebase: "knowledge base",
  workflow: "workflow",
  sub_agent: "sub-agent",
};

export function routingHintPlaceholder(kind: CapabilityKind): string {
  return PLACEHOLDERS[kind];
}

export function capabilityKindLabel(kind: CapabilityKind): string {
  return LABELS[kind];
}

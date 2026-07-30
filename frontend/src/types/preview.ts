export type RuntimeGraphNodeType =
  | "orchestrator"
  | "tool"
  | "workflow"
  | "sub_agent"
  | "knowledge_base";

export type RuntimeGraphEdgeKind = "tool" | "workflow" | "sub_agent" | "knowledge_base";

export type RuntimeGraphOrchestrator = {
  id: string;
  name: string;
  kind: string;
  status?: string | null;
  description?: string | null;
};

export type RuntimeGraphNode = {
  id: string;
  type: RuntimeGraphNodeType;
  label: string;
  description: string | null;
};

export type RuntimeGraphEdge = {
  id: string;
  source: string;
  target: string;
  kind: RuntimeGraphEdgeKind;
};

export type RuntimeGraphResponse = {
  agent_id: string;
  organization_id: string;
  orchestrator: RuntimeGraphOrchestrator;
  nodes: RuntimeGraphNode[];
  edges: RuntimeGraphEdge[];
};

export type PreviewTraceEvent = {
  type: string;
  at: string;
  data: Record<string, unknown>;
};

export type PreviewTraceTurn = {
  turn_id: string;
  started_at: string;
  events: PreviewTraceEvent[];
  routing_decision: Record<string, unknown> | null;
};

export type PreviewTraceResponse = {
  agent_id: string;
  sender_id: string;
  source: string | null;
  turns: PreviewTraceTurn[];
};

export type ChatButton = {
  title: string;
  payload: string;
};

export type ChatMessage = {
  recipient_id: string;
  text: string | null;
  buttons: ChatButton[] | null;
};

export type PreviewChatRequest = {
  sender_id: string;
  message: string;
  metadata?: Record<string, unknown>;
};

export type PreviewChatResponse = {
  messages: ChatMessage[];
};

export type PositionedRuntimeGraphNode = RuntimeGraphNode & {
  position: { x: number; y: number };
};

import type { PreviewTraceEvent, PreviewTraceTurn } from "../types/preview";

export type TraceTimelineItemKind =
  | "input"
  | "output"
  | "llm"
  | "tool"
  | "tool_complete"
  | "workflow"
  | "delegate"
  | "blocked"
  | "other";

export type TraceTimelineItem = {
  id: string;
  turnId: string;
  kind: TraceTimelineItemKind;
  label: string;
  detail?: string;
  at: string;
  nested?: TraceTimelineItem[];
};

export type TraceTurnGroup = {
  turnId: string;
  startedAt: string;
  items: TraceTimelineItem[];
};

const HIDDEN_EVENT_TYPES = new Set(["bundle_loaded"]);

const LLM_EVENT_TYPES = new Set(["guardrail_complete", "rag_complete", "rag_skipped"]);

const WORKFLOW_GROUP_TYPES = new Set([
  "workflow_enter",
  "workflow_step",
  "slot_captured",
  "workflow_exit",
]);

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatTurnTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function outputDetail(data: Record<string, unknown>): string {
  if (typeof data.text === "string" && data.text) {
    return data.text;
  }
  if (Array.isArray(data.texts) && data.texts.length > 0) {
    return data.texts.map(String).join("\n\n");
  }
  const count = data.message_count;
  if (typeof count === "number" && count > 0) {
    return `${count} message${count === 1 ? "" : "s"}`;
  }
  return "";
}

function llmStepDetail(event: PreviewTraceEvent): string {
  if (event.type === "guardrail_complete") {
    return "guardrails passed";
  }
  if (event.type === "rag_skipped") {
    return "RAG skipped";
  }
  if (event.type === "rag_complete") {
    const chunks = event.data.chunk_count;
    const length = event.data.context_length;
    if (typeof chunks === "number" && chunks > 0) {
      return `retrieved ${chunks} chunk${chunks === 1 ? "" : "s"}`;
    }
    if (typeof length === "number" && length > 0) {
      return `${length} chars of context`;
    }
    return "retrieval complete";
  }
  return event.type;
}

function buildLlmGroup(turnId: string, events: PreviewTraceEvent[]): TraceTimelineItem {
  return {
    id: `${turnId}-llm-group-${events[0]?.at ?? ""}`,
    turnId,
    kind: "llm",
    label: "LLM Request",
    at: events[0]?.at ?? "",
    nested: events.map((event, index) => ({
      id: `${turnId}-llm-${event.type}-${index}`,
      turnId,
      kind: "llm",
      label: "LLM Request",
      detail: llmStepDetail(event),
      at: event.at,
    })),
  };
}

function workflowStepDetail(event: PreviewTraceEvent): string {
  if (event.type === "workflow_enter") {
    const name = event.data.workflow_name;
    const reason = event.data.reason;
    if (typeof name === "string" && name) {
      return reason ? `${name} (${String(reason)})` : name;
    }
    return "workflow started";
  }
  if (event.type === "workflow_step") {
    const nodeType = event.data.type;
    const nodeId = event.data.node_id;
    if (typeof nodeType === "string" && typeof nodeId === "string") {
      return `${nodeType} · ${nodeId}`;
    }
    return String(nodeType ?? "step");
  }
  if (event.type === "slot_captured") {
    const slot = event.data.slot_name;
    return typeof slot === "string" ? `captured ${slot}` : "slot captured";
  }
  if (event.type === "workflow_exit") {
    return "workflow finished";
  }
  return event.type.replace(/_/g, " ");
}

function buildWorkflowGroup(turnId: string, events: PreviewTraceEvent[]): TraceTimelineItem {
  const enter = events.find((event) => event.type === "workflow_enter");
  const workflowName = enter?.data.workflow_name;
  const label =
    typeof workflowName === "string" && workflowName
      ? `Workflow · ${workflowName}`
      : "Workflow";

  return {
    id: `${turnId}-workflow-group-${events[0]?.at ?? ""}`,
    turnId,
    kind: "workflow",
    label,
    at: events[0]?.at ?? "",
    nested: events.map((event, index) => ({
      id: `${turnId}-workflow-${event.type}-${index}`,
      turnId,
      kind: "workflow",
      label: event.type === "workflow_enter" ? "Started" : event.type === "workflow_exit" ? "Finished" : "Step",
      detail: workflowStepDetail(event),
      at: event.at,
    })),
  };
}

function buildDelegateGroup(turnId: string, events: PreviewTraceEvent[]): TraceTimelineItem {
  const start = events.find((event) => event.type === "sub_agent_start");
  const name = start?.data.sub_agent_name;
  const label = typeof name === "string" && name ? `Sub-agent · ${name}` : "Sub-agent";

  return {
    id: `${turnId}-delegate-group-${events[0]?.at ?? ""}`,
    turnId,
    kind: "delegate",
    label,
    at: events[0]?.at ?? "",
    nested: events.map((event, index) => ({
      id: `${turnId}-delegate-${event.type}-${index}`,
      turnId,
      kind: "delegate",
      label: event.type === "sub_agent_start" ? "Delegated" : "Complete",
      detail:
        event.type === "sub_agent_complete" && typeof event.data.reply_count === "number"
          ? `${event.data.reply_count} repl${event.data.reply_count === 1 ? "y" : "ies"}`
          : undefined,
      at: event.at,
    })),
  };
}

function mapEvent(event: PreviewTraceEvent, turnId: string, index: number): TraceTimelineItem | null {
  if (HIDDEN_EVENT_TYPES.has(event.type)) {
    return null;
  }

  const id = `${turnId}-${event.type}-${index}`;

  switch (event.type) {
    case "input_message":
      return {
        id,
        turnId,
        kind: "input",
        label: "Input Message",
        detail: String(event.data.message ?? ""),
        at: event.at,
      };
    case "output_message": {
      const detail = outputDetail(event.data);
      return {
        id,
        turnId,
        kind: "output",
        label: "Output Message",
        detail: detail || undefined,
        at: event.at,
      };
    }
    case "guardrail_complete":
    case "rag_complete":
    case "rag_skipped":
      return null;
    case "workflow_enter":
    case "workflow_step":
    case "slot_captured":
    case "workflow_exit":
      return null;
    case "sub_agent_start":
    case "sub_agent_complete":
      return null;
    case "guardrail_blocked":
      return {
        id,
        turnId,
        kind: "blocked",
        label: "Guardrail Blocked",
        at: event.at,
      };
    case "tool_start":
      return {
        id,
        turnId,
        kind: "tool",
        label: "Tool Start",
        detail: String(event.data.tool ?? event.data.name ?? "tool"),
        at: event.at,
      };
    case "tool_complete":
      return {
        id,
        turnId,
        kind: "tool_complete",
        label: "Tool Complete",
        detail: String(event.data.tool ?? event.data.name ?? "tool"),
        at: event.at,
      };
    case "tool_error":
      return {
        id,
        turnId,
        kind: "blocked",
        label: "Tool Error",
        detail: String(event.data.tool ?? event.data.error ?? ""),
        at: event.at,
      };
    case "rag_error":
      return {
        id,
        turnId,
        kind: "blocked",
        label: "RAG Error",
        detail: String(event.data.detail ?? ""),
        at: event.at,
      };
    default:
      return {
        id,
        turnId,
        kind: "other",
        label: event.type.replace(/_/g, " "),
        at: event.at,
      };
  }
}

function buildTurnItems(turn: PreviewTraceTurn): TraceTimelineItem[] {
  const items: TraceTimelineItem[] = [];
  let index = 0;

  while (index < turn.events.length) {
    const event = turn.events[index];

    if (LLM_EVENT_TYPES.has(event.type)) {
      const llmEvents: PreviewTraceEvent[] = [];
      while (index < turn.events.length && LLM_EVENT_TYPES.has(turn.events[index].type)) {
        llmEvents.push(turn.events[index]);
        index += 1;
      }
      if (llmEvents.length > 0) {
        items.push(buildLlmGroup(turn.turn_id, llmEvents));
      }
      continue;
    }

    if (event.type === "workflow_enter") {
      const workflowEvents: PreviewTraceEvent[] = [];
      while (index < turn.events.length && WORKFLOW_GROUP_TYPES.has(turn.events[index].type)) {
        workflowEvents.push(turn.events[index]);
        index += 1;
      }
      if (workflowEvents.length > 0) {
        items.push(buildWorkflowGroup(turn.turn_id, workflowEvents));
      }
      continue;
    }

    if (event.type === "sub_agent_start") {
      const delegateEvents: PreviewTraceEvent[] = [event];
      index += 1;
      if (index < turn.events.length && turn.events[index].type === "sub_agent_complete") {
        delegateEvents.push(turn.events[index]);
        index += 1;
      }
      items.push(buildDelegateGroup(turn.turn_id, delegateEvents));
      continue;
    }

    const mapped = mapEvent(event, turn.turn_id, index);
    if (mapped) {
      items.push(mapped);
    }
    index += 1;
  }

  return items;
}

export function buildTraceTurnGroups(turns: PreviewTraceTurn[]): TraceTurnGroup[] {
  return turns
    .map((turn) => ({
      turnId: turn.turn_id,
      startedAt: turn.started_at,
      items: buildTurnItems(turn),
    }))
    .filter((group) => group.items.length > 0);
}

export function buildTraceTimeline(turns: PreviewTraceTurn[]): TraceTimelineItem[] {
  return buildTraceTurnGroups(turns).flatMap((group) => group.items);
}

export function formatTraceTimestamp(iso: string): string {
  return formatTime(iso);
}

export function formatTraceTurnTimestamp(iso: string): string {
  return formatTurnTime(iso);
}

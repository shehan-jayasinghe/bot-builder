import type { PreviewTraceEvent, PreviewTraceTurn } from "../types/preview";

export type TraceTimelineItemKind =
  | "input"
  | "output"
  | "llm"
  | "tool"
  | "tool_complete"
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

function llmNested(events: PreviewTraceEvent[]): TraceTimelineItem[] {
  return events
    .filter((event) => event.type === "guardrail_complete" || event.type === "rag_complete")
    .map((event, index) => ({
      id: `${event.type}-${event.at}-${index}`,
      turnId: "",
      kind: "llm" as const,
      label: "LLM Request",
      detail: event.type,
      at: event.at,
    }));
}

function mapEvent(event: PreviewTraceEvent, turnId: string, index: number): TraceTimelineItem | null {
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
    case "output_message":
      return {
        id,
        turnId,
        kind: "output",
        label: "Output Message",
        detail: String(event.data.text ?? ""),
        at: event.at,
      };
    case "guardrail_complete":
    case "rag_complete":
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

export function buildTraceTimeline(turns: PreviewTraceTurn[]): TraceTimelineItem[] {
  const items: TraceTimelineItem[] = [];

  for (const turn of turns) {
    const llmEvents = turn.events.filter(
      (event) => event.type === "guardrail_complete" || event.type === "rag_complete",
    );

    turn.events.forEach((event, index) => {
      if (event.type === "guardrail_complete" && llmEvents[0] === event) {
        const nested = llmNested(llmEvents);
        if (nested.length > 0) {
          items.push({
            id: `${turn.turn_id}-llm-group`,
            turnId: turn.turn_id,
            kind: "llm",
            label: "LLM Request",
            at: event.at,
            nested,
          });
        }
        return;
      }
      if (event.type === "rag_complete") {
        return;
      }

      const mapped = mapEvent(event, turn.turn_id, index);
      if (mapped) {
        items.push(mapped);
      }
    });
  }

  return items;
}

export function formatTraceTimestamp(iso: string): string {
  return formatTime(iso);
}

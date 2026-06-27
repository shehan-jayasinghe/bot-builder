import type {
  PositionedRuntimeGraphNode,
  RuntimeGraphEdge,
  RuntimeGraphNode,
  RuntimeGraphResponse,
} from "../types/preview";

const NODE_WIDTH = 148;
const NODE_HEIGHT = 52;
const ORCHESTRATOR_SIZE = { width: 120, height: 56 };
const RADIUS = 220;
const CENTER = { x: 360, y: 300 };

const TYPE_ORDER: RuntimeGraphNode["type"][] = [
  "tool",
  "workflow",
  "sub_agent",
  "knowledge_base",
];

export function layoutRuntimeGraph(graph: RuntimeGraphResponse): {
  nodes: PositionedRuntimeGraphNode[];
  edges: RuntimeGraphEdge[];
} {
  const orchestratorId = graph.orchestrator.id;
  const children = graph.nodes.filter((node) => node.id !== orchestratorId);

  const grouped = TYPE_ORDER.map((type) => children.filter((node) => node.type === type));
  const flatChildren = grouped.flat();

  const positioned: PositionedRuntimeGraphNode[] = [];

  const orchestrator = graph.nodes.find((node) => node.id === orchestratorId);
  if (orchestrator) {
    positioned.push({
      ...orchestrator,
      position: {
        x: CENTER.x - ORCHESTRATOR_SIZE.width / 2,
        y: CENTER.y - ORCHESTRATOR_SIZE.height / 2,
      },
    });
  }

  const count = flatChildren.length;
  flatChildren.forEach((node, index) => {
    const angle = count === 1 ? -Math.PI / 2 : -Math.PI / 2 + (index / Math.max(count - 1, 1)) * Math.PI;
    const x = CENTER.x + Math.cos(angle) * RADIUS - NODE_WIDTH / 2;
    const y = CENTER.y + Math.sin(angle) * RADIUS - NODE_HEIGHT / 2;
    positioned.push({ ...node, position: { x, y } });
  });

  return { nodes: positioned, edges: graph.edges };
}

export function nodeDimensions(type: RuntimeGraphNode["type"]): { width: number; height: number } {
  if (type === "orchestrator") {
    return ORCHESTRATOR_SIZE;
  }
  return { width: NODE_WIDTH, height: NODE_HEIGHT };
}

export function resolveHighlightedNodeId(
  routing: Record<string, unknown> | null | undefined,
  orchestratorId: string,
): string | null {
  if (!routing) {
    return null;
  }

  if (routing.mode === "orchestrator") {
    return orchestratorId;
  }

  const type = routing.type;
  if (type === "tool" && typeof routing.tool_id === "string") {
    return routing.tool_id;
  }
  if (type === "sub_agent" && typeof routing.sub_agent_id === "string") {
    return routing.sub_agent_id;
  }
  if (type === "workflow" && typeof routing.workflow_id === "string") {
    return routing.workflow_id;
  }
  if (type === "knowledge_base" && typeof routing.knowledge_base_id === "string") {
    return routing.knowledge_base_id;
  }

  return orchestratorId;
}

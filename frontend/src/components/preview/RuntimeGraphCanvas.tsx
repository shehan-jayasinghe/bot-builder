import type { PositionedRuntimeGraphNode, RuntimeGraphEdge } from "../../types/preview";
import { nodeDimensions } from "../../utils/runtimeGraphLayout";

type RuntimeGraphCanvasProps = {
  nodes: PositionedRuntimeGraphNode[];
  edges: RuntimeGraphEdge[];
  highlightedNodeId?: string | null;
  zoom?: number;
  orchestratorMeta?: {
    status?: string | null;
    description?: string | null;
  };
};

function edgePath(
  source: PositionedRuntimeGraphNode,
  target: PositionedRuntimeGraphNode,
): string {
  const s = nodeDimensions(source.type);
  const t = nodeDimensions(target.type);
  const x1 = source.position.x + s.width / 2;
  const y1 = source.position.y + s.height / 2;
  const x2 = target.position.x + t.width / 2;
  const y2 = target.position.y + t.height / 2;
  const dx = Math.max(40, Math.abs(x2 - x1) * 0.45);
  const dy = Math.max(20, Math.abs(y2 - y1) * 0.25);
  return `M ${x1} ${y1} C ${x1 + dx} ${y1 - dy}, ${x2 - dx} ${y2 + dy}, ${x2} ${y2}`;
}

function nodeTypeLabel(type: PositionedRuntimeGraphNode["type"]): string {
  switch (type) {
    case "orchestrator":
      return "Agent";
    case "tool":
      return "Tool";
    case "workflow":
      return "Workflow";
    case "sub_agent":
      return "Sub-agent";
    case "knowledge_base":
      return "Knowledge";
    default:
      return type;
  }
}

export function RuntimeGraphCanvas({
  nodes,
  edges,
  highlightedNodeId,
  zoom = 1,
  orchestratorMeta,
}: RuntimeGraphCanvasProps) {
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));

  return (
    <div className="runtime-graph-canvas" style={{ transform: `scale(${zoom})` }}>
      <svg className="runtime-graph-canvas__edges" aria-hidden="true">
        {edges.map((edge) => {
          const source = nodeMap.get(edge.source);
          const target = nodeMap.get(edge.target);
          if (!source || !target) {
            return null;
          }
          const isActive =
            highlightedNodeId === edge.source || highlightedNodeId === edge.target;
          return (
            <path
              key={edge.id}
              d={edgePath(source, target)}
              className={`runtime-graph-canvas__edge ${isActive ? "runtime-graph-canvas__edge--active" : ""}`}
              fill="none"
            />
          );
        })}
      </svg>

      {nodes.map((node) => {
        const size = nodeDimensions(node.type);
        const isHighlighted = highlightedNodeId === node.id;
        const isOrchestrator = node.type === "orchestrator";

        return (
          <div
            key={node.id}
            className={[
              "runtime-graph-node",
              `runtime-graph-node--${node.type}`,
              isHighlighted && "runtime-graph-node--highlighted",
              isOrchestrator && "runtime-graph-node--orchestrator",
            ]
              .filter(Boolean)
              .join(" ")}
            style={{
              left: node.position.x,
              top: node.position.y,
              width: size.width,
              minHeight: size.height,
            }}
            title={node.description ?? undefined}
          >
            <span className="runtime-graph-node__type">{nodeTypeLabel(node.type)}</span>
            {isOrchestrator && orchestratorMeta?.status ? (
              <span className={`runtime-graph-node__status runtime-graph-node__status--${orchestratorMeta.status}`}>
                {orchestratorMeta.status}
              </span>
            ) : null}
            <span className="runtime-graph-node__label">{node.label}</span>
            {(isOrchestrator ? orchestratorMeta?.description : node.description) ? (
              <span className="runtime-graph-node__description">
                {isOrchestrator ? orchestratorMeta?.description : node.description}
              </span>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

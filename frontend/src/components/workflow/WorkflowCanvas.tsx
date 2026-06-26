import type { WorkflowEdge, WorkflowNode } from "../../types/workflow";

type WorkflowCanvasProps = {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  zoom: number;
  selectedNodeId?: string | null;
  onSelectNode?: (nodeId: string) => void;
};

const NODE_WIDTH: Record<string, number> = {
  start: 72,
  message: 132,
  default: 120,
};

const NODE_HEIGHT: Record<string, number> = {
  start: 36,
  message: 48,
  default: 44,
};

function nodeSize(type: string) {
  return {
    width: NODE_WIDTH[type] ?? NODE_WIDTH.default,
    height: NODE_HEIGHT[type] ?? NODE_HEIGHT.default,
  };
}

function nodeLabel(node: WorkflowNode): string {
  if (node.type === "start") {
    return "Start";
  }
  if (node.type === "message") {
    return String(node.data.text ?? "Message");
  }
  if (node.type === "action") {
    return String(node.data.label ?? node.data.action_type ?? "Action");
  }
  return String(node.data.label ?? node.type);
}

function edgePath(source: WorkflowNode, target: WorkflowNode): string {
  const s = nodeSize(source.type);
  const t = nodeSize(target.type);
  const x1 = source.position.x + s.width;
  const y1 = source.position.y + s.height / 2;
  const x2 = target.position.x;
  const y2 = target.position.y + t.height / 2;
  const dx = Math.max(48, (x2 - x1) * 0.5);
  return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
}

export function WorkflowCanvas({ nodes, edges, zoom, selectedNodeId, onSelectNode }: WorkflowCanvasProps) {
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));

  return (
    <div className="workflow-canvas" style={{ transform: `scale(${zoom})` }}>
      <svg className="workflow-canvas__edges" aria-hidden="true">
        {edges.map((edge) => {
          const source = nodeMap.get(edge.source);
          const target = nodeMap.get(edge.target);
          if (!source || !target) {
            return null;
          }
          return (
            <path
              key={edge.id}
              d={edgePath(source, target)}
              className="workflow-canvas__edge"
              fill="none"
            />
          );
        })}
      </svg>

      {nodes.map((node) => {
        const isStart = node.type === "start";
        const isMessage = node.type === "message";
        const isSelected = selectedNodeId === node.id;

        return (
          <button
            key={node.id}
            type="button"
            className={[
              "workflow-node",
              isStart && "workflow-node--start",
              isMessage && "workflow-node--message",
              !isStart && !isMessage && "workflow-node--step",
              isSelected && "workflow-node--selected",
            ]
              .filter(Boolean)
              .join(" ")}
            style={{ left: node.position.x, top: node.position.y }}
            onClick={() => onSelectNode?.(node.id)}
          >
            <span className="workflow-node__label">{nodeLabel(node)}</span>
            {!isStart ? <span className="workflow-node__port" aria-hidden="true" /> : null}
          </button>
        );
      })}
    </div>
  );
}

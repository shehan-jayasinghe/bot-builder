import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getWorkflow, updateWorkflow } from "../../api/workflows";
import { WorkflowCanvas } from "../../components/workflow/WorkflowCanvas";
import { WorkflowIcon } from "../../components/workflow/WorkflowIcon";
import { WORKFLOW_ACTION_ITEMS, WORKFLOW_TOOLBAR_ITEMS } from "../../constants/workflows";
import type { WorkflowEdge, WorkflowNode } from "../../types/workflow";
import { getApiError } from "../../utils/apiError";

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) {
    return "just now";
  }
  if (mins < 60) {
    return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  }
  const hours = Math.floor(mins / 60);
  if (hours < 24) {
    return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function getTailNode(nodes: WorkflowNode[], edges: WorkflowEdge[]): WorkflowNode | undefined {
  const outgoing = new Map(edges.map((edge) => [edge.source, edge.target]));
  let current = nodes.find((node) => node.type === "start") ?? nodes[0];
  if (!current) {
    return undefined;
  }

  while (outgoing.has(current.id)) {
    const nextId = outgoing.get(current.id);
    const next = nodes.find((node) => node.id === nextId);
    if (!next) {
      break;
    }
    current = next;
  }

  return current;
}

function defaultNodeData(type: string, label?: string): Record<string, unknown> {
  if (type === "message") {
    return { text: label ?? "Message" };
  }
  if (type === "action") {
    return { label: label ?? "Action", action_type: label?.toLowerCase().replace(/\s+/g, "_") ?? "action" };
  }
  return { label: label ?? type };
}

export function WorkflowEditorPage() {
  const { workflowId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const actionsRef = useRef<HTMLDivElement>(null);

  const [name, setName] = useState("");
  const [nodes, setNodes] = useState<WorkflowNode[]>([]);
  const [edges, setEdges] = useState<WorkflowEdge[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [actionsOpen, setActionsOpen] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);

  const workflowQuery = useQuery({
    queryKey: ["workflow", workflowId],
    queryFn: () => getWorkflow(workflowId),
    enabled: Boolean(workflowId),
  });

  useEffect(() => {
    if (!workflowQuery.data) {
      return;
    }
    setName(workflowQuery.data.name);
    setNodes(workflowQuery.data.nodes);
    setEdges(workflowQuery.data.edges);
    setDirty(false);
    setSaveError(null);
  }, [workflowQuery.data]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (actionsRef.current && !actionsRef.current.contains(event.target as HTMLElement)) {
        setActionsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const saveMutation = useMutation({
    mutationFn: () =>
      updateWorkflow(workflowId, {
        name: name.trim() || "Welcome",
        nodes,
        edges,
      }),
    onSuccess: (workflow) => {
      queryClient.setQueryData(["workflow", workflowId], workflow);
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      setDirty(false);
      setSaveError(null);
    },
    onError: (error) => setSaveError(getApiError(error)),
  });

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId],
  );

  function markDirty() {
    setDirty(true);
    setSaveError(null);
  }

  function addNode(type: string, label?: string, actionType?: string) {
    const tail = getTailNode(nodes, edges);
    const id = `${type}-${Date.now()}`;
    const position = {
      x: (tail?.position.x ?? 80) + 180,
      y: tail?.position.y ?? 220,
    };

    const data =
      type === "action" && actionType
        ? { label: label ?? "Action", action_type: actionType }
        : defaultNodeData(type, label);

    const nextNode: WorkflowNode = { id, type, position, data };
    const nextNodes = [...nodes, nextNode];
    const nextEdges = tail
      ? [...edges, { id: `edge-${id}`, source: tail.id, target: id }]
      : edges;

    setNodes(nextNodes);
    setEdges(nextEdges);
    setSelectedNodeId(id);
    markDirty();
    setActionsOpen(false);
  }

  function updateSelectedNodeData(patch: Record<string, unknown>) {
    if (!selectedNodeId) {
      return;
    }
    setNodes((current) =>
      current.map((node) =>
        node.id === selectedNodeId ? { ...node, data: { ...node.data, ...patch } } : node,
      ),
    );
    markDirty();
  }

  if (!workflowId) {
    return null;
  }

  if (workflowQuery.isLoading) {
    return <div className="workflow-editor workflow-editor--loading">Loading workflow…</div>;
  }

  if (workflowQuery.isError) {
    return (
      <div className="workflow-editor workflow-editor--error">
        <p>{getApiError(workflowQuery.error)}</p>
        <button type="button" className="workflow-editor__btn" onClick={() => navigate("/workflows")}>
          Back to workflows
        </button>
      </div>
    );
  }

  const workflow = workflowQuery.data!;

  return (
    <div className="workflow-editor">
      <div className="workflow-editor__topbar">
        <input
          className="workflow-editor__title"
          value={name}
          onChange={(event) => {
            setName(event.target.value);
            markDirty();
          }}
          aria-label="Workflow name"
        />
        <div className="workflow-editor__topbar-actions">
          <button type="button" className="workflow-editor__btn workflow-editor__btn--ghost" disabled>
            Preview
          </button>
          <button type="button" className="workflow-editor__btn workflow-editor__btn--primary" disabled>
            Publish
          </button>
        </div>
      </div>

      <div className="workflow-editor__toolbar">
        <div className="workflow-editor__palette">
          {WORKFLOW_TOOLBAR_ITEMS.map((item) =>
            item.id === "actions" ? (
              <div key={item.id} className="workflow-editor__palette-item-wrap" ref={actionsRef}>
                <button
                  type="button"
                  className={["workflow-editor__palette-item", actionsOpen && "workflow-editor__palette-item--active"]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => setActionsOpen((open) => !open)}
                  title={item.label}
                >
                  <WorkflowIcon name={item.id} />
                  <span>{item.label}</span>
                </button>
                {actionsOpen ? (
                  <div className="workflow-editor__actions-menu">
                    {WORKFLOW_ACTION_ITEMS.map((action) => (
                      <button
                        key={action.id}
                        type="button"
                        className="workflow-editor__actions-item"
                        onClick={() => addNode("action", action.label, action.actionType)}
                      >
                        <WorkflowIcon name={`action-${action.id.replace(/_/g, "-")}`} />
                        <span>{action.label}</span>
                      </button>
                    ))}
                    <p className="workflow-editor__actions-hint">Click to add a step to the canvas.</p>
                  </div>
                ) : null}
              </div>
            ) : (
              <button
                key={item.id}
                type="button"
                className="workflow-editor__palette-item"
                title={item.label}
                onClick={() => item.nodeType && addNode(item.nodeType, item.label)}
              >
                <WorkflowIcon name={item.id} />
                <span>{item.label}</span>
              </button>
            ),
          )}
        </div>

        <div className="workflow-editor__toolbar-right">
          {saveError ? <span className="workflow-editor__save-error">{saveError}</span> : null}
          <button
            type="button"
            className="workflow-editor__palette-item workflow-editor__palette-item--save"
            title="Save"
            disabled={!dirty || saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            <WorkflowIcon name="save" />
            <span>{saveMutation.isPending ? "Saving…" : "Save"}</span>
          </button>
        </div>
      </div>

      <div className="workflow-editor__body">
        <WorkflowCanvas
          nodes={nodes}
          edges={edges}
          zoom={zoom}
          selectedNodeId={selectedNodeId}
          onSelectNode={setSelectedNodeId}
        />

        {selectedNode && (selectedNode.type === "message" || selectedNode.type === "action") ? (
          <aside className="workflow-editor__inspector">
            <h3>Step settings</h3>
            {selectedNode.type === "message" ? (
              <label className="workflow-editor__field">
                <span>Message</span>
                <input
                  value={String(selectedNode.data.text ?? "")}
                  onChange={(event) => updateSelectedNodeData({ text: event.target.value })}
                />
              </label>
            ) : (
              <p className="workflow-editor__inspector-meta">
                Action type: <strong>{String(selectedNode.data.action_type ?? "")}</strong>
              </p>
            )}
          </aside>
        ) : null}
      </div>

      <div className="workflow-editor__footer">
        <div className="workflow-editor__zoom">
          <button type="button" aria-label="Zoom in" onClick={() => setZoom((z) => Math.min(1.5, z + 0.1))}>
            +
          </button>
          <button type="button" aria-label="Zoom out" onClick={() => setZoom((z) => Math.max(0.6, z - 0.1))}>
            −
          </button>
          <button type="button" aria-label="Reset zoom" onClick={() => setZoom(1)}>
            ⊡
          </button>
        </div>
        <span className="workflow-editor__modified">Last modified {formatRelativeTime(workflow.updated_at)}</span>
      </div>
    </div>
  );
}

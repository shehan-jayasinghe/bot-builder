import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { listKnowledgebasesByAgent } from "../../api/knowledgebases";
import { createSubAgent } from "../../api/subAgents";
import { listToolsByAgent } from "../../api/tools";
import { listWorkflows } from "../../api/workflows";
import type { CreateSubAgentPayload } from "../../types/subAgent";
import { getApiError } from "../../utils/apiError";
import { RoutingHintField } from "./RoutingHintField";

const NONE = "";

type CreateSubAgentModalProps = {
  agentId: string;
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
};

function isSnakeCaseName(value: string): boolean {
  return /^[a-z][a-z0-9_]*$/.test(value);
}

export function CreateSubAgentModal({ agentId, open, onClose, onSuccess }: CreateSubAgentModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [instructions, setInstructions] = useState("");
  const [toolId, setToolId] = useState(NONE);
  const [knowledgeBaseId, setKnowledgeBaseId] = useState(NONE);
  const [workflowId, setWorkflowId] = useState(NONE);
  const [routingHint, setRoutingHint] = useState("");

  const toolsQuery = useQuery({
    queryKey: ["tools", "agent", agentId],
    queryFn: () => listToolsByAgent(agentId),
    enabled: open,
  });

  const knowledgebasesQuery = useQuery({
    queryKey: ["knowledgebases", "agent", agentId],
    queryFn: () => listKnowledgebasesByAgent(agentId),
    enabled: open,
  });

  const workflowsQuery = useQuery({
    queryKey: ["workflows", "agent", agentId],
    queryFn: () => listWorkflows({ agent_id: agentId }),
    enabled: open,
  });

  const createMutation = useMutation({
    mutationFn: (payload: CreateSubAgentPayload) => createSubAgent(agentId, payload),
    onSuccess: () => {
      onSuccess();
      onClose();
    },
  });

  useEffect(() => {
    if (!open) {
      setName("");
      setDescription("");
      setInstructions("");
      setToolId(NONE);
      setKnowledgeBaseId(NONE);
      setWorkflowId(NONE);
      setRoutingHint("");
      createMutation.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reset when modal opens/closes only
  }, [open]);

  if (!open) {
    return null;
  }

  const tools = toolsQuery.data?.items ?? [];
  const knowledgebases = knowledgebasesQuery.data?.items ?? [];
  const workflows = workflowsQuery.data?.items ?? [];

  const nameValid = isSnakeCaseName(name.trim());
  const instructionsValid = instructions.trim().length >= 20;
  const canSubmit = nameValid && instructionsValid && !createMutation.isPending;

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    createMutation.mutate({
      name: name.trim(),
      description: description.trim() || null,
      instructions: instructions.trim(),
      tool_ids: toolId ? [toolId] : [],
      knowledge_base_ids: knowledgeBaseId ? [knowledgeBaseId] : [],
      workflow_ids: workflowId ? [workflowId] : [],
      parameters: [],
      routing_hint: routingHint.trim() || null,
    });
  }

  return (
    <div className="modal-overlay" role="presentation" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-labelledby="create-sub-agent-title"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal__header">
          <div>
            <h2 id="create-sub-agent-title">Add sub agent</h2>
            <p className="modal__subtitle">A specialist the main agent can delegate to.</p>
          </div>
          <button type="button" className="modal__close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <form className="modal__body" onSubmit={handleSubmit}>
          {createMutation.isError ? (
            <p className="agent-panel__error">{getApiError(createMutation.error)}</p>
          ) : null}

          <label className="agent-detail__field">
            <span>Sub agent name</span>
            <input
              className="agent-panel__input"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="research_agent"
              autoFocus
            />
            <span className="agent-detail__field-hint">
              Use snake_case (letters, numbers, underscores). Example: billing_helper
            </span>
            {name.trim() && !nameValid ? (
              <span className="agent-detail__field-error">Name must be snake_case.</span>
            ) : null}
          </label>

          <label className="agent-detail__field">
            <span>Description</span>
            <textarea
              className="agent-panel__textarea"
              rows={2}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Short summary for the builder UI."
            />
          </label>

          <RoutingHintField
            capabilityKind="sub_agent"
            value={routingHint}
            onChange={setRoutingHint}
          />

          <label className="agent-detail__field">
            <span>Instructions</span>
            <textarea
              className="agent-panel__textarea"
              rows={5}
              value={instructions}
              onChange={(event) => setInstructions(event.target.value)}
              placeholder="You are a research assistant. Answer using attached tools and knowledge bases only."
            />
            <span className="agent-detail__field-hint">
              Sub agent prompt — minimum 20 characters ({instructions.trim().length}/20)
            </span>
          </label>

          <label className="agent-detail__field">
            <span>Tool</span>
            <select
              className="agent-panel__input"
              value={toolId}
              onChange={(event) => setToolId(event.target.value)}
              disabled={toolsQuery.isLoading}
            >
              <option value={NONE}>None</option>
              {tools.map((tool) => (
                <option key={tool.id} value={tool.id}>
                  {tool.name}
                </option>
              ))}
            </select>
            {!toolsQuery.isLoading && tools.length === 0 ? (
              <span className="agent-detail__field-hint">Attach a tool to this agent first.</span>
            ) : null}
          </label>

          <label className="agent-detail__field">
            <span>Knowledge base</span>
            <select
              className="agent-panel__input"
              value={knowledgeBaseId}
              onChange={(event) => setKnowledgeBaseId(event.target.value)}
              disabled={knowledgebasesQuery.isLoading}
            >
              <option value={NONE}>None</option>
              {knowledgebases.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            {!knowledgebasesQuery.isLoading && knowledgebases.length === 0 ? (
              <span className="agent-detail__field-hint">Attach a knowledge base to this agent first.</span>
            ) : null}
          </label>

          <label className="agent-detail__field">
            <span>Workflow</span>
            <select
              className="agent-panel__input"
              value={workflowId}
              onChange={(event) => setWorkflowId(event.target.value)}
              disabled={workflowsQuery.isLoading}
            >
              <option value={NONE}>None</option>
              {workflows.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            {!workflowsQuery.isLoading && workflows.length === 0 ? (
              <span className="agent-detail__field-hint">Attach a workflow to this agent first.</span>
            ) : null}
          </label>

          <div className="modal__footer">
            <button type="button" className="btn btn--ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn--primary" disabled={!canSubmit}>
              {createMutation.isPending ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

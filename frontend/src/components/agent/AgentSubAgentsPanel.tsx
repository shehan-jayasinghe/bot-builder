import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { listSubAgents } from "../../api/subAgents";
import { getApiError } from "../../utils/apiError";
import { CreateSubAgentModal } from "./CreateSubAgentModal";

const MAX_SUB_AGENTS = 10;

type AgentSubAgentsPanelProps = {
  agentId: string;
};

function formatSkillSummary(item: {
  tool_count: number;
  knowledge_base_count: number;
  workflow_count: number;
}): string {
  const parts: string[] = [];
  if (item.tool_count > 0) {
    parts.push(`${item.tool_count} tool${item.tool_count === 1 ? "" : "s"}`);
  }
  if (item.knowledge_base_count > 0) {
    parts.push(`${item.knowledge_base_count} KB${item.knowledge_base_count === 1 ? "" : "s"}`);
  }
  if (item.workflow_count > 0) {
    parts.push(`${item.workflow_count} workflow${item.workflow_count === 1 ? "" : "s"}`);
  }
  return parts.length > 0 ? parts.join(" · ") : "No skills attached";
}

export function AgentSubAgentsPanel({ agentId }: AgentSubAgentsPanelProps) {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["sub-agents", agentId],
    queryFn: () => listSubAgents(agentId),
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const atLimit = total >= MAX_SUB_AGENTS;
  const isEmpty = !isLoading && items.length === 0;

  function handleCreated() {
    queryClient.invalidateQueries({ queryKey: ["sub-agents", agentId] });
    queryClient.invalidateQueries({ queryKey: ["capability-catalog-preview", agentId] });
  }

  return (
    <>
      <section className="agent-panel agent-panel--grow">
        <div className="agent-panel__header agent-panel__header--row">
          <div>
            <h2>Sub agents</h2>
            <span className="agent-panel__hint">
              Delegatable specialists for this agent ({total}/{MAX_SUB_AGENTS})
            </span>
          </div>
          <button
            type="button"
            className="agent-detail__link-btn"
            disabled={atLimit}
            onClick={() => setModalOpen(true)}
          >
            + Add sub agent
          </button>
        </div>

        {isLoading ? (
          <p className="agent-kb-panel__loading">Loading sub agents…</p>
        ) : isError ? (
          <p className="agent-panel__error">{getApiError(error)}</p>
        ) : isEmpty ? (
          <div className="agent-detail__empty-panel">
            <div className="agent-detail__empty-icon" aria-hidden>
              🤖
            </div>
            <p>No sub agents yet.</p>
            <span>Create a specialist with its own prompt and optional tool, knowledge base, or workflow.</span>
            <button type="button" className="btn btn--ghost" onClick={() => setModalOpen(true)}>
              Add sub agent
            </button>
          </div>
        ) : (
          <ul className="agent-kb-list">
            {items.map((item) => (
              <li key={item.id} className="agent-kb-list__item">
                <div className="agent-kb-list__main">
                  <strong>{item.name}</strong>
                  {item.description ? (
                    <span className="agent-kb-list__meta">{item.description}</span>
                  ) : (
                    <span className="agent-kb-list__meta">{formatSkillSummary(item)}</span>
                  )}
                  {item.routing_hint ? (
                    <span className="agent-kb-list__meta agent-kb-list__hint">{item.routing_hint}</span>
                  ) : null}
                </div>
                <div className="agent-kb-list__actions">
                  <span className="agent-kb-list__meta">{formatSkillSummary(item)}</span>
                  <span className={`agent-status agent-status--${item.status}`}>{item.status}</span>
                </div>
              </li>
            ))}
          </ul>
        )}

        {atLimit ? (
          <p className="agent-panel__hint agent-sub-agents__limit-hint">
            Maximum of {MAX_SUB_AGENTS} sub agents per agent.
          </p>
        ) : null}
      </section>

      <CreateSubAgentModal
        agentId={agentId}
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={handleCreated}
      />
    </>
  );
}

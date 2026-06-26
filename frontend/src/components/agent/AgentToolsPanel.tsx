import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listTools, updateTool } from "../../api/tools";
import { getApiError } from "../../utils/apiError";
import { AttachDetachButton } from "./AttachDetachButton";

type AgentToolsPanelProps = {
  agentId: string;
};

function formatExecutorName(executor: string): string {
  return executor.replace(/_/g, " ");
}

export function AgentToolsPanel({ agentId }: AgentToolsPanelProps) {
  const queryClient = useQueryClient();
  const addPath = `/agent/${agentId}/tools/new`;

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["tools", "org"],
    queryFn: () => listTools(),
  });

  const attachMutation = useMutation({
    mutationFn: ({ toolId, attach }: { toolId: string; attach: boolean }) =>
      updateTool(toolId, { agent_id: attach ? agentId : null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tools"] });
    },
  });

  const items = data?.items ?? [];
  const isEmpty = !isLoading && items.length === 0;
  const pendingId = attachMutation.isPending ? attachMutation.variables?.toolId : null;

  return (
    <section className="agent-panel">
      <div className="agent-panel__header agent-panel__header--row">
        <h2>Tools</h2>
        <Link to={addPath} className="agent-detail__link-btn">
          + Add
        </Link>
      </div>

      {attachMutation.isError ? (
        <p className="agent-panel__error">{getApiError(attachMutation.error)}</p>
      ) : null}

      {isLoading ? (
        <p className="agent-kb-panel__loading">Loading tools…</p>
      ) : isError ? (
        <p className="agent-panel__error">{getApiError(error)}</p>
      ) : isEmpty ? (
        <div className="agent-detail__empty-panel">
          <div className="agent-detail__empty-icon" aria-hidden>
            🔧
          </div>
          <p>No tools yet.</p>
          <span>Create a tool, then attach it to this agent.</span>
          <Link to={addPath} className="btn btn--ghost">
            Add tool
          </Link>
        </div>
      ) : (
        <ul className="agent-kb-list">
          {items.map((item) => {
            const attached = item.agent_id === agentId;

            return (
              <li key={item.id} className="agent-kb-list__item">
                <div className="agent-kb-list__main">
                  <strong>{item.name}</strong>
                  <span className="agent-kb-list__meta">{formatExecutorName(item.executor)}</span>
                </div>
                <div className="agent-kb-list__actions">
                  <span className={`agent-status agent-status--${item.status}`}>{item.status}</span>
                  <AttachDetachButton
                    attached={attached}
                    disabled={pendingId === item.id}
                    onAttach={() => attachMutation.mutate({ toolId: item.id, attach: true })}
                    onDetach={() => attachMutation.mutate({ toolId: item.id, attach: false })}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

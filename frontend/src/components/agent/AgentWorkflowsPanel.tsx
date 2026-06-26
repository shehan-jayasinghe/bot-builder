import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listWorkflows, updateWorkflow } from "../../api/workflows";
import { getApiError } from "../../utils/apiError";
import { AttachDetachButton } from "./AttachDetachButton";

type AgentWorkflowsPanelProps = {
  agentId: string;
};

export function AgentWorkflowsPanel({ agentId }: AgentWorkflowsPanelProps) {
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["workflows", "org"],
    queryFn: () => listWorkflows(),
  });

  const attachMutation = useMutation({
    mutationFn: ({ workflowId, attach }: { workflowId: string; attach: boolean }) =>
      updateWorkflow(workflowId, { agent_id: attach ? agentId : null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
    },
  });

  const items = data?.items ?? [];
  const isEmpty = !isLoading && items.length === 0;
  const pendingId = attachMutation.isPending ? attachMutation.variables?.workflowId : null;

  return (
    <section className="agent-panel">
      <div className="agent-panel__header agent-panel__header--row">
        <h2>Workflows</h2>
        <Link to="/workflows" className="agent-detail__link-btn">
          + Add
        </Link>
      </div>

      {attachMutation.isError ? (
        <p className="agent-panel__error">{getApiError(attachMutation.error)}</p>
      ) : null}

      {isLoading ? (
        <p className="agent-kb-panel__loading">Loading workflows…</p>
      ) : isError ? (
        <p className="agent-panel__error">{getApiError(error)}</p>
      ) : isEmpty ? (
        <div className="agent-detail__empty-panel">
          <div className="agent-detail__empty-icon" aria-hidden>
            ↗
          </div>
          <p>No workflows yet.</p>
          <span>Create a workflow in the sidebar, then attach it here.</span>
          <Link to="/workflows" className="btn btn--ghost">
            Open workflows
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
                  <span className="agent-kb-list__meta">
                    {item.node_count} step{item.node_count === 1 ? "" : "s"} · {item.status}
                  </span>
                </div>
                <div className="agent-kb-list__actions">
                  <AttachDetachButton
                    attached={attached}
                    disabled={pendingId === item.id}
                    onAttach={() => attachMutation.mutate({ workflowId: item.id, attach: true })}
                    onDetach={() => attachMutation.mutate({ workflowId: item.id, attach: false })}
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

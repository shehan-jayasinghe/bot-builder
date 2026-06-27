import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { listWorkflows, updateWorkflow } from "../../api/workflows";
import { getApiError } from "../../utils/apiError";
import { AttachDetachButton } from "./AttachDetachButton";
import { RoutingHintModal } from "./RoutingHintModal";

type AgentWorkflowsPanelProps = {
  agentId: string;
};

type AttachTarget = {
  id: string;
  name: string;
};

export function AgentWorkflowsPanel({ agentId }: AgentWorkflowsPanelProps) {
  const queryClient = useQueryClient();
  const [attachTarget, setAttachTarget] = useState<AttachTarget | null>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["workflows", "org"],
    queryFn: () => listWorkflows(),
  });

  const attachMutation = useMutation({
    mutationFn: ({
      workflowId,
      attach,
      routingHint,
    }: {
      workflowId: string;
      attach: boolean;
      routingHint?: string | null;
    }) =>
      updateWorkflow(workflowId, {
        agent_id: attach ? agentId : null,
        ...(attach ? { routing_hint: routingHint ?? null } : {}),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      setAttachTarget(null);
    },
  });

  const items = data?.items ?? [];
  const isEmpty = !isLoading && items.length === 0;
  const pendingId = attachMutation.isPending ? attachMutation.variables?.workflowId : null;

  function handleAttachConfirm(routingHint: string | null) {
    if (!attachTarget) {
      return;
    }
    attachMutation.mutate({
      workflowId: attachTarget.id,
      attach: true,
      routingHint,
    });
  }

  return (
    <>
      <section className="agent-panel">
        <div className="agent-panel__header agent-panel__header--row">
          <h2>Workflows</h2>
          <Link to="/workflows" className="agent-detail__link-btn">
            + Add
          </Link>
        </div>

        {attachMutation.isError && !attachTarget ? (
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
                    {attached && item.routing_hint ? (
                      <span className="agent-kb-list__meta agent-kb-list__hint">{item.routing_hint}</span>
                    ) : null}
                  </div>
                  <div className="agent-kb-list__actions">
                    <AttachDetachButton
                      attached={attached}
                      disabled={pendingId === item.id}
                      onAttach={() => setAttachTarget({ id: item.id, name: item.name })}
                      onDetach={() => attachMutation.mutate({ workflowId: item.id, attach: false })}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <RoutingHintModal
        open={attachTarget !== null}
        capabilityKind="workflow"
        resourceName={attachTarget?.name ?? ""}
        submitting={attachMutation.isPending}
        error={attachTarget && attachMutation.isError ? getApiError(attachMutation.error) : null}
        onClose={() => {
          if (!attachMutation.isPending) {
            setAttachTarget(null);
            attachMutation.reset();
          }
        }}
        onConfirm={handleAttachConfirm}
      />
    </>
  );
}

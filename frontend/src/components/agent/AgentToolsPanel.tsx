import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { listTools, updateTool } from "../../api/tools";
import { getApiError } from "../../utils/apiError";
import { AttachDetachButton } from "./AttachDetachButton";
import { RoutingHintModal } from "./RoutingHintModal";

type AgentToolsPanelProps = {
  agentId: string;
};

type AttachTarget = {
  id: string;
  name: string;
};

function formatExecutorName(executor: string): string {
  return executor.replace(/_/g, " ");
}

export function AgentToolsPanel({ agentId }: AgentToolsPanelProps) {
  const queryClient = useQueryClient();
  const addPath = `/agent/${agentId}/tools/new`;
  const [attachTarget, setAttachTarget] = useState<AttachTarget | null>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["tools", "org"],
    queryFn: () => listTools(),
  });

  const attachMutation = useMutation({
    mutationFn: ({
      toolId,
      attach,
      routingHint,
    }: {
      toolId: string;
      attach: boolean;
      routingHint?: string | null;
    }) =>
      updateTool(toolId, {
        agent_id: attach ? agentId : null,
        ...(attach ? { routing_hint: routingHint ?? null } : {}),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tools"] });
      setAttachTarget(null);
    },
  });

  const items = data?.items ?? [];
  const isEmpty = !isLoading && items.length === 0;
  const pendingId = attachMutation.isPending ? attachMutation.variables?.toolId : null;

  function handleAttachConfirm(routingHint: string | null) {
    if (!attachTarget) {
      return;
    }
    attachMutation.mutate({
      toolId: attachTarget.id,
      attach: true,
      routingHint,
    });
  }

  return (
    <>
      <section className="agent-panel">
        <div className="agent-panel__header agent-panel__header--row">
          <h2>Tools</h2>
          <Link to={addPath} className="agent-detail__link-btn">
            + Add
          </Link>
        </div>

        {attachMutation.isError && !attachTarget ? (
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
                    {attached && item.routing_hint ? (
                      <span className="agent-kb-list__meta agent-kb-list__hint">{item.routing_hint}</span>
                    ) : null}
                  </div>
                  <div className="agent-kb-list__actions">
                    <span className={`agent-status agent-status--${item.status}`}>{item.status}</span>
                    <AttachDetachButton
                      attached={attached}
                      disabled={pendingId === item.id}
                      onAttach={() => setAttachTarget({ id: item.id, name: item.name })}
                      onDetach={() => attachMutation.mutate({ toolId: item.id, attach: false })}
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
        capabilityKind="tool"
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

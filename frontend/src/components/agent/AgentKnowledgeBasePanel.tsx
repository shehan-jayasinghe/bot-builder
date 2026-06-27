import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { listKnowledgebases, updateKnowledgebase } from "../../api/knowledgebases";
import { getApiError } from "../../utils/apiError";
import { AttachDetachButton } from "./AttachDetachButton";
import { RoutingHintModal } from "./RoutingHintModal";

type AgentKnowledgeBasePanelProps = {
  agentId: string;
};

type AttachTarget = {
  id: string;
  name: string;
};

export function AgentKnowledgeBasePanel({ agentId }: AgentKnowledgeBasePanelProps) {
  const queryClient = useQueryClient();
  const addPath = `/agent/${agentId}/knowledgebases/new`;
  const [attachTarget, setAttachTarget] = useState<AttachTarget | null>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["knowledgebases", "org"],
    queryFn: () => listKnowledgebases(),
  });

  const attachMutation = useMutation({
    mutationFn: ({
      knowledgebaseId,
      attach,
      routingHint,
    }: {
      knowledgebaseId: string;
      attach: boolean;
      routingHint?: string | null;
    }) =>
      updateKnowledgebase(knowledgebaseId, {
        agent_id: attach ? agentId : null,
        ...(attach ? { routing_hint: routingHint ?? null } : {}),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledgebases"] });
      setAttachTarget(null);
    },
  });

  const items = data?.items ?? [];
  const isEmpty = !isLoading && items.length === 0;
  const pendingId = attachMutation.isPending ? attachMutation.variables?.knowledgebaseId : null;

  function handleAttachConfirm(routingHint: string | null) {
    if (!attachTarget) {
      return;
    }
    attachMutation.mutate({
      knowledgebaseId: attachTarget.id,
      attach: true,
      routingHint,
    });
  }

  return (
    <>
      <section className="agent-panel">
        <div className="agent-panel__header agent-panel__header--row">
          <h2>Knowledge base</h2>
          <Link to={addPath} className="agent-detail__link-btn">
            + Add
          </Link>
        </div>

        {attachMutation.isError && !attachTarget ? (
          <p className="agent-panel__error">{getApiError(attachMutation.error)}</p>
        ) : null}

        {isLoading ? (
          <p className="agent-kb-panel__loading">Loading knowledge bases…</p>
        ) : isError ? (
          <p className="agent-panel__error">{getApiError(error)}</p>
        ) : isEmpty ? (
          <div className="agent-detail__empty-panel">
            <div className="agent-detail__empty-icon" aria-hidden>
              📚
            </div>
            <p>No knowledge bases yet.</p>
            <span>Add a knowledge base, then attach it to this agent.</span>
            <Link to={addPath} className="btn btn--ghost">
              Add knowledge base
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
                      {item.storage_type} · {item.source_type}
                    </span>
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
                      onDetach={() => attachMutation.mutate({ knowledgebaseId: item.id, attach: false })}
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
        capabilityKind="knowledgebase"
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

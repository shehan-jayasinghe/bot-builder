import { useQuery } from "@tanstack/react-query";

import { getCapabilityCatalogPreview } from "../../api/agents";
import { getApiError } from "../../utils/apiError";

type CapabilityCatalogPanelProps = {
  agentId: string;
};

export function CapabilityCatalogPanel({ agentId }: CapabilityCatalogPanelProps) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["capability-catalog-preview", agentId],
    queryFn: () => getCapabilityCatalogPreview(agentId),
  });

  return (
    <section className="agent-panel agent-panel--catalog">
      <div className="agent-panel__header">
        <h2>Navigation catalog</h2>
        <span className="agent-panel__hint">Added to the prompt at chat time</span>
      </div>

      {isLoading ? (
        <p className="agent-kb-panel__loading">Loading navigation rules…</p>
      ) : isError ? (
        <p className="agent-panel__error">{getApiError(error)}</p>
      ) : data?.has_capabilities ? (
        <div className="agent-panel__scroll">
          <pre className="agent-catalog-preview">{data.text}</pre>
        </div>
      ) : (
        <div className="agent-detail__empty-panel agent-detail__empty-panel--compact">
          <p>No attached capabilities yet.</p>
          <span>Attach tools, workflows, or knowledge bases below — routing hints appear here.</span>
        </div>
      )}
    </section>
  );
}

import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listToolsByAgent } from "../../api/tools";

type AgentToolsPanelProps = {
  agentId: string;
};

function formatExecutorName(executor: string): string {
  return executor.replace(/_/g, " ");
}

export function AgentToolsPanel({ agentId }: AgentToolsPanelProps) {
  const addPath = `/agent/${agentId}/tools/new`;

  const { data, isLoading } = useQuery({
    queryKey: ["tools", agentId],
    queryFn: () => listToolsByAgent(agentId),
  });

  const items = data?.items ?? [];
  const isEmpty = !isLoading && items.length === 0;

  return (
    <section className="agent-panel">
      <div className="agent-panel__header agent-panel__header--row">
        <h2>Tools</h2>
        <Link to={addPath} className="agent-detail__link-btn">
          + Add
        </Link>
      </div>

      {isLoading ? (
        <p className="agent-kb-panel__loading">Loading tools…</p>
      ) : isEmpty ? (
        <div className="agent-detail__empty-panel">
          <div className="agent-detail__empty-icon" aria-hidden>
            🔧
          </div>
          <p>No tools connected yet.</p>
          <span>Add APIs, CRMs, or custom actions to extend your agent.</span>
          <Link to={addPath} className="btn btn--ghost">
            Add tool
          </Link>
        </div>
      ) : (
        <ul className="agent-kb-list">
          {items.map((item) => (
            <li key={item.id} className="agent-kb-list__item">
              <div className="agent-kb-list__main">
                <strong>{item.name}</strong>
                <span className="agent-kb-list__meta">{formatExecutorName(item.executor)}</span>
              </div>
              <span className={`agent-status agent-status--${item.status}`}>{item.status}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

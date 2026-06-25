import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listKnowledgebasesByAgent } from "../../api/knowledgebases";

type AgentKnowledgeBasePanelProps = {
  agentId: string;
};

export function AgentKnowledgeBasePanel({ agentId }: AgentKnowledgeBasePanelProps) {
  const addPath = `/agent/${agentId}/knowledgebases/new`;

  const { data, isLoading } = useQuery({
    queryKey: ["knowledgebases", agentId],
    queryFn: () => listKnowledgebasesByAgent(agentId),
  });

  const items = data?.items ?? [];
  const isEmpty = !isLoading && items.length === 0;

  return (
    <section className="agent-panel">
      <div className="agent-panel__header agent-panel__header--row">
        <h2>Knowledge base</h2>
        <Link to={addPath} className="agent-detail__link-btn">
          + Add
        </Link>
      </div>

      {isLoading ? (
        <p className="agent-kb-panel__loading">Loading knowledge bases…</p>
      ) : isEmpty ? (
        <div className="agent-detail__empty-panel">
          <div className="agent-detail__empty-icon" aria-hidden>
            📚
          </div>
          <p>No knowledge base connected yet.</p>
          <span>Add a website or document index for vector, keyword, or graph search.</span>
          <Link to={addPath} className="btn btn--ghost">
            Add knowledge base
          </Link>
        </div>
      ) : (
        <ul className="agent-kb-list">
          {items.map((item) => (
            <li key={item.id} className="agent-kb-list__item">
              <div className="agent-kb-list__main">
                <strong>{item.name}</strong>
                <span className="agent-kb-list__meta">
                  {item.storage_type} · {item.source_type}
                </span>
              </div>
              <span className={`agent-status agent-status--${item.status}`}>{item.status}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

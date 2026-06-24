import { useNavigate } from "react-router-dom";

import { AgentList } from "../../components/agent/AgentList";

export function AgentListPage() {
  const navigate = useNavigate();

  return (
    <div className="agent-page">
      <div className="agent-page__hero">
        <div>
          <p className="agent-page__eyebrow">Workspace</p>
          <h1 className="agent-page__title">My Applications</h1>
          <p className="agent-page__subtitle">Manage, preview, and publish your AI agents in one place.</p>
        </div>
        <div className="agent-page__actions">
          <button type="button" className="btn btn--ghost">
            Start with a template
          </button>
          <button type="button" className="btn btn--primary" onClick={() => navigate("/agent/new")}>
            + New Application
          </button>
        </div>
      </div>
      <div className="agent-page__content">
        <AgentList onCreate={() => navigate("/agent/new")} />
      </div>
    </div>
  );
}

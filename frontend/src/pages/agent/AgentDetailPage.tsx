import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getAgent } from "../../api/agents";
import { AgentKnowledgeBasePanel } from "../../components/agent/AgentKnowledgeBasePanel";
import { AgentSubAgentsPanel } from "../../components/agent/AgentSubAgentsPanel";
import { AgentToolsPanel } from "../../components/agent/AgentToolsPanel";
import { AgentWorkflowsPanel } from "../../components/agent/AgentWorkflowsPanel";
import { AGENT_DETAIL_TABS } from "../../constants/navigation";
import { getAgentTypeOption, getIndustryLabel } from "../../constants/agents";
import { NavIcon } from "../../components/ui/NavIcon";

const PERSONALITY_TAGS = [
  "Friendly",
  "Calm",
  "Approachable",
  "Expert Customer Service",
  "Professional",
  "Empathetic",
  "Custom",
];

export function AgentDetailPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const [activeTab, setActiveTab] = useState<(typeof AGENT_DETAIL_TABS)[number]["label"]>(
    AGENT_DETAIL_TABS[0].label,
  );

  const { data: agent, isLoading, isError, error } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => getAgent(agentId!),
    enabled: Boolean(agentId),
  });

  if (!agentId) {
    return <div className="agent-page__state">Invalid agent.</div>;
  }

  if (isLoading) {
    return <div className="agent-page__state">Loading agent…</div>;
  }

  if (isError || !agent) {
    const message =
      error && typeof error === "object" && "response" in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : null;
    return (
      <div className="agent-page">
        <div className="agent-page__state agent-page__state--error">{message ?? "Agent not found."}</div>
        <Link to="/agent" className="btn">
          Back to applications
        </Link>
      </div>
    );
  }

  const typeOption = getAgentTypeOption(agent.agent_type);

  return (
    <div className="agent-detail">
      <div className="agent-detail__topbar">
        <div className="agent-detail__tabs">
          {AGENT_DETAIL_TABS.map((tab) => (
            <button
              key={tab.label}
              type="button"
              className={`agent-detail__tab ${activeTab === tab.label ? "agent-detail__tab--active" : ""}`}
              onClick={() => setActiveTab(tab.label)}
            >
              <NavIcon name={tab.icon} className="agent-detail__tab-icon" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
        <div className="agent-detail__topbar-actions">
          <button type="button" className="btn btn--ghost">
            Preview
          </button>
          <button type="button" className="btn btn--primary">
            Publish
          </button>
        </div>
      </div>

      <div className="agent-detail__header">
        <div>
          <Link to="/agent" className="agent-detail__back">
            ← All applications
          </Link>
          <h1 className="agent-detail__title">{agent.name}</h1>
          <p className="agent-detail__subtitle">Instruct your agent with a prompt and let it handle the rest.</p>
          <div className="agent-detail__chips">
            <span className="agent-detail__chip">{getIndustryLabel(agent.industry)}</span>
            {typeOption ? <span className="agent-detail__chip">{typeOption.label}</span> : null}
            <span className={`agent-status agent-status--${agent.status}`}>{agent.status}</span>
          </div>
        </div>
        {activeTab === "Agent" ? (
          <div className="agent-detail__header-actions">
            <button type="button" className="btn btn--ghost">
              Clear
            </button>
            <button type="button" className="btn btn--primary">
              Save changes
            </button>
          </div>
        ) : null}
      </div>

      {activeTab === "Sub Agents" ? (
        <div className="agent-detail__tab-content">
          <AgentSubAgentsPanel agentId={agent.id} />
        </div>
      ) : activeTab === "Agent" ? (
        <div className="agent-detail__grid">
          <div className="agent-detail__main">
            <section className="agent-panel agent-panel--prompt">
              <div className="agent-panel__header">
                <h2>System prompt</h2>
                <span className="agent-panel__hint">Core instructions for your agent</span>
              </div>
              <div className="agent-panel__scroll">
                <textarea className="agent-panel__textarea" readOnly value={agent.system_prompt} />
              </div>
            </section>

            <div className="agent-detail__secondary">
              <section className="agent-panel agent-panel--compact">
                <div className="agent-panel__header">
                  <h2>Personality</h2>
                </div>
                <div className="agent-detail__tags">
                  {PERSONALITY_TAGS.map((tag) => (
                    <span
                      key={tag}
                      className={`agent-detail__tag ${tag === "Custom" ? "agent-detail__tag--active" : ""}`}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <input className="agent-panel__input" readOnly value={agent.personality} />
              </section>

              <section className="agent-panel agent-panel--compact">
                <div className="agent-panel__header">
                  <h2>Tone</h2>
                </div>
                <input className="agent-panel__input" readOnly value={agent.tone} />
              </section>
            </div>
          </div>

          <aside className="agent-detail__aside">
            <AgentToolsPanel agentId={agent.id} />
            <AgentWorkflowsPanel agentId={agent.id} />
            <AgentKnowledgeBasePanel agentId={agent.id} />

            <section className="agent-panel">
              <div className="agent-panel__header">
                <h2>Deployment</h2>
              </div>
              <dl className="agent-meta-list">
                <div>
                  <dt>Status</dt>
                  <dd>
                    <span className={`agent-status agent-status--${agent.status}`}>{agent.status}</span>
                  </dd>
                </div>
                <div>
                  <dt>Model</dt>
                  <dd>{agent.llm_config.model_id}</dd>
                </div>
                <div>
                  <dt>Region</dt>
                  <dd>{agent.llm_config.region}</dd>
                </div>
                <div>
                  <dt>Temperature</dt>
                  <dd>{agent.llm_config.temperature}</dd>
                </div>
              </dl>
            </section>
          </aside>
        </div>
      ) : (
        <div className="agent-detail__tab-content">
          <section className="agent-panel">
            <div className="agent-detail__empty-panel">
              <p>{activeTab} coming soon.</p>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

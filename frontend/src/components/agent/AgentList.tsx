import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listAgents, type AgentListItem } from "../../api/agents";
import { getAgentTypeOption, getIndustryLabel } from "../../constants/agents";

type AgentListProps = {
  onCreate: () => void;
};

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function matchesSearch(agent: AgentListItem, query: string): boolean {
  const haystack = [
    agent.name,
    agent.description,
    getIndustryLabel(agent.industry),
    getAgentTypeOption(agent.agent_type)?.label,
    agent.status,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return haystack.includes(query.toLowerCase());
}

export function AgentList({ onCreate }: AgentListProps) {
  const [search, setSearch] = useState("");

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["agents"],
    queryFn: () => listAgents(),
  });

  const agents = data?.items ?? [];
  const filteredAgents = useMemo(
    () => agents.filter((agent) => matchesSearch(agent, search.trim())),
    [agents, search],
  );

  if (isLoading) {
    return (
      <div className="agent-list-card">
        <div className="agent-list-card__loading">Loading your applications…</div>
      </div>
    );
  }

  if (isError) {
    const message =
      error && typeof error === "object" && "response" in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : null;
    return (
      <div className="agent-list-card agent-list-card--error">
        {message ?? "Failed to load applications. Please try again."}
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <div className="agent-empty">
        <div className="agent-empty__icon" aria-hidden>
          ✦
        </div>
        <h2 className="agent-empty__title">No applications yet</h2>
        <p className="agent-empty__text">
          Create your first AI agent to automate conversations, collections, and customer support.
        </p>
        <button type="button" className="btn btn--primary" onClick={onCreate}>
          + New Application
        </button>
      </div>
    );
  }

  return (
    <div className="agent-list-card">
      <div className="agent-list-card__toolbar">
        <label className="agent-search">
          <span className="agent-search__icon" aria-hidden>
            ⌕
          </span>
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search applications…"
          />
        </label>
        <span className="agent-list-card__count">
          {filteredAgents.length} of {agents.length}
        </span>
      </div>

      <div className="agent-list-table" role="table">
        <div className="agent-list-table__head" role="row">
          <span role="columnheader">Application</span>
          <span role="columnheader">Type</span>
          <span role="columnheader">Industry</span>
          <span role="columnheader">Status</span>
          <span role="columnheader">Created</span>
          <span className="agent-list-table__head-action" role="columnheader" aria-hidden />
        </div>

        {filteredAgents.length === 0 ? (
          <div className="agent-list-table__empty">No applications match your search.</div>
        ) : (
          filteredAgents.map((agent) => {
            const typeOption = getAgentTypeOption(agent.agent_type);
            return (
              <Link key={agent.id} to={`/agent/${agent.id}`} className="agent-list-row" role="row">
                <div className="agent-list-row__app" role="cell">
                  <span className="agent-list-row__avatar">{typeOption?.icon ?? "🤖"}</span>
                  <div>
                    <strong>{agent.name}</strong>
                    <p>{agent.description || typeOption?.description || "AI application"}</p>
                  </div>
                </div>
                <span className="agent-list-row__type" role="cell">
                  {typeOption?.label ?? "General agent"}
                </span>
                <span className="agent-list-row__industry" role="cell">
                  {getIndustryLabel(agent.industry)}
                </span>
                <span role="cell">
                  <span className={`agent-status agent-status--${agent.status}`}>{agent.status}</span>
                </span>
                <span className="agent-list-row__date" role="cell">
                  {formatDate(agent.created_at)}
                </span>
                <span className="agent-list-row__chevron" aria-hidden>
                  →
                </span>
              </Link>
            );
          })
        )}
      </div>
    </div>
  );
}

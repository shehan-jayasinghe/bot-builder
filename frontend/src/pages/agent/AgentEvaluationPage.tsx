import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getAgent } from "../../api/agents";
import { getDummyEvalDataset, getEvalRun, runEvaluation } from "../../api/evaluation";
import { listKnowledgebasesByAgent } from "../../api/knowledgebases";
import { AnswerRelevancyPanel } from "../../components/evaluation/AnswerRelevancyPanel";
import { ContextPrecisionPanel } from "../../components/evaluation/ContextPrecisionPanel";
import { ContextRecallPanel } from "../../components/evaluation/ContextRecallPanel";
import { EvalCaseTable } from "../../components/evaluation/EvalCaseTable";
import { FaithfulnessPanel } from "../../components/evaluation/FaithfulnessPanel";
import { getAgentTypeOption, getIndustryLabel } from "../../constants/agents";
import type { EvalCaseRow, EvalRunDetailResponse, MetricTab } from "../../types/evaluation";
import { getApiError } from "../../utils/apiError";
import { isAxiosError } from "axios";

const METRIC_TABS: Array<{ id: MetricTab; label: string }> = [
  { id: "faithfulness", label: "Faithfulness" },
  { id: "answer_relevancy", label: "Answer relevancy" },
  { id: "context_precision", label: "Context precision" },
  { id: "context_recall", label: "Context recall" },
];

function createCaseId(): string {
  return `case-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function emptyCase(): EvalCaseRow {
  return {
    id: createCaseId(),
    question: "",
    ground_truth: "",
    knowledge_base_names: [],
    mode: "full_bot",
  };
}

export function AgentEvaluationPage() {
  const { agentId = "" } = useParams();
  const [cases, setCases] = useState<EvalCaseRow[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<MetricTab>("faithfulness");
  const [currentRun, setCurrentRun] = useState<EvalRunDetailResponse | null>(null);
  const [runningCaseId, setRunningCaseId] = useState<string | null>(null);
  const [runningAll, setRunningAll] = useState(false);
  const [evalDisabled, setEvalDisabled] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  const agentQuery = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => getAgent(agentId),
    enabled: Boolean(agentId),
  });

  const kbQuery = useQuery({
    queryKey: ["knowledgebases", "agent", agentId],
    queryFn: () => listKnowledgebasesByAgent(agentId),
    enabled: Boolean(agentId),
  });

  const dummyMutation = useMutation({
    mutationFn: () => getDummyEvalDataset(agentId),
    onSuccess: (data) => {
      const loaded: EvalCaseRow[] = data.cases.map((item) => ({
        id: createCaseId(),
        question: item.question,
        ground_truth: item.ground_truth ?? "",
        knowledge_base_names: item.knowledge_base_names ?? [],
        mode: "full_bot",
      }));
      setCases(loaded);
      setSelectedCaseId(loaded[0]?.id ?? null);
      setPageError(null);
    },
    onError: (error) => {
      if (isAxiosError(error) && error.response?.status === 503) {
        setEvalDisabled(true);
      }
      setPageError(getApiError(error));
    },
  });

  const runMutation = useMutation({
    mutationFn: async (row: EvalCaseRow) => {
      const response = await runEvaluation(agentId, {
        question: row.question.trim(),
        ground_truth: row.ground_truth.trim() || null,
        mode: row.mode,
        knowledge_base_names:
          row.knowledge_base_names.length > 0 ? row.knowledge_base_names : null,
      });
      return { row, response };
    },
    onError: (error) => {
      if (isAxiosError(error) && error.response?.status === 503) {
        setEvalDisabled(true);
      }
      setPageError(getApiError(error));
      setRunningCaseId(null);
      setRunningAll(false);
    },
  });

  const knowledgeBases = useMemo(
    () => (kbQuery.data?.items ?? []).map((kb) => ({ id: kb.id, name: kb.name })),
    [kbQuery.data],
  );

  const selectedCase = cases.find((row) => row.id === selectedCaseId) ?? null;
  const hasGroundTruth = Boolean(selectedCase?.ground_truth.trim() || currentRun?.ground_truth);

  async function executeRun(row: EvalCaseRow) {
    setPageError(null);
    setRunningCaseId(row.id);
    setSelectedCaseId(row.id);

    try {
      const { row: caseRow, response } = await runMutation.mutateAsync(row);
      const detail = await getEvalRun(agentId, response.run_id);
      setCurrentRun(detail);
      setCases((prev) =>
        prev.map((item) =>
          item.id === caseRow.id
            ? {
                ...item,
                lastRunId: response.run_id,
                lastScores: response.scores,
                lastPassed: response.passed,
              }
            : item,
        ),
      );
    } finally {
      setRunningCaseId(null);
    }
  }

  async function handleRunSelected() {
    const row = cases.find((item) => item.id === selectedCaseId);
    if (!row?.question.trim()) {
      setPageError("Select a test case with a question.");
      return;
    }
    await executeRun(row);
  }

  async function handleRunAll() {
    const runnable = cases.filter((row) => row.question.trim());
    if (runnable.length === 0) {
      setPageError("Add at least one test case with a question.");
      return;
    }
    setRunningAll(true);
    setPageError(null);
    try {
      for (const row of runnable) {
        await executeRun(row);
      }
    } finally {
      setRunningAll(false);
    }
  }

  function handleCaseChange(id: string, patch: Partial<EvalCaseRow>) {
    setCases((prev) => prev.map((row) => (row.id === id ? { ...row, ...patch } : row)));
  }

  if (!agentId) {
    return <div className="agent-evaluation__state">Invalid agent.</div>;
  }

  if (agentQuery.isLoading) {
    return <div className="agent-evaluation__state">Loading evaluation lab…</div>;
  }

  if (agentQuery.isError || !agentQuery.data) {
    return (
      <div className="agent-evaluation">
        <div className="agent-evaluation__state agent-evaluation__state--error">
          {getApiError(agentQuery.error)}
        </div>
        <Link to="/agent" className="btn">
          Back to applications
        </Link>
      </div>
    );
  }

  const agent = agentQuery.data;
  const typeOption = getAgentTypeOption(agent.agent_type);

  return (
    <div className="agent-evaluation">
      <header className="agent-evaluation__header">
        <div className="agent-evaluation__header-main">
          <Link to={`/agent/${agentId}`} className="agent-evaluation__back">
            ← Back to {agent.name}
          </Link>
          <h1 className="agent-evaluation__title">Eval Lab</h1>
          <p className="agent-evaluation__subtitle">
            Run RAGAS metrics on test cases — {getIndustryLabel(agent.industry)}
            {typeOption ? ` / ${typeOption.label}` : ""}
          </p>
          <div className="agent-evaluation__links">
            <Link to={`/agent/${agentId}/preview`} className="agent-evaluation__nav-link">
              Preview
            </Link>
            <span className="agent-evaluation__nav-sep">|</span>
            <span className="agent-evaluation__nav-link agent-evaluation__nav-link--active">
              Evaluation
            </span>
          </div>
        </div>
      </header>

      {evalDisabled ? (
        <div className="agent-evaluation__banner agent-evaluation__banner--warn">
          RAG evaluation is disabled on the server (`RAG_EVAL_ENABLED=false`). Run buttons are
          disabled.
        </div>
      ) : null}

      {knowledgeBases.length === 0 ? (
        <div className="agent-evaluation__banner">
          Attach knowledge bases to this agent for meaningful RAG metrics.
        </div>
      ) : null}

      {pageError ? <div className="agent-evaluation__banner agent-evaluation__banner--error">{pageError}</div> : null}

      <div className="agent-evaluation__layout">
        <section className="agent-evaluation__panel agent-evaluation__panel--cases">
          <div className="agent-evaluation__panel-head">
            <h2>Test cases</h2>
          </div>
          <div className="agent-evaluation__panel-body">
            <EvalCaseTable
              cases={cases}
              selectedId={selectedCaseId}
              knowledgeBases={knowledgeBases}
              runningCaseId={runningCaseId}
              runningAll={runningAll}
              evalDisabled={evalDisabled}
              onSelect={setSelectedCaseId}
              onChange={handleCaseChange}
              onAdd={() => {
                const row = emptyCase();
                setCases((prev) => [...prev, row]);
                setSelectedCaseId(row.id);
              }}
              onLoadDummy={() => dummyMutation.mutate()}
              onRunSelected={() => void handleRunSelected()}
              onRunCase={(id) => {
                const row = cases.find((item) => item.id === id);
                if (row) {
                  void executeRun(row);
                }
              }}
              onRunAll={() => void handleRunAll()}
              isLoadingDummy={dummyMutation.isPending}
            />
          </div>
        </section>

        <section className="agent-evaluation__panel agent-evaluation__panel--metrics">
          <div className="agent-evaluation__panel-head">
            <div className="agent-evaluation__tabs">
              {METRIC_TABS.map((tab) => {
                const disabled = tab.id === "context_recall" && !hasGroundTruth;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    className={`agent-evaluation__tab ${
                      activeTab === tab.id ? "agent-evaluation__tab--active" : ""
                    }`}
                    disabled={disabled}
                    title={
                      disabled ? "Add ground truth to enable context recall" : undefined
                    }
                    onClick={() => setActiveTab(tab.id)}
                  >
                    {tab.label}
                  </button>
                );
              })}
            </div>
            {currentRun ? (
              <span className="agent-evaluation__run-badge">
                Run {currentRun.run_id.slice(-6)}
              </span>
            ) : null}
          </div>
          <div className="agent-evaluation__panel-body">
            {activeTab === "faithfulness" ? <FaithfulnessPanel run={currentRun} /> : null}
            {activeTab === "answer_relevancy" ? (
              <AnswerRelevancyPanel run={currentRun} />
            ) : null}
            {activeTab === "context_precision" ? (
              <ContextPrecisionPanel run={currentRun} />
            ) : null}
            {activeTab === "context_recall" ? (
              <ContextRecallPanel run={currentRun} hasGroundTruth={hasGroundTruth} />
            ) : null}
          </div>
        </section>
      </div>
    </div>
  );
}

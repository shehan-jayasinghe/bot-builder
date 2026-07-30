import type { EvalCaseRow, EvalMode } from "../../types/evaluation";

type KnowledgeBaseOption = {
  id: string;
  name: string;
};

type EvalCaseTableProps = {
  cases: EvalCaseRow[];
  selectedId: string | null;
  knowledgeBases: KnowledgeBaseOption[];
  runningCaseId: string | null;
  runningAll: boolean;
  evalDisabled: boolean;
  onSelect: (id: string) => void;
  onChange: (id: string, patch: Partial<EvalCaseRow>) => void;
  onAdd: () => void;
  onLoadDummy: () => void;
  onRunSelected: () => void;
  onRunCase: (id: string) => void;
  onRunAll: () => void;
  isLoadingDummy: boolean;
};

function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return value.toFixed(2);
}

function scoreSummary(scores: EvalCaseRow["lastScores"]): string {
  if (!scores) {
    return "—";
  }
  const parts = [
    scores.faithfulness,
    scores.answer_relevancy,
    scores.context_precision,
    scores.context_recall,
  ].filter((value) => value !== null && value !== undefined);
  if (parts.length === 0) {
    return "—";
  }
  const avg = parts.reduce((sum, value) => sum + value, 0) / parts.length;
  return formatScore(avg);
}

export function EvalCaseTable({
  cases,
  selectedId,
  knowledgeBases,
  runningCaseId,
  runningAll,
  evalDisabled,
  onSelect,
  onChange,
  onAdd,
  onLoadDummy,
  onRunSelected,
  onRunCase,
  onRunAll,
  isLoadingDummy,
}: EvalCaseTableProps) {
  const busy = Boolean(runningCaseId) || runningAll;
  const canRun = !evalDisabled && !busy && cases.length > 0;

  return (
    <div className="eval-cases">
      <div className="eval-cases__toolbar">
        <button type="button" className="btn btn--ghost" onClick={onAdd} disabled={evalDisabled}>
          + Add row
        </button>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={onLoadDummy}
          disabled={evalDisabled || isLoadingDummy}
        >
          {isLoadingDummy ? "Loading…" : "Load dummy"}
        </button>
        <button
          type="button"
          className="btn btn--primary"
          onClick={onRunSelected}
          disabled={!canRun || !selectedId}
        >
          {runningCaseId ? "Running…" : "Run selected"}
        </button>
        <button type="button" className="btn btn--ghost" onClick={onRunAll} disabled={!canRun}>
          {runningAll ? "Running all…" : "Run all"}
        </button>
      </div>

      {cases.length === 0 ? (
        <div className="eval-cases__empty">
          <p>No test cases</p>
          <span>Add a row or load dummy data for this agent profile.</span>
        </div>
      ) : (
        <div className="eval-cases__table-wrap">
          <table className="eval-cases__table">
            <thead>
              <tr>
                <th>Question</th>
                <th>Ground truth</th>
                <th>Mode</th>
                <th>KB scope</th>
                <th>Last score</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {cases.map((row) => {
                const isSelected = row.id === selectedId;
                const isRunning = runningCaseId === row.id;
                return (
                  <tr
                    key={row.id}
                    className={`eval-cases__row ${isSelected ? "eval-cases__row--selected" : ""}`}
                    onClick={() => onSelect(row.id)}
                  >
                    <td>
                      <textarea
                        className="eval-cases__input"
                        value={row.question}
                        rows={2}
                        placeholder="User question"
                        onClick={(event) => event.stopPropagation()}
                        onChange={(event) =>
                          onChange(row.id, { question: event.target.value })
                        }
                      />
                    </td>
                    <td>
                      <textarea
                        className="eval-cases__input"
                        value={row.ground_truth}
                        rows={2}
                        placeholder="Optional reference answer"
                        onClick={(event) => event.stopPropagation()}
                        onChange={(event) =>
                          onChange(row.id, { ground_truth: event.target.value })
                        }
                      />
                    </td>
                    <td>
                      <select
                        className="eval-cases__select"
                        value={row.mode}
                        onClick={(event) => event.stopPropagation()}
                        onChange={(event) =>
                          onChange(row.id, { mode: event.target.value as EvalMode })
                        }
                      >
                        <option value="full_bot">Full bot</option>
                        <option value="rag_only">RAG only</option>
                      </select>
                    </td>
                    <td>
                      <select
                        className="eval-cases__select"
                        multiple
                        value={row.knowledge_base_names}
                        onClick={(event) => event.stopPropagation()}
                        onChange={(event) => {
                          const selected = Array.from(event.target.selectedOptions).map(
                            (option) => option.value,
                          );
                          onChange(row.id, { knowledge_base_names: selected });
                        }}
                      >
                        {knowledgeBases.length === 0 ? (
                          <option disabled value="">
                            No KBs
                          </option>
                        ) : (
                          knowledgeBases.map((kb) => (
                            <option key={kb.id} value={kb.name}>
                              {kb.name}
                            </option>
                          ))
                        )}
                      </select>
                    </td>
                    <td>
                      <span
                        className={`eval-cases__score ${
                          row.lastPassed === false
                            ? "eval-cases__score--fail"
                            : row.lastPassed
                              ? "eval-cases__score--pass"
                              : ""
                        }`}
                      >
                        {isRunning ? "…" : scoreSummary(row.lastScores)}
                      </span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn--ghost eval-cases__run-btn"
                        disabled={!canRun}
                        onClick={(event) => {
                          event.stopPropagation();
                          onSelect(row.id);
                          onRunCase(row.id);
                        }}
                      >
                        Run
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

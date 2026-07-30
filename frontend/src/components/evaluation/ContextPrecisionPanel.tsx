import type { EvalRunDetailResponse } from "../../types/evaluation";
import { MetricScoreBar } from "./MetricScoreBar";

type ContextPrecisionPanelProps = {
  run: EvalRunDetailResponse | null;
};

export function ContextPrecisionPanel({ run }: ContextPrecisionPanelProps) {
  if (!run) {
    return (
      <div className="eval-metric__empty">
        <p>No run selected</p>
        <span>Run a test case to see context precision.</span>
      </div>
    );
  }

  const detail = run.context_precision_detail;
  const chunks = detail?.ranked_chunks ?? [];
  const precisionAtK = detail?.precision_at_k ?? [];

  if (chunks.length === 0) {
    return (
      <div className="eval-metric__empty">
        <p>No retrieval in this run</p>
        <span>Context precision needs ranked RAG chunks.</span>
      </div>
    );
  }

  return (
    <div className="eval-metric eval-metric--precision">
      <section className="eval-metric__card">
        <h3 className="eval-metric__card-title">Ranked chunks</h3>
        <ul className="eval-precision__chunks">
          {chunks.map((chunk) => (
            <li key={chunk.rank} className="eval-precision__chunk">
              <div className="eval-precision__chunk-head">
                <span className="eval-precision__rank">#{chunk.rank}</span>
                <span
                  className={`eval-precision__label eval-precision__label--${chunk.label}`}
                >
                  {chunk.label}
                </span>
              </div>
              <p className="eval-precision__chunk-text">{chunk.text}</p>
              {precisionAtK[chunk.rank - 1] !== undefined ? (
                <div className="eval-precision__pk">
                  <span>P@{chunk.rank}</span>
                  <div className="eval-precision__pk-bar">
                    <div
                      className="eval-precision__pk-fill"
                      style={{ width: `${precisionAtK[chunk.rank - 1] * 100}%` }}
                    />
                  </div>
                  <span>{(precisionAtK[chunk.rank - 1] * 100).toFixed(0)}%</span>
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      </section>

      <MetricScoreBar
        label="Context precision"
        score={detail?.score ?? run.scores.context_precision}
        threshold={run.thresholds.context_precision}
        passed={
          run.scores.context_precision !== null && run.scores.context_precision !== undefined
            ? run.scores.context_precision >= run.thresholds.context_precision
            : null
        }
      />
    </div>
  );
}

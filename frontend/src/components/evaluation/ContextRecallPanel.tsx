import type { EvalRunDetailResponse } from "../../types/evaluation";
import { MetricScoreBar } from "./MetricScoreBar";

type ContextRecallPanelProps = {
  run: EvalRunDetailResponse | null;
  hasGroundTruth: boolean;
};

export function ContextRecallPanel({ run, hasGroundTruth }: ContextRecallPanelProps) {
  if (!hasGroundTruth) {
    return (
      <div className="eval-metric__empty">
        <p>Ground truth required</p>
        <span>Add ground truth to the test case to evaluate context recall.</span>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="eval-metric__empty">
        <p>No run selected</p>
        <span>Run a test case with ground truth to see context recall.</span>
      </div>
    );
  }

  const detail = run.context_recall_detail;
  const claims = detail?.reference_claims ?? [];

  return (
    <div className="eval-metric eval-metric--recall">
      <section className="eval-metric__card">
        <h3 className="eval-metric__card-title">Reference (ground truth)</h3>
        <p className="eval-recall__ground-truth">{run.ground_truth || "—"}</p>

        <h3 className="eval-metric__card-title">Reference claims vs context</h3>
        {claims.length === 0 ? (
          <p className="eval-metric__muted">No reference claim breakdown available.</p>
        ) : (
          <ul className="eval-recall__claims">
            {claims.map((claim, index) => (
              <li
                key={`${claim.text}-${index}`}
                className={`eval-recall__claim eval-recall__claim--${claim.verdict}`}
              >
                <span className="eval-recall__claim-verdict">{claim.verdict}</span>
                <span className="eval-recall__claim-text">{claim.text}</span>
                {claim.chunk_index !== null ? (
                  <span className="eval-recall__chunk-ref">chunk #{claim.chunk_index + 1}</span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      <MetricScoreBar
        label="Context recall"
        score={detail?.score ?? run.scores.context_recall}
        formula={
          claims.length > 0
            ? `${claims.filter((c) => c.verdict === "supported").length} / ${claims.length} claims supported`
            : undefined
        }
      />
    </div>
  );
}

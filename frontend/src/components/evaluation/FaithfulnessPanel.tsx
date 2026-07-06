import type { ReactNode } from "react";

import type { EvalRunDetailResponse, FaithfulnessClaim } from "../../types/evaluation";
import { MetricScoreBar } from "./MetricScoreBar";

type FaithfulnessPanelProps = {
  run: EvalRunDetailResponse | null;
};

function flattenContexts(run: EvalRunDetailResponse): string[] {
  const chunks: string[] = [];
  for (const retrieval of run.turn_evidence?.rag_retrievals ?? []) {
    for (const chunk of retrieval.chunks ?? []) {
      if (chunk.text?.trim()) {
        chunks.push(chunk.text.trim());
      }
    }
  }
  return chunks;
}

function highlightAnswer(answer: string, claims: FaithfulnessClaim[]): ReactNode {
  if (!answer || claims.length === 0) {
    return answer || "—";
  }

  const hallucinated = claims.filter((claim) => claim.verdict === "hallucinated");
  if (hallucinated.length === 0) {
    return answer;
  }

  let nodes: ReactNode[] = [answer];
  for (const claim of hallucinated) {
    const text = claim.text.trim();
    if (!text) {
      continue;
    }
    nodes = nodes.flatMap((node, index) => {
      if (typeof node !== "string" || !node.includes(text)) {
        return [node];
      }
      const parts = node.split(text);
      const result: ReactNode[] = [];
      parts.forEach((part, partIndex) => {
        if (part) {
          result.push(part);
        }
        if (partIndex < parts.length - 1) {
          result.push(
            <mark key={`${text}-${index}-${partIndex}`} className="eval-faithfulness__highlight">
              {text}
            </mark>,
          );
        }
      });
      return result;
    });
  }
  return nodes;
}

export function FaithfulnessPanel({ run }: FaithfulnessPanelProps) {
  if (!run) {
    return (
      <div className="eval-metric__empty">
        <p>No run selected</p>
        <span>Run a test case to see faithfulness breakdown.</span>
      </div>
    );
  }

  const contexts = flattenContexts(run);
  const answer = (run.turn_evidence?.assistant_replies ?? []).join("\n");
  const detail = run.faithfulness_detail;
  const claims = detail?.claims ?? [];

  if (!contexts.length && !answer) {
    return (
      <div className="eval-metric__empty">
        <p>No retrieval in this run</p>
        <span>Faithfulness needs an assistant reply and retrieved context.</span>
      </div>
    );
  }

  const groundedCount = claims.filter((claim) => claim.verdict === "grounded").length;
  const formula =
    claims.length > 0 ? `${groundedCount} / ${claims.length} claims grounded` : undefined;

  return (
    <div className="eval-metric eval-metric--faithfulness">
      <div className="eval-metric__split">
        <section className="eval-metric__card">
          <h3 className="eval-metric__card-title">Retrieved context</h3>
          {contexts.length === 0 ? (
            <p className="eval-metric__muted">No chunks retrieved.</p>
          ) : (
            <ol className="eval-faithfulness__context-list">
              {contexts.map((text, index) => (
                <li key={index} className="eval-faithfulness__context-item">
                  {text}
                </li>
              ))}
            </ol>
          )}
          <h3 className="eval-metric__card-title">Assistant response</h3>
          <p className="eval-faithfulness__answer">{highlightAnswer(answer, claims)}</p>
        </section>

        <section className="eval-metric__card">
          <h3 className="eval-metric__card-title">Claims</h3>
          {claims.length === 0 ? (
            <p className="eval-metric__muted">No claim breakdown available.</p>
          ) : (
            <ul className="eval-faithfulness__claims">
              {claims.map((claim, index) => (
                <li
                  key={`${claim.text}-${index}`}
                  className={`eval-faithfulness__claim eval-faithfulness__claim--${claim.verdict}`}
                >
                  <span className="eval-faithfulness__claim-verdict">{claim.verdict}</span>
                  <span className="eval-faithfulness__claim-text">{claim.text}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <MetricScoreBar
        label="Faithfulness"
        score={detail?.score ?? run.scores.faithfulness}
        threshold={run.thresholds.faithfulness}
        formula={formula}
        passed={
          run.scores.faithfulness !== null && run.scores.faithfulness !== undefined
            ? run.scores.faithfulness >= run.thresholds.faithfulness
            : null
        }
      />
    </div>
  );
}

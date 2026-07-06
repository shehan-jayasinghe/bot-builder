import type { EvalRunDetailResponse } from "../../types/evaluation";
import { MetricScoreBar } from "./MetricScoreBar";

type AnswerRelevancyPanelProps = {
  run: EvalRunDetailResponse | null;
};

export function AnswerRelevancyPanel({ run }: AnswerRelevancyPanelProps) {
  if (!run) {
    return (
      <div className="eval-metric__empty">
        <p>No run selected</p>
        <span>Run a test case to see answer relevancy.</span>
      </div>
    );
  }

  const detail = run.answer_relevancy_detail;
  const questions = detail?.generated_questions ?? [];
  const similarities = detail?.similarities ?? [];

  return (
    <div className="eval-metric eval-metric--relevancy">
      <section className="eval-metric__card">
        <h3 className="eval-metric__card-title">Original question</h3>
        <p className="eval-relevancy__question">{run.question}</p>

        <h3 className="eval-metric__card-title">Generated questions from answer</h3>
        {questions.length === 0 ? (
          <p className="eval-metric__muted">No generated questions in this run.</p>
        ) : (
          <ul className="eval-relevancy__list">
            {questions.map((question, index) => (
              <li key={index} className="eval-relevancy__item">
                <span className="eval-relevancy__item-text">{question}</span>
                {similarities[index] !== undefined ? (
                  <span className="eval-relevancy__similarity">
                    {(similarities[index] * 100).toFixed(0)}% similar
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      <MetricScoreBar
        label="Answer relevancy"
        score={detail?.score ?? run.scores.answer_relevancy}
        formula={questions.length > 0 ? "Average cosine similarity vs original question" : undefined}
      />
    </div>
  );
}

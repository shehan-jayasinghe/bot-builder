type MetricScoreBarProps = {
  label: string;
  score: number | null | undefined;
  threshold?: number | null;
  formula?: string;
  passed?: boolean | null;
};

function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return value.toFixed(2);
}

export function MetricScoreBar({
  label,
  score,
  threshold,
  formula,
  passed,
}: MetricScoreBarProps) {
  const pct =
    score !== null && score !== undefined && !Number.isNaN(score)
      ? Math.min(100, Math.max(0, score * 100))
      : 0;

  const thresholdPct =
    threshold !== null && threshold !== undefined ? Math.min(100, threshold * 100) : null;

  return (
    <footer className="eval-metric__footer">
      <div className="eval-metric__score-head">
        <span className="eval-metric__score-label">{label}</span>
        <span className="eval-metric__score-value">{formatScore(score)}</span>
        {passed !== null && passed !== undefined ? (
          <span className={`eval-metric__badge eval-metric__badge--${passed ? "pass" : "fail"}`}>
            {passed ? "Pass" : "Fail"}
          </span>
        ) : null}
      </div>
      <div className="eval-metric__bar-track">
        <div className="eval-metric__bar-fill" style={{ width: `${pct}%` }} />
        {thresholdPct !== null ? (
          <div className="eval-metric__bar-threshold" style={{ left: `${thresholdPct}%` }} />
        ) : null}
      </div>
      {formula ? <p className="eval-metric__formula">{formula}</p> : null}
      {threshold !== null && threshold !== undefined ? (
        <p className="eval-metric__threshold-hint">Threshold: {threshold.toFixed(2)}</p>
      ) : null}
    </footer>
  );
}

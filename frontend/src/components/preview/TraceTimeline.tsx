import type { PreviewTraceTurn } from "../../types/preview";
import {
  buildTraceTimeline,
  formatTraceTimestamp,
  type TraceTimelineItem,
} from "../../utils/traceTimeline";

type TraceTimelineProps = {
  turns: PreviewTraceTurn[];
  isLoading?: boolean;
};

function TraceRow({ item }: { item: TraceTimelineItem }) {
  return (
    <div className={`trace-item trace-item--${item.kind}`}>
      <div className="trace-item__marker" aria-hidden="true" />
      <div className="trace-item__body">
        <div className="trace-item__header">
          <span className="trace-item__label">{item.label}</span>
          <time className="trace-item__time" dateTime={item.at}>
            {formatTraceTimestamp(item.at)}
          </time>
        </div>
        {item.detail ? <p className="trace-item__detail">{item.detail}</p> : null}
        {item.nested?.length ? (
          <div className="trace-item__nested">
            {item.nested.map((child) => (
              <div key={child.id} className="trace-item__nested-row">
                <span className="trace-item__nested-dot" aria-hidden="true" />
                <span className="trace-item__nested-label">{child.detail ?? child.label}</span>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function TraceTimeline({ turns, isLoading }: TraceTimelineProps) {
  const items = buildTraceTimeline(turns);

  if (isLoading) {
    return <div className="trace-timeline__state">Loading trace…</div>;
  }

  if (items.length === 0) {
    return (
      <div className="trace-timeline__empty">
        <p>No trace yet</p>
        <span>Send a message in preview chat to see the execution timeline.</span>
      </div>
    );
  }

  return (
    <div className="trace-timeline">
      {items.map((item) => (
        <TraceRow key={item.id} item={item} />
      ))}
    </div>
  );
}

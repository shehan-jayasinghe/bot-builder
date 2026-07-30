import { useEffect, useState } from "react";

import {
  capabilityKindLabel,
  ROUTING_HINT_MAX_LENGTH,
  routingHintPlaceholder,
  type CapabilityKind,
} from "../../constants/routingHint";

type RoutingHintModalProps = {
  open: boolean;
  capabilityKind: CapabilityKind;
  resourceName: string;
  initialHint?: string;
  submitting?: boolean;
  error?: string | null;
  onClose: () => void;
  onConfirm: (routingHint: string | null) => void;
};

export function RoutingHintModal({
  open,
  capabilityKind,
  resourceName,
  initialHint = "",
  submitting = false,
  error = null,
  onClose,
  onConfirm,
}: RoutingHintModalProps) {
  const [hint, setHint] = useState(initialHint);

  useEffect(() => {
    if (open) {
      setHint(initialHint);
    }
  }, [open, initialHint]);

  if (!open) {
    return null;
  }

  const trimmed = hint.trim();
  const kindLabel = capabilityKindLabel(capabilityKind);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    onConfirm(trimmed.length > 0 ? trimmed : null);
  }

  return (
    <div className="modal-overlay" role="presentation" onClick={submitting ? undefined : onClose}>
      <div
        className="modal"
        role="dialog"
        aria-labelledby="routing-hint-title"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal__header">
          <div>
            <h2 id="routing-hint-title">When should the agent use this?</h2>
            <p className="modal__subtitle">
              Attach <strong>{resourceName}</strong> to this agent. Tell the orchestrator when to choose this{" "}
              {kindLabel}.
            </p>
          </div>
          <button
            type="button"
            className="modal__close"
            onClick={onClose}
            aria-label="Close"
            disabled={submitting}
          >
            ×
          </button>
        </div>

        <form className="modal__body" onSubmit={handleSubmit}>
          {error ? <p className="agent-panel__error">{error}</p> : null}

          <label className="agent-detail__field">
            <span>Routing hint</span>
            <textarea
              className="agent-panel__textarea"
              rows={4}
              value={hint}
              onChange={(event) => setHint(event.target.value)}
              placeholder={routingHintPlaceholder(capabilityKind)}
              maxLength={ROUTING_HINT_MAX_LENGTH}
              autoFocus
            />
            <span className="agent-detail__field-hint">
              Optional — guides the main agent at chat time ({trimmed.length}/{ROUTING_HINT_MAX_LENGTH})
            </span>
          </label>

          <div className="modal__footer">
            <button type="button" className="btn btn--ghost" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn--primary" disabled={submitting}>
              {submitting ? "Attaching…" : "Attach"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

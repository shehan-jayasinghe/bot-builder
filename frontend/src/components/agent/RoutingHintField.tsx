import {
  capabilityKindLabel,
  ROUTING_HINT_MAX_LENGTH,
  routingHintPlaceholder,
  type CapabilityKind,
} from "../../constants/routingHint";

type RoutingHintFieldProps = {
  capabilityKind: CapabilityKind;
  value: string;
  onChange: (value: string) => void;
};

export function RoutingHintField({ capabilityKind, value, onChange }: RoutingHintFieldProps) {
  const trimmed = value.trim();
  const kindLabel = capabilityKindLabel(capabilityKind);

  return (
    <label className="agent-detail__field">
      <span>When should the agent use this {kindLabel}?</span>
      <textarea
        className="agent-panel__textarea"
        rows={3}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={routingHintPlaceholder(capabilityKind)}
        maxLength={ROUTING_HINT_MAX_LENGTH}
      />
      <span className="agent-detail__field-hint">
        Optional routing hint for the orchestrator ({trimmed.length}/{ROUTING_HINT_MAX_LENGTH})
      </span>
    </label>
  );
}

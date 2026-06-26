type AttachDetachButtonProps = {
  attached: boolean;
  disabled?: boolean;
  onAttach: () => void;
  onDetach: () => void;
};

export function AttachDetachButton({ attached, disabled = false, onAttach, onDetach }: AttachDetachButtonProps) {
  return (
    <button
      type="button"
      className={attached ? "agent-attach-btn agent-attach-btn--detach" : "agent-attach-btn"}
      disabled={disabled}
      onClick={attached ? onDetach : onAttach}
    >
      {attached ? "Detach" : "Attach"}
    </button>
  );
}

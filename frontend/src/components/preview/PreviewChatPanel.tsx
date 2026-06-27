import { useEffect, useRef, type FormEvent, type KeyboardEvent } from "react";

import type { ChatButton } from "../../types/preview";

export type PreviewChatEntry = {
  id: string;
  role: "user" | "assistant";
  text: string;
  buttons?: ChatButton[] | null;
};

type PreviewChatPanelProps = {
  messages: PreviewChatEntry[];
  draft: string;
  onDraftChange: (value: string) => void;
  onSend: () => void;
  isSending?: boolean;
  agentName?: string;
};

export function PreviewChatPanel({
  messages,
  draft,
  onDraftChange,
  onSend,
  isSending,
  agentName,
}: PreviewChatPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, isSending]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim() || isSending) {
      return;
    }
    onSend();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!draft.trim() || isSending) {
        return;
      }
      onSend();
    }
  }

  return (
    <div className="preview-chat">
      <div className="preview-chat__header">
        <div>
          <h2>Preview</h2>
          <p>{agentName ? `Chat with ${agentName}` : "Test your agent"}</p>
        </div>
      </div>

      <div className="preview-chat__messages" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="preview-chat__empty">
            <p>Start a conversation</p>
            <span>Messages you send here run through the full agent pipeline.</span>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`preview-chat__bubble preview-chat__bubble--${message.role}`}
            >
              <p>{message.text}</p>
              {message.buttons?.length ? (
                <div className="preview-chat__buttons">
                  {message.buttons.map((button) => (
                    <button key={button.payload} type="button" className="preview-chat__button-chip">
                      {button.title}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ))
        )}
        {isSending ? (
          <div className="preview-chat__bubble preview-chat__bubble--assistant preview-chat__bubble--typing">
            <span className="preview-chat__typing-dots" aria-label="Agent is typing">
              <span />
              <span />
              <span />
            </span>
          </div>
        ) : null}
      </div>

      <form className="preview-chat__composer" onSubmit={handleSubmit}>
        <textarea
          className="preview-chat__input"
          placeholder="Type a message…"
          rows={2}
          value={draft}
          onChange={(event) => onDraftChange(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSending}
        />
        <button type="submit" className="btn btn--primary preview-chat__send" disabled={isSending || !draft.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getAgent } from "../../api/agents";
import { getPreviewTrace, getRuntimeGraph, previewChat } from "../../api/preview";
import { PreviewChatPanel, type PreviewChatEntry } from "../../components/preview/PreviewChatPanel";
import { RuntimeGraphCanvas } from "../../components/preview/RuntimeGraphCanvas";
import { TraceTimeline } from "../../components/preview/TraceTimeline";
import { clearPreviewSenderId, getOrCreatePreviewSenderId } from "../../utils/previewSession";
import { layoutRuntimeGraph, resolveHighlightedNodeId } from "../../utils/runtimeGraphLayout";
import { getApiError } from "../../utils/apiError";

export function AgentPreviewPage() {
  const { agentId = "" } = useParams();
  const queryClient = useQueryClient();

  const [senderId, setSenderId] = useState(() =>
    agentId ? getOrCreatePreviewSenderId(agentId) : "",
  );
  const [draft, setDraft] = useState("");
  const [chatMessages, setChatMessages] = useState<PreviewChatEntry[]>([]);
  const [zoom, setZoom] = useState(1);
  const [sendError, setSendError] = useState<string | null>(null);

  useEffect(() => {
    if (agentId) {
      setSenderId(getOrCreatePreviewSenderId(agentId));
      setChatMessages([]);
      setDraft("");
      setSendError(null);
    }
  }, [agentId]);

  const agentQuery = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => getAgent(agentId),
    enabled: Boolean(agentId),
  });

  const graphQuery = useQuery({
    queryKey: ["runtime-graph", agentId],
    queryFn: () => getRuntimeGraph(agentId),
    enabled: Boolean(agentId),
  });

  const traceQuery = useQuery({
    queryKey: ["preview-trace", agentId, senderId],
    queryFn: () => getPreviewTrace(agentId, senderId),
    enabled: Boolean(agentId && senderId),
  });

  const chatMutation = useMutation({
    mutationFn: (message: string) =>
      previewChat(agentId, {
        sender_id: senderId,
        message,
        metadata: {},
      }),
    onSuccess: async (response) => {
      setSendError(null);
      const assistantMessages = response.messages
        .filter((item) => item.text)
        .map((item, index) => ({
          id: `assistant-${Date.now()}-${index}`,
          role: "assistant" as const,
          text: item.text ?? "",
          buttons: item.buttons,
        }));
      setChatMessages((prev) => [...prev, ...assistantMessages]);
      await queryClient.invalidateQueries({ queryKey: ["preview-trace", agentId, senderId] });
      setDraft("");
    },
    onError: (error) => {
      setSendError(getApiError(error));
    },
  });

  const layout = useMemo(() => {
    if (!graphQuery.data) {
      return null;
    }
    return layoutRuntimeGraph(graphQuery.data);
  }, [graphQuery.data]);

  const highlightedNodeId = useMemo(() => {
    const turns = traceQuery.data?.turns ?? [];
    const lastTurn = turns[turns.length - 1];
    return resolveHighlightedNodeId(
      lastTurn?.routing_decision,
      graphQuery.data?.orchestrator.id ?? "",
    );
  }, [traceQuery.data, graphQuery.data]);

  function handleSend(messageText?: string) {
    const message = (messageText ?? draft).trim();
    if (!message || chatMutation.isPending) {
      return;
    }
    setChatMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: "user", text: message },
    ]);
    if (!messageText) {
      setDraft("");
    }
    chatMutation.mutate(message);
  }

  function handleClear() {
    const nextSenderId = clearPreviewSenderId(agentId);
    setSenderId(nextSenderId);
    setChatMessages([]);
    setDraft("");
    setSendError(null);
    queryClient.removeQueries({ queryKey: ["preview-trace", agentId] });
  }

  if (!agentId) {
    return <div className="agent-preview__state">Invalid agent.</div>;
  }

  if (agentQuery.isLoading || graphQuery.isLoading) {
    return <div className="agent-preview__state">Loading preview…</div>;
  }

  if (agentQuery.isError || graphQuery.isError || !agentQuery.data) {
    const message = getApiError(agentQuery.error ?? graphQuery.error);
    return (
      <div className="agent-preview">
        <div className="agent-preview__state agent-preview__state--error">{message}</div>
        <Link to={`/agent/${agentId}`} className="btn">
          Back to agent
        </Link>
      </div>
    );
  }

  const agent = agentQuery.data;

  return (
    <div className="agent-preview">
      <header className="agent-preview__header">
        <div className="agent-preview__header-main">
          <Link to={`/agent/${agentId}`} className="agent-preview__back">
            ← Back to {agent.name}
          </Link>
          <h1 className="agent-preview__title">Preview</h1>
          <p className="agent-preview__subtitle">
            Test your agent, inspect routing, and review the execution trace.
          </p>
        </div>
        <div className="agent-preview__header-actions">
          <button type="button" className="btn btn--ghost" onClick={handleClear}>
            Clear session
          </button>
        </div>
      </header>

      <div className="agent-preview__panels">
        <section className="agent-preview__panel agent-preview__panel--graph">
          <div className="agent-preview__panel-head">
            <h2>Agent View</h2>
            <div className="agent-preview__zoom">
              <button type="button" onClick={() => setZoom((value) => Math.max(0.6, value - 0.1))} aria-label="Zoom out">
                −
              </button>
              <span>{Math.round(zoom * 100)}%</span>
              <button type="button" onClick={() => setZoom((value) => Math.min(1.4, value + 0.1))} aria-label="Zoom in">
                +
              </button>
            </div>
          </div>
          <div className="agent-preview__panel-body agent-preview__panel-body--canvas">
            {layout ? (
              <RuntimeGraphCanvas
                nodes={layout.nodes}
                edges={layout.edges}
                highlightedNodeId={highlightedNodeId}
                zoom={zoom}
                orchestratorMeta={{
                  status: graphQuery.data?.orchestrator.status ?? agent.status,
                  description: graphQuery.data?.orchestrator.description ?? agent.description,
                }}
              />
            ) : (
              <div className="agent-preview__panel-empty">No graph data.</div>
            )}
          </div>
        </section>

        <section className="agent-preview__panel agent-preview__panel--trace">
          <div className="agent-preview__panel-head">
            <h2>Trace View</h2>
            {traceQuery.isFetching ? <span className="agent-preview__panel-badge">Updating…</span> : null}
          </div>
          <div className="agent-preview__panel-body">
            <TraceTimeline turns={traceQuery.data?.turns ?? []} isLoading={traceQuery.isLoading} />
          </div>
        </section>

        <section className="agent-preview__panel agent-preview__panel--chat">
          <PreviewChatPanel
            messages={chatMessages}
            draft={draft}
            onDraftChange={setDraft}
            onSend={handleSend}
            isSending={chatMutation.isPending}
            agentName={agent.name}
          />
          {sendError ? <p className="agent-preview__error">{sendError}</p> : null}
        </section>
      </div>
    </div>
  );
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getAgent } from "../../api/agents";
import { createKnowledgebase } from "../../api/knowledgebases";
import {
  DEFAULT_KB_FORM_STATE,
  isKnowledgeBaseFormValid,
  KnowledgeBaseFormFields,
  type KnowledgeBaseFormState,
} from "../../components/agent/KnowledgeBaseForm";
import { RoutingHintField } from "../../components/agent/RoutingHintField";
import { WizardLayout } from "../../components/agent/WizardLayout";

function getApiError(error: unknown): string {
  if (error && typeof error === "object" && "response" in error) {
    const detail = (error as { response?: { data?: { detail?: string | { msg?: string }[] } } }).response?.data
      ?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail) && detail[0]?.msg) {
      return detail[0].msg;
    }
    return "Request failed.";
  }
  return "Request failed.";
}

export function AddKnowledgeBasePage() {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<KnowledgeBaseFormState>(DEFAULT_KB_FORM_STATE);
  const [routingHint, setRoutingHint] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: agent, isLoading } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => getAgent(agentId!),
    enabled: Boolean(agentId),
  });

  const createMutation = useMutation({
    mutationFn: createKnowledgebase,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["knowledgebases", agentId] });
      navigate(`/agent/${agentId}`);
    },
    onError: (err) => {
      setError(getApiError(err));
    },
  });

  if (!agentId) {
    return <div className="agent-page__state">Invalid agent.</div>;
  }

  if (isLoading || !agent) {
    return <div className="agent-page__state">Loading…</div>;
  }

  function handleSubmit() {
    if (!agent || !isKnowledgeBaseFormValid(form) || !form.storageType) {
      return;
    }

    setError(null);
    createMutation.mutate({
      name: `${agent.name} knowledge base`,
      description: agent.description ?? undefined,
      storage_type: form.storageType,
      source_type: form.sourceType,
      agent_id: agentId,
      routing_hint: routingHint.trim() || null,
      website_url: form.sourceType === "website" ? form.websiteUrl.trim() : undefined,
      crawl_depth: form.sourceType === "website" ? form.crawlDepth : undefined,
      file: form.sourceType === "file" ? form.documentFile : undefined,
    });
  }

  return (
    <WizardLayout
      step={1}
      totalSteps={1}
      stepLabel="Knowledge base"
      eyebrow={agent.name.toUpperCase()}
      title="Add a knowledge base"
      subtitle="Choose a storage type and connect a website or document for this agent."
      footer={
        <>
          <Link to={`/agent/${agentId}`} className="btn">
            Cancel
          </Link>
          <button
            type="button"
            className="btn btn--primary"
            disabled={createMutation.isPending || !isKnowledgeBaseFormValid(form)}
            onClick={() => handleSubmit()}
          >
            {createMutation.isPending ? "Creating…" : "Create knowledge base"}
          </button>
        </>
      }
    >
      <div className="agent-form">
        <KnowledgeBaseFormFields form={form} onChange={setForm} />
        <RoutingHintField
          capabilityKind="knowledgebase"
          value={routingHint}
          onChange={setRoutingHint}
        />
        {error ? <p className="agent-form__error">{error}</p> : null}
      </div>
    </WizardLayout>
  );
}

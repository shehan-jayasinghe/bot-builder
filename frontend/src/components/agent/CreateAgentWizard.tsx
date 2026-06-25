import { useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { createAgent } from "../../api/agents";
import { createKnowledgebase } from "../../api/knowledgebases";
import { AGENT_TYPES, INDUSTRIES, SAMPLE_QUESTIONS } from "../../constants/agents";
import { CRAWL_DEPTH_OPTIONS, SOURCE_TYPES, STORAGE_TYPES } from "../../constants/knowledgebase";
import type { AgentType, Industry } from "../../types/agent";
import type { SourceType, StorageType } from "../../types/knowledgebase";
import { WizardLayout } from "./WizardLayout";

const BUILD_STEPS = [
  "Initializing agent runtime",
  "Configuring system prompt",
  "Configuring language model",
  "Building knowledge index",
  "Generating API endpoint",
  "Connecting to Agent",
  "Extracting website content",
] as const;

type WizardStep = "basics" | "type" | "configure" | "building" | "success";

type FormState = {
  name: string;
  industry: Industry | "";
  agentType: AgentType | "";
  storageType: StorageType | "";
  sourceType: SourceType | "";
  websiteUrl: string;
  crawlDepth: number;
  documentFile: File | null;
};

function getApiError(error: unknown): string {
  if (error && typeof error === "object" && "response" in error) {
    const detail = (error as { response?: { data?: { detail?: string | { msg?: string }[] } } }).response?.data?.detail;
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

function isConfigureValid(form: FormState): boolean {
  if (!form.storageType || !form.sourceType) {
    return false;
  }
  if (form.sourceType === "website") {
    return form.websiteUrl.trim().length > 0;
  }
  return form.documentFile !== null;
}

export function CreateAgentWizard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [step, setStep] = useState<WizardStep>("basics");
  const [form, setForm] = useState<FormState>({
    name: "",
    industry: "",
    agentType: "",
    storageType: "",
    sourceType: "website",
    websiteUrl: "",
    crawlDepth: 2,
    documentFile: null,
  });
  const [buildProgress, setBuildProgress] = useState(0);
  const [activeBuildStep, setActiveBuildStep] = useState(0);
  const [createdAgentId, setCreatedAgentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isBuilding, setIsBuilding] = useState(false);

  const selectedType = useMemo(
    () => AGENT_TYPES.find((item) => item.value === form.agentType),
    [form.agentType],
  );

  function runBuildAnimation() {
    setStep("building");
    setBuildProgress(0);
    setActiveBuildStep(0);

    let progress = 0;
    const interval = window.setInterval(() => {
      progress += 1;
      setBuildProgress(progress);
      setActiveBuildStep(Math.min(Math.floor((progress / 100) * BUILD_STEPS.length), BUILD_STEPS.length - 1));

      if (progress >= 100) {
        window.clearInterval(interval);
        window.setTimeout(() => setStep("success"), 400);
      }
    }, 80);
  }

  async function handleBuild() {
    if (!form.name || !form.industry || !form.agentType || !isConfigureValid(form)) {
      return;
    }

    setError(null);
    setIsBuilding(true);

    const typeOption = AGENT_TYPES.find((item) => item.value === form.agentType);

    try {
      const agent = await createAgent({
        name: form.name,
        industry: form.industry,
        agent_type: form.agentType,
        description: typeOption?.description,
      });

      await queryClient.invalidateQueries({ queryKey: ["agents"] });
      setCreatedAgentId(agent.id);

      await createKnowledgebase({
        name: `${form.name} knowledge base`,
        description: typeOption?.description,
        storage_type: form.storageType as StorageType,
        source_type: form.sourceType as SourceType,
        agent_id: agent.id,
        website_url: form.sourceType === "website" ? form.websiteUrl.trim() : undefined,
        crawl_depth: form.sourceType === "website" ? form.crawlDepth : undefined,
        file: form.sourceType === "file" ? form.documentFile : undefined,
      });

      runBuildAnimation();
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setIsBuilding(false);
    }
  }

  if (step === "basics") {
    return (
      <WizardLayout
        step={0}
        totalSteps={5}
        centered
        eyebrow="WELCOME TO BOTCIRCUITS"
        title="Let's set up your agent 🚀"
        subtitle="Tell us about your application so we can tailor the perfect AI agent for you."
        footer={
          <button
            type="button"
            className="btn btn--primary agent-wizard__continue"
            disabled={!form.name.trim() || !form.industry}
            onClick={() => setStep("type")}
          >
            Continue &gt;
          </button>
        }
      >
        <div className="agent-form">
          <label className="agent-form__field">
            <span>APPLICATION NAME</span>
            <input
              value={form.name}
              onChange={(e) => setForm((current) => ({ ...current, name: e.target.value }))}
              placeholder="abc bank"
            />
          </label>
          <label className="agent-form__field">
            <span>WHAT&apos;S YOUR INDUSTRY?</span>
            <select
              value={form.industry}
              onChange={(e) => setForm((current) => ({ ...current, industry: e.target.value as Industry }))}
            >
              <option value="">Select your industry</option>
              {INDUSTRIES.map((industry) => (
                <option key={industry.value} value={industry.value}>
                  {industry.emoji} {industry.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </WizardLayout>
    );
  }

  if (step === "type") {
    return (
      <WizardLayout
        step={2}
        totalSteps={5}
        stepLabel="Agent Type"
        eyebrow="CHOOSE YOUR AGENT"
        title="What kind of agent do you need?"
        subtitle="Pick the agent that best fits your use case."
        footer={
          <>
            <button type="button" className="btn" onClick={() => setStep("basics")}>
              Back
            </button>
            <button
              type="button"
              className="btn btn--primary"
              disabled={!form.agentType}
              onClick={() => setStep("configure")}
            >
              Continue &gt;
            </button>
          </>
        }
      >
        <div className="agent-type-list">
          {AGENT_TYPES.map((type) => (
            <button
              key={type.value}
              type="button"
              className={`agent-type-card ${form.agentType === type.value ? "agent-type-card--selected" : ""}`}
              onClick={() => setForm((current) => ({ ...current, agentType: type.value }))}
            >
              <span className="agent-type-card__icon">{type.icon}</span>
              <div>
                <strong>{type.label}</strong>
                <p>{type.description}</p>
              </div>
            </button>
          ))}
        </div>
      </WizardLayout>
    );
  }

  if (step === "configure") {
    return (
      <WizardLayout
        step={3}
        totalSteps={5}
        stepLabel="Configure"
        eyebrow={selectedType?.label.toUpperCase()}
        title="Here's what your agent will do."
        subtitle="Choose a knowledge base type and connect your content."
        footer={
          <>
            <button type="button" className="btn" onClick={() => setStep("type")}>
              Back
            </button>
            <button
              type="button"
              className="btn btn--primary"
              disabled={isBuilding || !isConfigureValid(form)}
              onClick={() => void handleBuild()}
            >
              {isBuilding ? "Building…" : "Build my agent ✨"}
            </button>
          </>
        }
      >
        <div className="agent-form">
          <div className="agent-form__section">
            <span className="agent-form__label">AGENT CAPABILITIES</span>
            <ul className="agent-capability-list">
              {selectedType?.capabilities.map((capability) => (
                <li key={capability}>
                  <span className="agent-capability-list__check">✓</span>
                  {capability}
                </li>
              ))}
            </ul>
          </div>

          <div className="agent-form__section">
            <span className="agent-form__label">KNOWLEDGE BASE TYPE *</span>
            <div className="kb-storage-grid">
              {STORAGE_TYPES.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`kb-storage-card ${form.storageType === option.value ? "kb-storage-card--selected" : ""}`}
                  onClick={() => setForm((current) => ({ ...current, storageType: option.value }))}
                >
                  <span className="kb-storage-card__icon">{option.icon}</span>
                  <strong>{option.label}</strong>
                  <p>{option.description}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="agent-form__section">
            <span className="agent-form__label">CONTENT SOURCE *</span>
            <div className="kb-source-toggle">
              {SOURCE_TYPES.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`kb-source-toggle__btn ${form.sourceType === option.value ? "kb-source-toggle__btn--active" : ""}`}
                  onClick={() =>
                    setForm((current) => ({
                      ...current,
                      sourceType: option.value,
                      websiteUrl: option.value === "website" ? current.websiteUrl : "",
                      documentFile: option.value === "file" ? current.documentFile : null,
                    }))
                  }
                >
                  {option.label}
                </button>
              ))}
            </div>
            <small>
              {SOURCE_TYPES.find((item) => item.value === form.sourceType)?.description}
            </small>
          </div>

          {form.sourceType === "website" ? (
            <>
              <label className="agent-form__field">
                <span>WEBSITE URL *</span>
                <input
                  type="url"
                  value={form.websiteUrl}
                  onChange={(e) => setForm((current) => ({ ...current, websiteUrl: e.target.value }))}
                  placeholder="https://www.yourcompany.com/help"
                />
                <small>We&apos;ll crawl this site and index pages for your agent.</small>
              </label>
              <label className="agent-form__field">
                <span>CRAWL DEPTH *</span>
                <select
                  value={form.crawlDepth}
                  onChange={(e) =>
                    setForm((current) => ({ ...current, crawlDepth: Number(e.target.value) }))
                  }
                >
                  {CRAWL_DEPTH_OPTIONS.map((depth) => (
                    <option key={depth} value={depth}>
                      {depth} {depth === 1 ? "level" : "levels"}
                    </option>
                  ))}
                </select>
                <small>How many link levels to follow from the starting URL.</small>
              </label>
            </>
          ) : (
            <label className="agent-form__field">
              <span>DOCUMENT *</span>
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md,.csv"
                onChange={(e) =>
                  setForm((current) => ({
                    ...current,
                    documentFile: e.target.files?.[0] ?? null,
                  }))
                }
              />
              <small>Upload PDF, DOCX, or TXT. Max size depends on your server limits.</small>
              {form.documentFile ? <small>Selected: {form.documentFile.name}</small> : null}
            </label>
          )}

          {error ? <p className="agent-form__error">{error}</p> : null}
        </div>
      </WizardLayout>
    );
  }

  if (step === "building") {
    const isExtracting = activeBuildStep === BUILD_STEPS.length - 1;

    return (
      <WizardLayout
        step={4}
        totalSteps={5}
        centered
        title={isExtracting ? "Extracting website content." : "Building your agent."}
        subtitle={
          isExtracting
            ? "Crawling and indexing your content. This may take a few minutes."
            : "This usually takes under 10 seconds."
        }
      >
        <div className="agent-build">
          <div className="agent-build__progress-row">
            <span>Progress</span>
            <span>{buildProgress}%</span>
          </div>
          <div className="agent-build__bar">
            <div className="agent-build__bar-fill" style={{ width: `${buildProgress}%` }} />
          </div>
          <ul className="agent-build__steps">
            {BUILD_STEPS.map((label, index) => {
              const isDone = index < activeBuildStep;
              const isActive = index === activeBuildStep;
              return (
                <li
                  key={label}
                  className={`agent-build__step ${isDone ? "agent-build__step--done" : ""} ${
                    isActive ? "agent-build__step--active" : ""
                  }`}
                >
                  <span>{isDone ? "✓" : isActive ? "◌" : "○"}</span>
                  <div>
                    <strong>{label}</strong>
                    {isActive && label === "Extracting website content" && form.sourceType === "website" && form.websiteUrl ? (
                      <small>Crawling and indexing pages from {form.websiteUrl}</small>
                    ) : null}
                    {isActive && label === "Extracting website content" && form.sourceType === "file" && form.documentFile ? (
                      <small>Processing document {form.documentFile.name}</small>
                    ) : null}
                    {isActive && label === "Connecting to Agent" ? <small>Going live worldwide</small> : null}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      </WizardLayout>
    );
  }

  return (
    <WizardLayout
      step={5}
      totalSteps={5}
      centered
      eyebrow="AGENT LIVE"
      title="Your agent is ready."
      subtitle={`${form.name} is deployed and ready to handle conversations.`}
      footer={
        <>
          <button type="button" className="btn btn--primary agent-wizard__full-btn" onClick={() => navigate(`/agent/${createdAgentId}`)}>
            Test your agent →
          </button>
          <button type="button" className="btn agent-wizard__full-btn" onClick={() => navigate("/agent")}>
            Explore the platform
          </button>
        </>
      }
    >
      <div className="agent-success">
        <div className="agent-success__section">
          <span className="agent-form__label">TRY ASKING</span>
          <div className="agent-success__questions">
            {(form.agentType ? SAMPLE_QUESTIONS[form.agentType] : []).map((question) => (
              <div key={question} className="agent-success__question">
                <span>💬</span>
                <span>{question}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="agent-success__section">
          <span className="agent-form__label">NEXT STEPS</span>
          <div className="agent-success__next-steps">
            <div className="agent-success__next-card">
              <span>🔧</span>
              <div>
                <strong>Integrate Tools</strong>
                <p>Connect APIs, CRMs, and databases to supercharge your agent.</p>
              </div>
            </div>
            <div className="agent-success__next-card">
              <span>📱</span>
              <div>
                <strong>Integrate Channels</strong>
                <p>Deploy on WhatsApp, SMS, Web Chat, Slack, and more.</p>
              </div>
            </div>
            <div className="agent-success__next-card">
              <span>🚀</span>
              <div>
                <strong>Explore &amp; Test</strong>
                <p>Test your agent, fine-tune responses, and go live.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </WizardLayout>
  );
}

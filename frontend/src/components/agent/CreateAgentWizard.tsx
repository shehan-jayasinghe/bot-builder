import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { createAgent } from "../../api/agents";
import { AGENT_TYPES, INDUSTRIES, SAMPLE_QUESTIONS } from "../../constants/agents";
import type { AgentType, Industry } from "../../types/agent";
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
  websiteUrl: string;
};

function getApiError(error: unknown): string {
  if (error && typeof error === "object" && "response" in error) {
    return (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "Request failed.";
  }
  return "Request failed.";
}

export function CreateAgentWizard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [step, setStep] = useState<WizardStep>("basics");
  const [form, setForm] = useState<FormState>({
    name: "",
    industry: "",
    agentType: "",
    websiteUrl: "",
  });
  const [buildProgress, setBuildProgress] = useState(0);
  const [activeBuildStep, setActiveBuildStep] = useState(0);
  const [createdAgentId, setCreatedAgentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedType = useMemo(
    () => AGENT_TYPES.find((item) => item.value === form.agentType),
    [form.agentType],
  );

  const createMutation = useMutation({
    mutationFn: createAgent,
    onSuccess: async (agent) => {
      await queryClient.invalidateQueries({ queryKey: ["agents"] });
      setCreatedAgentId(agent.id);
      runBuildAnimation();
    },
    onError: (err) => {
      setError(getApiError(err));
      setStep("configure");
    },
  });

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

  function handleBuild() {
    if (!form.name || !form.industry || !form.agentType) {
      return;
    }

    setError(null);
    const typeOption = AGENT_TYPES.find((item) => item.value === form.agentType);
    createMutation.mutate({
      name: form.name,
      industry: form.industry,
      agent_type: form.agentType,
      description: typeOption?.description,
    });
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
        subtitle="We'll configure your agent based on your selection."
        footer={
          <>
            <button type="button" className="btn" onClick={() => setStep("type")}>
              Back
            </button>
            <button
              type="button"
              className="btn btn--primary"
              disabled={createMutation.isPending}
              onClick={handleBuild}
            >
              Build my agent ✨
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

          <label className="agent-form__field">
            <span>YOUR WEBSITE *</span>
            <input
              value={form.websiteUrl}
              onChange={(e) => setForm((current) => ({ ...current, websiteUrl: e.target.value }))}
              placeholder="https://www.yourcompany.com"
            />
            <small>We&apos;ll use your website to train your agent with relevant information about your business.</small>
          </label>

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
            ? "Crawling and indexing your website. This may take a few minutes."
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
                    {isActive && label === "Extracting website content" && form.websiteUrl ? (
                      <small>Crawling and indexing pages from {form.websiteUrl}</small>
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

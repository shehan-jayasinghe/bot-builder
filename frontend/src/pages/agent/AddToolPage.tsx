import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getAgent } from "../../api/agents";
import { createConnector, listConnectorTypes } from "../../api/connectors";
import { listExecutors } from "../../api/executors";
import { createTool } from "../../api/tools";
import { WizardLayout } from "../../components/agent/WizardLayout";
import {
  defaultConfigValues,
  isToolConfigValid,
  parseToolConfig,
  ToolConfigFields,
} from "../../components/agent/ToolConfigFields";
import { RoutingHintField } from "../../components/agent/RoutingHintField";
import { CONNECTOR_TYPE_ICONS } from "../../constants/tools";
import type { ConnectorType, HttpAuthType } from "../../types/connector";
import type { ExecutorCatalogItem, ExecutorName } from "../../types/executor";
import { getApiError } from "../../utils/apiError";

const TOTAL_STEPS = 4;

const STEP_LABELS = ["Connection type", "Connector", "Executor", "Review"];

type ConnectorFormState = {
  name: string;
  mongoUri: string;
  mongoDatabase: string;
  httpBaseUrl: string;
  httpAuthType: HttpAuthType;
  httpTokenUrl: string;
  httpClientId: string;
  httpClientSecret: string;
  httpScope: string;
  httpAuthToken: string;
  httpAuthUsername: string;
  httpAuthPassword: string;
  httpApiKeyHeader: string;
};

const DEFAULT_CONNECTOR_FORM: ConnectorFormState = {
  name: "",
  mongoUri: "",
  mongoDatabase: "",
  httpBaseUrl: "",
  httpAuthType: "oauth2_client_credentials",
  httpTokenUrl: "",
  httpClientId: "",
  httpClientSecret: "",
  httpScope: "",
  httpAuthToken: "",
  httpAuthUsername: "",
  httpAuthPassword: "",
  httpApiKeyHeader: "X-API-Key",
};

function isSnakeCaseName(value: string): boolean {
  return /^[a-z][a-z0-9_]*$/.test(value);
}

function buildConnectorConfig(type: ConnectorType, form: ConnectorFormState): Record<string, unknown> {
  if (type === "mongo") {
    return {
      uri: form.mongoUri.trim(),
      database: form.mongoDatabase.trim(),
    };
  }

  const config: Record<string, unknown> = {
    base_url: form.httpBaseUrl.trim(),
    auth_type: form.httpAuthType,
  };

  if (form.httpAuthType === "oauth2_client_credentials") {
    config.token_url = form.httpTokenUrl.trim();
    config.client_id = form.httpClientId.trim();
    config.client_secret = form.httpClientSecret.trim();
    config.grant_type = "client_credentials";
    if (form.httpScope.trim()) {
      config.scope = form.httpScope.trim();
    }
  }
  if (form.httpAuthType === "bearer" || form.httpAuthType === "api_key") {
    config.auth_token = form.httpAuthToken.trim();
  }
  if (form.httpAuthType === "basic") {
    config.auth_username = form.httpAuthUsername.trim();
    config.auth_password = form.httpAuthPassword;
  }
  if (form.httpAuthType === "api_key") {
    config.api_key_header = form.httpApiKeyHeader.trim() || "X-API-Key";
  }

  return config;
}

function isConnectorFormValid(type: ConnectorType, form: ConnectorFormState): boolean {
  if (!form.name.trim()) {
    return false;
  }
  if (type === "mongo") {
    return form.mongoUri.trim().length > 0 && form.mongoDatabase.trim().length > 0;
  }
  if (!form.httpBaseUrl.trim()) {
    return false;
  }
  if (form.httpAuthType === "oauth2_client_credentials") {
    return (
      form.httpTokenUrl.trim().length > 0 &&
      form.httpClientId.trim().length > 0 &&
      form.httpClientSecret.trim().length > 0
    );
  }
  if (form.httpAuthType === "bearer" || form.httpAuthType === "api_key") {
    return form.httpAuthToken.trim().length > 0;
  }
  if (form.httpAuthType === "basic") {
    return form.httpAuthUsername.trim().length > 0 && form.httpAuthPassword.length > 0;
  }
  return true;
}

export function AddToolPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [step, setStep] = useState(1);
  const [connectorType, setConnectorType] = useState<ConnectorType | "">("");
  const [connectorForm, setConnectorForm] = useState<ConnectorFormState>(DEFAULT_CONNECTOR_FORM);
  const [connectorId, setConnectorId] = useState<string | null>(null);
  const [connectionTested, setConnectionTested] = useState(false);
  const [selectedExecutor, setSelectedExecutor] = useState<ExecutorName | "">("");
  const [configValues, setConfigValues] = useState<Record<string, string>>({});
  const [toolName, setToolName] = useState("");
  const [toolDescription, setToolDescription] = useState("");
  const [routingHint, setRoutingHint] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: agent, isLoading: agentLoading } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => getAgent(agentId!),
    enabled: Boolean(agentId),
  });

  const { data: connectorTypesData, isLoading: typesLoading } = useQuery({
    queryKey: ["connector-types"],
    queryFn: listConnectorTypes,
  });

  const { data: executorsData, isLoading: executorsLoading } = useQuery({
    queryKey: ["executors"],
    queryFn: listExecutors,
  });

  const testConnectionMutation = useMutation({
    mutationFn: createConnector,
    onSuccess: (connector) => {
      setConnectorId(connector.id);
      setConnectionTested(true);
      setError(null);
    },
    onError: (err) => {
      setConnectionTested(false);
      setConnectorId(null);
      setError(getApiError(err));
    },
  });

  const createToolMutation = useMutation({
    mutationFn: (payload: Parameters<typeof createTool>[1]) => createTool(agentId!, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tools", agentId] });
      await queryClient.invalidateQueries({ queryKey: ["capability-catalog-preview", agentId] });
      navigate(`/agent/${agentId}`);
    },
    onError: (err) => {
      setError(getApiError(err));
    },
  });

  const connectorTypes = connectorTypesData?.items.filter((item) => item.mvp) ?? [];

  const compatibleExecutors = useMemo(() => {
    if (!connectorType || !executorsData) {
      return [];
    }
    return executorsData.items.filter((item) => item.mvp && item.connector_type === connectorType);
  }, [connectorType, executorsData]);

  const selectedExecutorItem = useMemo<ExecutorCatalogItem | null>(() => {
    if (!selectedExecutor) {
      return null;
    }
    return compatibleExecutors.find((item) => item.executor === selectedExecutor) ?? null;
  }, [compatibleExecutors, selectedExecutor]);

  if (!agentId) {
    return <div className="agent-page__state">Invalid agent.</div>;
  }

  if (agentLoading || typesLoading || !agent) {
    return <div className="agent-page__state">Loading…</div>;
  }

  function resetConnectorState() {
    setConnectorId(null);
    setConnectionTested(false);
  }

  function handleSelectConnectorType(type: ConnectorType) {
    setConnectorType(type);
    resetConnectorState();
    setConnectorForm(DEFAULT_CONNECTOR_FORM);
    setSelectedExecutor("");
    setConfigValues({});
    setError(null);
  }

  function handleSelectExecutor(executor: ExecutorName) {
    const item = compatibleExecutors.find((entry) => entry.executor === executor);
    if (!item) {
      return;
    }
    setSelectedExecutor(executor);
    setConfigValues(defaultConfigValues(item));
    setError(null);
  }

  function handleTestConnection() {
    if (!connectorType || !isConnectorFormValid(connectorType, connectorForm)) {
      return;
    }

    setError(null);
    testConnectionMutation.mutate({
      name: connectorForm.name.trim(),
      type: connectorType,
      config: buildConnectorConfig(connectorType, connectorForm),
      test_connection: true,
    });
  }

  function handleCreateTool() {
    if (!selectedExecutorItem || !connectorId) {
      return;
    }

    const { config, error: configError } = parseToolConfig(selectedExecutorItem, configValues);
    if (configError || !config) {
      setError(configError);
      return;
    }

    if (!isSnakeCaseName(toolName.trim())) {
      setError("Tool name must be lowercase snake_case (e.g. customer_lookup).");
      return;
    }

    if (!toolDescription.trim()) {
      setError("Description is required.");
      return;
    }

    setError(null);
    createToolMutation.mutate({
      name: toolName.trim(),
      description: toolDescription.trim(),
      executor: selectedExecutorItem.executor,
      connector_id: connectorId,
      config,
      routing_hint: routingHint.trim() || null,
    });
  }

  function canContinueFromStep(current: number): boolean {
    if (current === 1) {
      return Boolean(connectorType);
    }
    if (current === 2) {
      if (!connectorType) {
        return false;
      }
      return (
        isConnectorFormValid(connectorType, connectorForm) &&
        connectionTested &&
        Boolean(connectorId)
      );
    }
    if (current === 3) {
      return Boolean(selectedExecutorItem) && isToolConfigValid(selectedExecutorItem!, configValues);
    }
    return (
      isSnakeCaseName(toolName.trim()) &&
      toolDescription.trim().length > 0 &&
      Boolean(selectedExecutorItem) &&
      Boolean(connectorId)
    );
  }

  const stepSubtitle =
    step === 1
      ? "Choose how this tool connects to your data or API."
      : step === 2
        ? "Configure the connection and verify it works before continuing."
        : step === 3
          ? "Pick what the tool does and set executor parameters."
          : "Name the tool and review before creating.";

  const footer =
    step < TOTAL_STEPS ? (
      <>
        {step > 1 ? (
          <button
            type="button"
            className="btn"
            onClick={() => {
              setError(null);
              setStep((value) => value - 1);
            }}
          >
            Back
          </button>
        ) : (
          <Link to={`/agent/${agentId}`} className="btn">
            Cancel
          </Link>
        )}
        <button
          type="button"
          className="btn btn--primary"
          disabled={!canContinueFromStep(step)}
          onClick={() => {
            setError(null);
            setStep((value) => value + 1);
          }}
        >
          Continue
        </button>
      </>
    ) : (
      <button
        type="button"
        className="btn btn--primary"
        disabled={createToolMutation.isPending || !canContinueFromStep(step)}
        onClick={() => handleCreateTool()}
      >
        {createToolMutation.isPending ? "Creating…" : "Create tool"}
      </button>
    );

  return (
    <WizardLayout
      step={step}
      totalSteps={TOTAL_STEPS}
      stepLabel={STEP_LABELS[step - 1]}
      eyebrow={agent.name.toUpperCase()}
      title="Add a tool"
      subtitle={stepSubtitle}
      footer={footer}
    >
      {step === 1 ? (
        <div className="agent-form">
          <div className="agent-form__section">
            <span className="agent-form__label">CONNECTION TYPE *</span>
            <div className="kb-storage-grid">
              {connectorTypes.map((item) => (
                <button
                  key={item.type}
                  type="button"
                  className={`kb-storage-card ${connectorType === item.type ? "kb-storage-card--selected" : ""}`}
                  onClick={() => handleSelectConnectorType(item.type)}
                >
                  <span className="kb-storage-card__icon">{CONNECTOR_TYPE_ICONS[item.type]}</span>
                  <strong>{item.label}</strong>
                  <p>{item.description}</p>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : null}

      {step === 2 && connectorType ? (
        <div className="agent-form">
          <label className="agent-form__field">
            <span>CONNECTOR NAME *</span>
            <input
              type="text"
              value={connectorForm.name}
              onChange={(e) => {
                resetConnectorState();
                setConnectorForm({ ...connectorForm, name: e.target.value });
              }}
              placeholder="Customer MongoDB"
            />
          </label>

          {connectorType === "mongo" ? (
            <>
              <label className="agent-form__field">
                <span>MONGODB URI *</span>
                <input
                  type="text"
                  value={connectorForm.mongoUri}
                  onChange={(e) => {
                    resetConnectorState();
                    setConnectorForm({ ...connectorForm, mongoUri: e.target.value });
                  }}
                  placeholder="mongodb+srv://user:pass@cluster.mongodb.net"
                />
              </label>
              <label className="agent-form__field">
                <span>DATABASE *</span>
                <input
                  type="text"
                  value={connectorForm.mongoDatabase}
                  onChange={(e) => {
                    resetConnectorState();
                    setConnectorForm({ ...connectorForm, mongoDatabase: e.target.value });
                  }}
                  placeholder="production"
                />
              </label>
            </>
          ) : (
            <>
              <label className="agent-form__field">
                <span>BASE URL *</span>
                <input
                  type="url"
                  value={connectorForm.httpBaseUrl}
                  onChange={(e) => {
                    resetConnectorState();
                    setConnectorForm({ ...connectorForm, httpBaseUrl: e.target.value });
                  }}
                  placeholder="https://api.example.com"
                />
              </label>
              <label className="agent-form__field">
                <span>AUTH TYPE</span>
                <select
                  value={connectorForm.httpAuthType}
                  onChange={(e) => {
                    resetConnectorState();
                    setConnectorForm({
                      ...connectorForm,
                      httpAuthType: e.target.value as HttpAuthType,
                    });
                  }}
                >
                  <option value="oauth2_client_credentials">OAuth2 client credentials</option>
                  <option value="none">None</option>
                  <option value="api_key">API key header</option>
                  <option value="basic">Basic</option>
                  <option value="bearer">Static bearer token (dev only)</option>
                </select>
              </label>
              {connectorForm.httpAuthType === "oauth2_client_credentials" ? (
                <>
                  <label className="agent-form__field">
                    <span>TOKEN URL *</span>
                    <input
                      type="url"
                      value={connectorForm.httpTokenUrl}
                      onChange={(e) => {
                        resetConnectorState();
                        setConnectorForm({ ...connectorForm, httpTokenUrl: e.target.value });
                      }}
                      placeholder="https://idp.example.com/auth/realms/app/protocol/openid-connect/token"
                    />
                    <small>Where the platform requests an access token (Keycloak, Auth0, etc.).</small>
                  </label>
                  <label className="agent-form__field">
                    <span>CLIENT ID *</span>
                    <input
                      type="text"
                      value={connectorForm.httpClientId}
                      onChange={(e) => {
                        resetConnectorState();
                        setConnectorForm({ ...connectorForm, httpClientId: e.target.value });
                      }}
                    />
                  </label>
                  <label className="agent-form__field">
                    <span>CLIENT SECRET *</span>
                    <input
                      type="password"
                      value={connectorForm.httpClientSecret}
                      onChange={(e) => {
                        resetConnectorState();
                        setConnectorForm({ ...connectorForm, httpClientSecret: e.target.value });
                      }}
                    />
                  </label>
                  <label className="agent-form__field">
                    <span>SCOPE</span>
                    <input
                      type="text"
                      value={connectorForm.httpScope}
                      onChange={(e) => {
                        resetConnectorState();
                        setConnectorForm({ ...connectorForm, httpScope: e.target.value });
                      }}
                      placeholder="optional"
                    />
                  </label>
                </>
              ) : null}
              {connectorForm.httpAuthType === "bearer" || connectorForm.httpAuthType === "api_key" ? (
                <label className="agent-form__field">
                  <span>TOKEN *</span>
                  <input
                    type="password"
                    value={connectorForm.httpAuthToken}
                    onChange={(e) => {
                      resetConnectorState();
                      setConnectorForm({ ...connectorForm, httpAuthToken: e.target.value });
                    }}
                  />
                </label>
              ) : null}
              {connectorForm.httpAuthType === "basic" ? (
                <>
                  <label className="agent-form__field">
                    <span>USERNAME *</span>
                    <input
                      type="text"
                      value={connectorForm.httpAuthUsername}
                      onChange={(e) => {
                        resetConnectorState();
                        setConnectorForm({ ...connectorForm, httpAuthUsername: e.target.value });
                      }}
                    />
                  </label>
                  <label className="agent-form__field">
                    <span>PASSWORD *</span>
                    <input
                      type="password"
                      value={connectorForm.httpAuthPassword}
                      onChange={(e) => {
                        resetConnectorState();
                        setConnectorForm({ ...connectorForm, httpAuthPassword: e.target.value });
                      }}
                    />
                  </label>
                </>
              ) : null}
              {connectorForm.httpAuthType === "api_key" ? (
                <label className="agent-form__field">
                  <span>API KEY HEADER</span>
                  <input
                    type="text"
                    value={connectorForm.httpApiKeyHeader}
                    onChange={(e) => {
                      resetConnectorState();
                      setConnectorForm({ ...connectorForm, httpApiKeyHeader: e.target.value });
                    }}
                  />
                </label>
              ) : null}
            </>
          )}

          <div className="agent-kb-form__actions">
            <button
              type="button"
              className="btn btn--ghost"
              disabled={
                testConnectionMutation.isPending ||
                !isConnectorFormValid(connectorType, connectorForm)
              }
              onClick={() => handleTestConnection()}
            >
              {testConnectionMutation.isPending
                ? "Testing…"
                : connectionTested
                  ? "Connection verified"
                  : "Test connection"}
            </button>
            {connectionTested ? (
              <span className="agent-status agent-status--active">Ready to continue</span>
            ) : null}
          </div>
        </div>
      ) : null}

      {step === 3 ? (
        <div className="agent-form">
          {executorsLoading ? (
            <p className="agent-kb-panel__loading">Loading executors…</p>
          ) : (
            <>
              <div className="agent-form__section">
                <span className="agent-form__label">EXECUTOR *</span>
                <div className="kb-storage-grid kb-storage-grid--compact">
                  {compatibleExecutors.map((item) => (
                    <button
                      key={item.executor}
                      type="button"
                      className={`kb-storage-card ${selectedExecutor === item.executor ? "kb-storage-card--selected" : ""}`}
                      onClick={() => handleSelectExecutor(item.executor)}
                    >
                      <strong>{item.label}</strong>
                      <p>{item.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {selectedExecutorItem ? (
                <div className="agent-form__section">
                  <span className="agent-form__label">EXECUTOR CONFIG *</span>
                  <ToolConfigFields
                    executor={selectedExecutorItem}
                    values={configValues}
                    onChange={setConfigValues}
                  />
                </div>
              ) : null}
            </>
          )}
        </div>
      ) : null}

      {step === 4 && selectedExecutorItem ? (
        <div className="agent-form">
          <label className="agent-form__field">
            <span>TOOL NAME *</span>
            <input
              type="text"
              value={toolName}
              onChange={(e) => setToolName(e.target.value)}
              placeholder="customer_lookup"
            />
            <small>Lowercase snake_case — used when the LLM calls this tool.</small>
          </label>

          <label className="agent-form__field">
            <span>DESCRIPTION *</span>
            <textarea
              rows={3}
              value={toolDescription}
              onChange={(e) => setToolDescription(e.target.value)}
              placeholder="Look up a customer by ID and return loyalty points."
            />
            <small>The LLM uses this to decide when to invoke the tool.</small>
          </label>

          <RoutingHintField capabilityKind="tool" value={routingHint} onChange={setRoutingHint} />

          <div className="agent-form__section">
            <span className="agent-form__label">REVIEW</span>
            <dl className="agent-meta-list">
              <div>
                <dt>Connection</dt>
                <dd>{connectorType}</dd>
              </div>
              <div>
                <dt>Connector</dt>
                <dd>{connectorForm.name || "—"}</dd>
              </div>
              <div>
                <dt>Executor</dt>
                <dd>{selectedExecutorItem.label}</dd>
              </div>
              <div>
                <dt>Config</dt>
                <dd>
                  <pre className="agent-panel__textarea" style={{ minHeight: "6rem", fontSize: "0.75rem" }}>
                    {JSON.stringify(parseToolConfig(selectedExecutorItem, configValues).config ?? {}, null, 2)}
                  </pre>
                </dd>
              </div>
            </dl>
          </div>
        </div>
      ) : null}

      {error ? <p className="agent-form__error">{error}</p> : null}
    </WizardLayout>
  );
}

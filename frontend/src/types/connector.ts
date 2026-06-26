export type ConnectorType = "mongo" | "http";

export type HttpAuthType =
  | "none"
  | "oauth2_client_credentials"
  | "api_key"
  | "basic"
  | "bearer";

export type ConnectorTypeCatalogItem = {
  type: ConnectorType;
  label: string;
  description: string;
  mvp: boolean;
  config_schema: Record<string, unknown>;
  compatible_executors: string[];
};

export type ListConnectorTypesResponse = {
  items: ConnectorTypeCatalogItem[];
};

export type Connector = {
  id: string;
  name: string;
  description?: string | null;
  type: ConnectorType;
  config: Record<string, unknown>;
  status: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
};

export type CreateConnectorPayload = {
  name: string;
  description?: string;
  type: ConnectorType;
  config: Record<string, unknown>;
  test_connection?: boolean;
};

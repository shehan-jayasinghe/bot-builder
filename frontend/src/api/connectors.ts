import type {
  Connector,
  CreateConnectorPayload,
  ListConnectorTypesResponse,
} from "../types/connector";
import { api } from "./client";

export async function listConnectorTypes(): Promise<ListConnectorTypesResponse> {
  const { data } = await api.get<ListConnectorTypesResponse>("/connector-types");
  return data;
}

export async function createConnector(payload: CreateConnectorPayload): Promise<Connector> {
  const { data } = await api.post<Connector>("/connectors", payload);
  return data;
}

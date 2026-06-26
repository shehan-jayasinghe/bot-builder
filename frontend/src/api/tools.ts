import type { CreateToolPayload, ListToolsResponse, Tool, UpdateToolPayload } from "../types/tool";
import { api } from "./client";

export async function listTools(params?: {
  agent_id?: string;
  executor?: string;
  status?: string;
}): Promise<ListToolsResponse> {
  const { data } = await api.get<ListToolsResponse>("/tools", { params });
  return data;
}

export async function listToolsByAgent(
  agentId: string,
  params?: { executor?: string; status?: string },
): Promise<ListToolsResponse> {
  const { data } = await api.get<ListToolsResponse>(`/agents/${agentId}/tools`, { params });
  return data;
}

export async function createTool(agentId: string, payload: CreateToolPayload): Promise<Tool> {
  const { data } = await api.post<Tool>(`/agents/${agentId}/tools`, payload);
  return data;
}

export async function updateTool(toolId: string, payload: UpdateToolPayload): Promise<Tool> {
  const { data } = await api.patch<Tool>(`/tools/${toolId}`, payload);
  return data;
}

import type { CreateSubAgentPayload, ListSubAgentsResponse, SubAgent } from "../types/subAgent";
import { api } from "./client";

export async function listSubAgents(
  agentId: string,
  status?: string,
): Promise<ListSubAgentsResponse> {
  const { data } = await api.get<ListSubAgentsResponse>(`/agents/${agentId}/sub-agents`, {
    params: status ? { status } : undefined,
  });
  return data;
}

export async function createSubAgent(
  agentId: string,
  payload: CreateSubAgentPayload,
): Promise<SubAgent> {
  const { data } = await api.post<SubAgent>(`/agents/${agentId}/sub-agents`, payload);
  return data;
}

export async function getSubAgent(agentId: string, subAgentId: string): Promise<SubAgent> {
  const { data } = await api.get<SubAgent>(`/agents/${agentId}/sub-agents/${subAgentId}`);
  return data;
}

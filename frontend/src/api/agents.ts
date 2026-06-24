import type {
  Agent,
  CreateAgentRequest,
  ListAgentsResponse,
} from "../types/agent";
import { api } from "./client";

export async function listAgents(status?: string): Promise<ListAgentsResponse> {
  const { data } = await api.get<ListAgentsResponse>("/agents", {
    params: status ? { status } : undefined,
  });
  return data;
}

export async function getAgent(agentId: string): Promise<Agent> {
  const { data } = await api.get<Agent>(`/agents/${agentId}`);
  return data;
}

export async function createAgent(payload: CreateAgentRequest): Promise<Agent> {
  const { data } = await api.post<Agent>("/agents", payload);
  return data;
}

export type { Agent, AgentListItem, CreateAgentRequest, Industry } from "../types/agent";

import type {
  CreateWorkflowPayload,
  ListWorkflowsResponse,
  UpdateWorkflowPayload,
  Workflow,
} from "../types/workflow";
import { api } from "./client";

export async function listWorkflows(params?: {
  status?: string;
  agent_id?: string;
}): Promise<ListWorkflowsResponse> {
  const { data } = await api.get<ListWorkflowsResponse>("/workflows", { params });
  return data;
}

export async function createWorkflow(payload: CreateWorkflowPayload = {}): Promise<Workflow> {
  const { data } = await api.post<Workflow>("/workflows", payload);
  return data;
}

export async function getWorkflow(workflowId: string): Promise<Workflow> {
  const { data } = await api.get<Workflow>(`/workflows/${workflowId}`);
  return data;
}

export async function updateWorkflow(workflowId: string, payload: UpdateWorkflowPayload): Promise<Workflow> {
  const { data } = await api.patch<Workflow>(`/workflows/${workflowId}`, payload);
  return data;
}

export async function publishWorkflow(workflowId: string): Promise<Workflow> {
  const { data } = await api.post<Workflow>(`/workflows/${workflowId}/publish`);
  return data;
}

import type {
  PreviewChatRequest,
  PreviewChatResponse,
  PreviewTraceResponse,
  RuntimeGraphResponse,
} from "../types/preview";
import { api } from "./client";

export async function getRuntimeGraph(agentId: string): Promise<RuntimeGraphResponse> {
  const { data } = await api.get<RuntimeGraphResponse>(`/agents/${agentId}/runtime-graph`);
  return data;
}

export async function previewChat(
  agentId: string,
  payload: PreviewChatRequest,
): Promise<PreviewChatResponse> {
  const { data } = await api.post<PreviewChatResponse>(`/agents/${agentId}/preview/chat`, payload);
  return data;
}

export async function getPreviewTrace(
  agentId: string,
  senderId: string,
): Promise<PreviewTraceResponse> {
  const { data } = await api.get<PreviewTraceResponse>(
    `/agents/${agentId}/preview/sessions/${encodeURIComponent(senderId)}/trace`,
  );
  return data;
}

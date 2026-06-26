import type {
  CreateKnowledgebasePayload,
  Knowledgebase,
  ListKnowledgebasesResponse,
} from "../types/knowledgebase";
import { api } from "./client";

export async function listKnowledgebases(params?: {
  agent_id?: string;
  status?: string;
}): Promise<ListKnowledgebasesResponse> {
  const { data } = await api.get<ListKnowledgebasesResponse>("/knowledgebases", { params });
  return data;
}

export async function listKnowledgebasesByAgent(
  agentId: string,
  status?: string,
): Promise<ListKnowledgebasesResponse> {
  const { data } = await api.get<ListKnowledgebasesResponse>(`/agents/${agentId}/knowledgebases`, {
    params: status ? { status } : undefined,
  });
  return data;
}

export async function createKnowledgebase(payload: CreateKnowledgebasePayload): Promise<Knowledgebase> {
  const formData = new FormData();
  formData.append("name", payload.name);
  formData.append("source_type", payload.source_type);
  formData.append("storage_type", payload.storage_type);

  if (payload.description) {
    formData.append("description", payload.description);
  }
  if (payload.agent_id) {
    formData.append("agent_id", payload.agent_id);
  }

  if (payload.source_type === "website") {
    formData.append("website_url", payload.website_url ?? "");
    formData.append("crawl_depth", String(payload.crawl_depth ?? 2));
  }

  if (payload.source_type === "file" && payload.file) {
    formData.append("file", payload.file);
  }

  const { data } = await api.post<Knowledgebase>("/knowledgebases", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function updateKnowledgebase(
  knowledgebaseId: string,
  payload: { agent_id?: string | null },
): Promise<Knowledgebase> {
  const { data } = await api.patch<Knowledgebase>(`/knowledgebases/${knowledgebaseId}`, payload);
  return data;
}

export type { CreateKnowledgebasePayload, Knowledgebase, KnowledgebaseListItem, ListKnowledgebasesResponse, SourceType, StorageType } from "../types/knowledgebase";

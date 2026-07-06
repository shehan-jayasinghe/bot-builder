import type {
  EvalDatasetCreate,
  EvalDatasetListResponse,
  EvalDatasetResponse,
  EvalDummyDatasetResponse,
  EvalRunDetailResponse,
  EvalRunListResponse,
  EvalRunRequest,
  EvalRunResponse,
} from "../types/evaluation";
import { api } from "./client";

export async function runEvaluation(
  agentId: string,
  payload: EvalRunRequest,
): Promise<EvalRunResponse> {
  const { data } = await api.post<EvalRunResponse>(`/agents/${agentId}/evaluations/run`, payload);
  return data;
}

export async function listEvalRuns(
  agentId: string,
  params?: { limit?: number; offset?: number },
): Promise<EvalRunListResponse> {
  const { data } = await api.get<EvalRunListResponse>(`/agents/${agentId}/evaluations/runs`, {
    params,
  });
  return data;
}

export async function getEvalRun(agentId: string, runId: string): Promise<EvalRunDetailResponse> {
  const { data } = await api.get<EvalRunDetailResponse>(
    `/agents/${agentId}/evaluations/runs/${runId}`,
  );
  return data;
}

export async function listEvalDatasets(agentId: string): Promise<EvalDatasetListResponse> {
  const { data } = await api.get<EvalDatasetListResponse>(`/agents/${agentId}/evaluations/datasets`);
  return data;
}

export async function createEvalDataset(
  agentId: string,
  payload: EvalDatasetCreate,
): Promise<EvalDatasetResponse> {
  const { data } = await api.post<EvalDatasetResponse>(
    `/agents/${agentId}/evaluations/datasets`,
    payload,
  );
  return data;
}

export async function getDummyEvalDataset(agentId: string): Promise<EvalDummyDatasetResponse> {
  const { data } = await api.get<EvalDummyDatasetResponse>(
    `/agents/${agentId}/evaluations/datasets/dummy`,
  );
  return data;
}

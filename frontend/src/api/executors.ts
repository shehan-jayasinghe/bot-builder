import type { ListExecutorsResponse } from "../types/executor";
import { api } from "./client";

export async function listExecutors(): Promise<ListExecutorsResponse> {
  const { data } = await api.get<ListExecutorsResponse>("/executors");
  return data;
}

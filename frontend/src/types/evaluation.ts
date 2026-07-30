export type EvalMode = "full_bot" | "rag_only";

export type EvalRunStatus = "complete" | "failed";

export type EvalScores = {
  faithfulness: number | null;
  answer_relevancy: number | null;
  context_precision: number | null;
  context_recall: number | null;
};

export type EvalThresholds = {
  faithfulness: number;
  context_precision: number;
};

export type EvalRunRequest = {
  question: string;
  ground_truth?: string | null;
  mode?: EvalMode;
  knowledge_base_names?: string[] | null;
  sender_id?: string | null;
};

export type EvalRunResponse = {
  run_id: string;
  status: EvalRunStatus;
  scores: EvalScores;
  thresholds: EvalThresholds;
  passed: boolean;
};

export type EvalRunSummary = {
  run_id: string;
  question: string | null;
  mode: EvalMode;
  status: EvalRunStatus;
  scores: EvalScores;
  thresholds: EvalThresholds;
  passed: boolean;
  created_at: string | null;
};

export type EvalRunListResponse = {
  items: EvalRunSummary[];
  total: number;
};

export type FaithfulnessClaim = {
  text: string;
  verdict: "grounded" | "hallucinated";
  source_chunk_index: number | null;
};

export type FaithfulnessDetail = {
  claims: FaithfulnessClaim[];
  score: number | null;
};

export type AnswerRelevancyDetail = {
  generated_questions: string[];
  similarities: number[];
  score: number | null;
};

export type ContextPrecisionChunk = {
  rank: number;
  text: string;
  label: "relevant" | "noise";
};

export type ContextPrecisionDetail = {
  ranked_chunks: ContextPrecisionChunk[];
  precision_at_k: number[];
  score: number | null;
};

export type ContextRecallClaim = {
  text: string;
  verdict: "supported" | "missing";
  chunk_index: number | null;
};

export type ContextRecallDetail = {
  reference_claims: ContextRecallClaim[];
  score: number | null;
};

export type TurnEvidenceRagChunk = {
  rank: number;
  text: string;
  score?: number | null;
  kb_id?: string;
  kb_name?: string;
};

export type TurnEvidence = {
  user_message: string;
  assistant_replies: string[];
  rag_retrievals: Array<{
    query: string;
    chunks: TurnEvidenceRagChunk[];
  }>;
};

export type EvalRunDetailResponse = {
  run_id: string;
  agent_id: string;
  question: string;
  ground_truth: string | null;
  mode: EvalMode;
  status: EvalRunStatus;
  turn_evidence: TurnEvidence;
  scores: EvalScores;
  thresholds: EvalThresholds;
  passed: boolean;
  faithfulness_detail: FaithfulnessDetail | null;
  answer_relevancy_detail: AnswerRelevancyDetail | null;
  context_precision_detail: ContextPrecisionDetail | null;
  context_recall_detail: ContextRecallDetail | null;
  created_at: string;
};

export type EvalDatasetCase = {
  question: string;
  ground_truth?: string | null;
  knowledge_base_names?: string[] | null;
};

export type EvalDummyDatasetResponse = {
  name: string;
  industry: string;
  agent_type: string;
  cases: EvalDatasetCase[];
};

export type EvalDatasetCreate = {
  name: string;
  cases: EvalDatasetCase[];
};

export type EvalDatasetResponse = {
  dataset_id: string;
  name: string;
  case_count: number;
};

export type EvalDatasetListItem = {
  dataset_id: string;
  name: string;
  source: string;
  case_count: number;
};

export type EvalDatasetListResponse = {
  items: EvalDatasetListItem[];
};

export type MetricTab = "faithfulness" | "answer_relevancy" | "context_precision" | "context_recall";

export type EvalCaseRow = {
  id: string;
  question: string;
  ground_truth: string;
  knowledge_base_names: string[];
  mode: EvalMode;
  lastRunId?: string;
  lastScores?: EvalScores;
  lastPassed?: boolean;
};

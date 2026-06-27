export type StorageType = "vector" | "keyword" | "graph";

export type SourceType = "website" | "file";

export type CreateKnowledgebasePayload = {
  name: string;
  description?: string | null;
  source_type: SourceType;
  storage_type: StorageType;
  agent_id?: string | null;
  routing_hint?: string | null;
  website_url?: string;
  crawl_depth?: number;
  file?: File | null;
};

export type UpdateKnowledgebasePayload = {
  agent_id?: string | null;
  routing_hint?: string | null;
};

export type Knowledgebase = {
  id: string;
  name: string;
  description?: string | null;
  organization_id: string;
  source_type: SourceType;
  storage_type: StorageType;
  website_url?: string | null;
  crawl_depth?: number | null;
  agent_id?: string | null;
  routing_hint?: string | null;
  status: string;
  job_id: string;
  job_status: string;
  created_at: string;
};

export type KnowledgebaseListItem = {
  id: string;
  name: string;
  description?: string | null;
  source_type: SourceType;
  storage_type: StorageType;
  website_url?: string | null;
  crawl_depth?: number | null;
  agent_id?: string | null;
  routing_hint?: string | null;
  status: string;
  organization_id: string;
  created_at: string;
};

export type ListKnowledgebasesResponse = {
  items: KnowledgebaseListItem[];
  total: number;
};

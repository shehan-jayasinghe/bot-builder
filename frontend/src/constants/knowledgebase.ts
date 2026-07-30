import type { SourceType, StorageType } from "../types/knowledgebase";

export type StorageTypeOption = {
  value: StorageType;
  label: string;
  description: string;
  icon: string;
};

export type SourceTypeOption = {
  value: SourceType;
  label: string;
  description: string;
};

export const STORAGE_TYPES: StorageTypeOption[] = [
  {
    value: "vector",
    label: "Vector",
    description: "Semantic search with embeddings (Qdrant). Best for natural-language Q&A.",
    icon: "🧠",
  },
  {
    value: "keyword",
    label: "Keyword",
    description: "TF-IDF keyword index. Fast exact-term matching without embeddings.",
    icon: "🔤",
  },
  {
    value: "graph",
    label: "Graph",
    description: "Entity and relationship graph (Neo4j). Best for connected knowledge.",
    icon: "🕸️",
  },
];

export const SOURCE_TYPES: SourceTypeOption[] = [
  {
    value: "website",
    label: "Website",
    description: "Crawl pages from a URL",
  },
  {
    value: "file",
    label: "Document",
    description: "Upload PDF, DOCX, or TXT",
  },
];

export const CRAWL_DEPTH_OPTIONS = [1, 2, 3, 4, 5] as const;

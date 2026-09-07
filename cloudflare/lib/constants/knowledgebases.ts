import "server-only";

export const KnowledgebaseStorageType = {
  Vector: "vector",
  Keyword: "keyword",
} as const;

export type KnowledgebaseStorageType =
  (typeof KnowledgebaseStorageType)[keyof typeof KnowledgebaseStorageType];

export const KnowledgebaseStatus = {
  Pending: "pending",
  Ready: "ready",
  Failed: "failed",
} as const;

export type KnowledgebaseStatus =
  (typeof KnowledgebaseStatus)[keyof typeof KnowledgebaseStatus];

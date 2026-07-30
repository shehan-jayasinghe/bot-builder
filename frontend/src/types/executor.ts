export type ExecutorName =
  | "mongo_find_one"
  | "mongo_find_many"
  | "mongo_insert"
  | "mongo_update"
  | "mongo_delete"
  | "mongo_aggregate"
  | "http_request";

export type ExecutorCatalogItem = {
  executor: ExecutorName;
  label: string;
  description: string;
  connector_type: string;
  mvp: boolean;
  config_schema: Record<string, { type: string; required?: boolean; values?: string[] }>;
};

export type ListExecutorsResponse = {
  items: ExecutorCatalogItem[];
};

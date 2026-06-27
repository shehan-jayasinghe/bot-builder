export const MAX_WORKFLOWS_PER_ORG = 5;

export const WORKFLOW_TOOLBAR_ITEMS = [
  { id: "message", label: "Message", nodeType: "message" as const },
  { id: "input", label: "Input", nodeType: "input" as const },
  { id: "output", label: "Output", nodeType: "output" as const },
  { id: "actions", label: "Actions", nodeType: null },
  { id: "dev", label: "Dev", nodeType: "dev" as const },
  { id: "flow", label: "Flow", nodeType: "flow" as const },
  { id: "variable", label: "Variable", nodeType: "variable" as const },
] as const;

export const WORKFLOW_ACTION_ITEMS = [
  { id: "ai_tasks", label: "AI Tasks", actionType: "ai_tasks" },
  { id: "kb_query", label: "KB Query", actionType: "kb_query" },
  { id: "integration", label: "Integration", actionType: "integration" },
  { id: "htm", label: "HTM", actionType: "htm" },
] as const;

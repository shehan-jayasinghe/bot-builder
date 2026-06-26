import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Navigate, useNavigate } from "react-router-dom";

import { createWorkflow, listWorkflows } from "../../api/workflows";
import { MAX_WORKFLOWS_PER_ORG } from "../../constants/workflows";
import { getApiError } from "../../utils/apiError";

export function WorkflowsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const workflowsQuery = useQuery({
    queryKey: ["workflows"],
    queryFn: () => listWorkflows(),
  });

  const createMutation = useMutation({
    mutationFn: createWorkflow,
    onSuccess: (workflow) => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      navigate(`/workflows/${workflow.id}`);
    },
  });

  if (workflowsQuery.isLoading) {
    return <div className="workflow-index">Loading workflows…</div>;
  }

  if (workflowsQuery.isError) {
    return (
      <div className="workflow-index workflow-index--error">
        <p>{getApiError(workflowsQuery.error)}</p>
      </div>
    );
  }

  const items = workflowsQuery.data?.items ?? [];

  if (items.length > 0) {
    return <Navigate to={`/workflows/${items[0].id}`} replace />;
  }

  const atLimit = (workflowsQuery.data?.total ?? 0) >= MAX_WORKFLOWS_PER_ORG;

  return (
    <div className="workflow-index">
      <div className="workflow-index__card">
        <h1>Workflows</h1>
        <p>Build and manage conversation flows for your agents.</p>
        {createMutation.isError ? <p className="workflow-index__error">{getApiError(createMutation.error)}</p> : null}
        <button
          type="button"
          className="workflow-index__create"
          disabled={atLimit || createMutation.isPending}
          onClick={() => createMutation.mutate({})}
        >
          {createMutation.isPending ? "Creating…" : "+ Create workflow"}
        </button>
        {atLimit ? <p className="workflow-index__hint">Maximum of {MAX_WORKFLOWS_PER_ORG} workflows per organization.</p> : null}
      </div>
    </div>
  );
}

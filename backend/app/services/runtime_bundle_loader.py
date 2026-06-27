from typing import Any

from app.domain.constants.knowledgebase_constants import KB_STATUS_READY
from app.domain.constants.sub_agent_constants import SUB_AGENT_STATUS_ACTIVE
from app.domain.constants.tool_constants import TOOL_STATUS_ACTIVE
from app.domain.constants.workflow_constants import WORKFLOW_STATUS_DRAFT, WORKFLOW_STATUS_PUBLISHED
from app.domain.models.assistant import LLMConfig
from app.domain.models.runtime_bundle import (
    RuntimeBundle,
    RuntimeKnowledgeBase,
    RuntimeOrchestrator,
    RuntimeSubAgent,
    RuntimeSubAgentParameter,
    RuntimeTool,
    RuntimeWorkflow,
)
from app.infrastructure.db.repositories.mongo.connector_repository import ConnectorRepository
from app.infrastructure.db.repositories.mongo.knowledgebase_repository import KnowledgebaseRepository
from app.infrastructure.db.repositories.mongo.sub_agent_repository import SubAgentRepository
from app.infrastructure.db.repositories.mongo.tool_repository import ToolRepository
from app.infrastructure.db.repositories.mongo.workflow_repository import WorkflowRepository


class RuntimeBundleLoader:
    def __init__(
        self,
        *,
        tool_repository: ToolRepository,
        knowledgebase_repository: KnowledgebaseRepository,
        workflow_repository: WorkflowRepository,
        sub_agent_repository: SubAgentRepository,
        connector_repository: ConnectorRepository,
    ) -> None:
        self._tool_repository = tool_repository
        self._knowledgebase_repository = knowledgebase_repository
        self._workflow_repository = workflow_repository
        self._sub_agent_repository = sub_agent_repository
        self._connector_repository = connector_repository

    async def load(self, *, agent_doc: dict[str, Any], for_preview: bool = False) -> RuntimeBundle:
        organization_id = str(agent_doc["organization_id"])
        agent_id = str(agent_doc["_id"])

        sub_agent_ids = _string_list(agent_doc.get("sub_agent_ids"))
        sub_agent_docs = await self._sub_agent_repository.find_by_ids_for_agent(
            sub_agent_ids=sub_agent_ids,
            agent_id=agent_id,
            organization_id=organization_id,
            status=SUB_AGENT_STATUS_ACTIVE,
        )

        tool_ids = _unique(
            _string_list(agent_doc.get("tool_ids"))
            + _collect_ids(sub_agent_docs, "tool_ids"),
        )
        knowledge_base_ids = _unique(
            _string_list(agent_doc.get("knowledge_base_ids"))
            + _collect_ids(sub_agent_docs, "knowledge_base_ids"),
        )

        attached_workflow_docs = await self._workflow_repository.find_all_by_organization(
            organization_id=organization_id,
            agent_id=agent_id,
            status=None if for_preview else WORKFLOW_STATUS_PUBLISHED,
        )
        workflow_ids = _unique(
            _string_list(agent_doc.get("workflow_ids"))
            + _collect_ids(sub_agent_docs, "workflow_ids")
            + [str(doc["_id"]) for doc in attached_workflow_docs],
        )

        tool_docs = await self._tool_repository.find_by_ids_for_organization(
            organization_id=organization_id,
            tool_ids=tool_ids,
            agent_id=agent_id,
            status=TOOL_STATUS_ACTIVE,
        )
        kb_docs = await self._knowledgebase_repository.find_by_ids_for_organization(
            organization_id=organization_id,
            knowledgebase_ids=knowledge_base_ids,
            status=KB_STATUS_READY,
        )
        workflow_docs = await self._workflow_repository.find_by_ids_for_organization(
            organization_id=organization_id,
            workflow_ids=workflow_ids,
            status=None if for_preview else WORKFLOW_STATUS_PUBLISHED,
            agent_id=None if for_preview else agent_id,
        )

        tools_by_id = {str(doc["_id"]): _to_runtime_tool(doc) for doc in tool_docs}
        kbs_by_id = {str(doc["_id"]): _to_runtime_kb(doc) for doc in kb_docs}
        workflows_by_id = {str(doc["_id"]): _to_runtime_workflow(doc) for doc in workflow_docs}

        orchestrator_tools = [
            tools_by_id[tool_id]
            for tool_id in _string_list(agent_doc.get("tool_ids"))
            if tool_id in tools_by_id
        ]
        orchestrator_kbs = [
            kbs_by_id[kb_id]
            for kb_id in _string_list(agent_doc.get("knowledge_base_ids"))
            if kb_id in kbs_by_id
        ]
        orchestrator_workflows = [
            workflows_by_id[workflow_id]
            for workflow_id in workflow_ids
            if workflow_id in workflows_by_id
        ]

        sub_agents = [
            _to_runtime_sub_agent(
                doc,
                tools_by_id=tools_by_id,
                kbs_by_id=kbs_by_id,
                workflows_by_id=workflows_by_id,
            )
            for doc in sub_agent_docs
        ]

        llm_config = _parse_llm_config(agent_doc.get("llm_config"))
        temperature = (
            llm_config.temperature if llm_config else float(agent_doc.get("temperature", 0.7))
        )
        max_output_tokens = (
            llm_config.max_output_tokens
            if llm_config
            else int(agent_doc.get("max_output_tokens", 1024))
        )

        orchestrator = RuntimeOrchestrator(
            id=agent_id,
            name=str(agent_doc["name"]),
            system_prompt=str(agent_doc["system_prompt"]),
            personality=_optional_str(agent_doc.get("personality")),
            tone=_optional_str(agent_doc.get("tone")),
            llm_config=llm_config,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            guardrails=list(agent_doc.get("guardrails") or []),
            tools=orchestrator_tools,
            knowledge_bases=orchestrator_kbs,
            workflows=orchestrator_workflows,
            sub_agents=sub_agents,
        )
        return RuntimeBundle(orchestrator=orchestrator, organization_id=organization_id)

    async def load_connectors_for_tools(
        self,
        *,
        organization_id: str,
        tools: list[RuntimeTool],
    ) -> dict[str, dict[str, Any]]:
        connector_ids = _unique([tool.connector_id for tool in tools if tool.connector_id])
        if not connector_ids:
            return {}
        docs = await self._connector_repository.find_by_ids_for_organization(
            organization_id=organization_id,
            connector_ids=connector_ids,
        )
        return {str(doc["_id"]): doc for doc in docs}


def _to_runtime_tool(doc: dict[str, Any]) -> RuntimeTool:
    return RuntimeTool(
        id=str(doc["_id"]),
        name=str(doc["name"]),
        description=str(doc.get("description") or doc["name"]),
        executor=str(doc["executor"]),
        connector_id=str(doc["connector_id"]),
        config=dict(doc.get("config") or {}),
        status=str(doc.get("status", TOOL_STATUS_ACTIVE)),
    )


def _to_runtime_kb(doc: dict[str, Any]) -> RuntimeKnowledgeBase:
    return RuntimeKnowledgeBase(
        id=str(doc["_id"]),
        name=str(doc["name"]),
        description=_optional_str(doc.get("description")),
        storage_type=str(doc.get("storage_type", "vector")),
        status=str(doc.get("status", KB_STATUS_READY)),
    )


def _to_runtime_workflow(doc: dict[str, Any]) -> RuntimeWorkflow:
    return RuntimeWorkflow(
        id=str(doc["_id"]),
        name=str(doc["name"]),
        description=_optional_str(doc.get("description")),
        nodes=list(doc.get("nodes") or []),
        edges=list(doc.get("edges") or []),
        status=str(doc.get("status", WORKFLOW_STATUS_DRAFT)),
    )


def _to_runtime_sub_agent(
    doc: dict[str, Any],
    *,
    tools_by_id: dict[str, RuntimeTool],
    kbs_by_id: dict[str, RuntimeKnowledgeBase],
    workflows_by_id: dict[str, RuntimeWorkflow],
) -> RuntimeSubAgent:
    parameters = [
        RuntimeSubAgentParameter(
            name=str(item["name"]),
            type=str(item.get("type", "string")),
            description=_optional_str(item.get("description")),
            required=bool(item.get("required", True)),
        )
        for item in (doc.get("parameters") or [])
        if isinstance(item, dict) and item.get("name")
    ]
    return RuntimeSubAgent(
        id=str(doc["_id"]),
        name=str(doc["name"]),
        description=_optional_str(doc.get("description")),
        instructions=str(doc.get("instructions") or ""),
        parameters=parameters,
        tools=[
            tools_by_id[tool_id]
            for tool_id in _string_list(doc.get("tool_ids"))
            if tool_id in tools_by_id
        ],
        knowledge_bases=[
            kbs_by_id[kb_id]
            for kb_id in _string_list(doc.get("knowledge_base_ids"))
            if kb_id in kbs_by_id
        ],
        workflows=[
            workflows_by_id[workflow_id]
            for workflow_id in _string_list(doc.get("workflow_ids"))
            if workflow_id in workflows_by_id
        ],
        status=str(doc.get("status", SUB_AGENT_STATUS_ACTIVE)),
    )


def _parse_llm_config(raw: Any) -> LLMConfig | None:
    if not raw or not isinstance(raw, dict) or not raw.get("model_id"):
        return None
    return LLMConfig.model_validate(raw)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _collect_ids(docs: list[dict[str, Any]], field: str) -> list[str]:
    ids: list[str] = []
    for doc in docs:
        ids.extend(_string_list(doc.get(field)))
    return ids


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result

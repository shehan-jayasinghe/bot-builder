import asyncio
from unittest.mock import AsyncMock

from bson import ObjectId

from app.domain.constants.knowledgebase_constants import KB_STATUS_READY
from app.domain.constants.sub_agent_constants import SUB_AGENT_STATUS_ACTIVE
from app.domain.constants.tool_constants import TOOL_STATUS_ACTIVE
from app.domain.constants.workflow_constants import WORKFLOW_STATUS_PUBLISHED
from app.services.runtime_bundle_loader import RuntimeBundleLoader

ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = ObjectId("6a3b7c61d8139334274fbbf1")
TOOL_ID = ObjectId("6a3f9012d8139334274fbc01")
KB_ID = ObjectId("6a3f9012d8139334274fbc02")
WORKFLOW_ID = ObjectId("6a3f9012d8139334274fbc03")
SUB_AGENT_ID = ObjectId("6a3f9012d8139334274fbc04")


def test_runtime_bundle_loader_hydrates_orchestrator_and_sub_agents() -> None:
    async def _run() -> None:
        tool_repository = AsyncMock()
        knowledgebase_repository = AsyncMock()
        workflow_repository = AsyncMock()
        sub_agent_repository = AsyncMock()
        connector_repository = AsyncMock()

        sub_agent_repository.find_by_ids_for_agent.return_value = [
            {
                "_id": SUB_AGENT_ID,
                "name": "research_agent",
                "description": "Research",
                "instructions": "Research facts carefully.",
                "tool_ids": [str(TOOL_ID)],
                "knowledge_base_ids": [str(KB_ID)],
                "workflow_ids": [],
                "parameters": [{"name": "query", "type": "string", "required": True}],
                "status": SUB_AGENT_STATUS_ACTIVE,
            },
        ]
        tool_repository.find_by_ids_for_organization.return_value = [
            {
                "_id": TOOL_ID,
                "name": "customer_lookup",
                "description": "Lookup customer",
                "executor": "mongo_find_one",
                "connector_id": ObjectId("6a3f9012d8139334274fbc05"),
                "config": {},
                "status": TOOL_STATUS_ACTIVE,
            },
        ]
        knowledgebase_repository.find_by_ids_for_organization.return_value = [
            {
                "_id": KB_ID,
                "name": "Policy docs",
                "description": "Policies",
                "storage_type": "vector",
                "status": KB_STATUS_READY,
            },
        ]
        workflow_repository.find_by_ids_for_organization.return_value = [
            {
                "_id": WORKFLOW_ID,
                "name": "Onboarding",
                "description": "Onboard users",
                "nodes": [],
                "edges": [],
                "status": WORKFLOW_STATUS_PUBLISHED,
            },
        ]

        loader = RuntimeBundleLoader(
            tool_repository=tool_repository,
            knowledgebase_repository=knowledgebase_repository,
            workflow_repository=workflow_repository,
            sub_agent_repository=sub_agent_repository,
            connector_repository=connector_repository,
        )

        bundle = await loader.load(
            agent_doc={
                "_id": AGENT_ID,
                "organization_id": ORG_ID,
                "name": "Support Bot",
                "system_prompt": "You are helpful.",
                "tool_ids": [str(TOOL_ID)],
                "knowledge_base_ids": [str(KB_ID)],
                "workflow_ids": [str(WORKFLOW_ID)],
                "sub_agent_ids": [str(SUB_AGENT_ID)],
                "guardrails": [],
            },
        )

        assert bundle.organization_id == ORG_ID
        assert bundle.orchestrator.id == str(AGENT_ID)
        assert len(bundle.orchestrator.tools) == 1
        assert bundle.orchestrator.tools[0].name == "customer_lookup"
        assert len(bundle.orchestrator.knowledge_bases) == 1
        assert len(bundle.orchestrator.workflows) == 1
        assert len(bundle.orchestrator.sub_agents) == 1
        assert bundle.orchestrator.sub_agents[0].tools[0].name == "customer_lookup"

    asyncio.run(_run())

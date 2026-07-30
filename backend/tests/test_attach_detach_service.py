import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.models.current_user import CurrentUser
from app.schemas.knowledgebase import SourceType, StorageType, UpdateKnowledgebaseRequest
from app.schemas.tool import UpdateToolRequest
from app.services.knowledgebase_service import KnowledgebaseService
from app.services.tool_service import ToolService
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.knowledgebase import KnowledgebaseNotFoundError
from app.shared.exceptions.tool import ToolNameExistsError, ToolNotFoundError


ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = "6a3b7c61d8139334274fbbf1"
OTHER_AGENT_ID = "6a3b7c61d8139334274fbbf2"
KB_ID = "6a3f9012d8139334274fbc01"
TOOL_ID = "6a3f9012d8139334274fbc00"
WORKFLOW_ID = "6a3e780bcc2c2bdca82118c2"
NOW = datetime(2026, 6, 26, 10, 0, 0, tzinfo=UTC)


def _current_user() -> CurrentUser:
    return CurrentUser(
        user_id="6a3b7c61d8139334274fbbfd",
        organization_id=ORG_ID,
        clerk_id="user_test",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        user_type="root",
        is_root=True,
        status="active",
        organization_name="abc bank",
        organization_industry="financial_services",
    )


def _agent_repo_with_catalog(**overrides: object) -> MagicMock:
    agent_repo = MagicMock()
    agent_repo.upsert_capability_catalog_entry = AsyncMock(return_value=True)
    agent_repo.remove_capability_catalog_entry = AsyncMock(return_value=True)
    agent_repo.find_by_id_for_organization = AsyncMock(
        return_value={"_id": AGENT_ID, "capability_catalog": {}},
    )
    for name, value in overrides.items():
        setattr(agent_repo, name, value)
    return agent_repo


def test_knowledgebase_service_attach_updates_agent_ids() -> None:
    kb_repo = MagicMock()
    job_repo = MagicMock()
    s3 = MagicMock()

    kb_repo.find_by_id_for_organization = AsyncMock(
        return_value={
            "_id": KB_ID,
            "name": "Policy",
            "source_type": "file",
            "storage_type": "vector",
            "status": "ready",
            "organization_id": ORG_ID,
            "agent_id": None,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    kb_repo.update = AsyncMock(
        return_value={
            "_id": KB_ID,
            "name": "Policy",
            "source_type": "file",
            "storage_type": "vector",
            "status": "ready",
            "organization_id": ORG_ID,
            "agent_id": AGENT_ID,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    agent_repo = _agent_repo_with_catalog(
        push_knowledge_base_id=AsyncMock(return_value=True),
    )

    service = KnowledgebaseService(
        knowledgebase_repository=kb_repo,
        job_log_repository=job_repo,
        agent_repository=agent_repo,
        s3_connector=s3,
    )

    async def _run() -> None:
        result = await service.update(
            current_user=_current_user(),
            knowledgebase_id=KB_ID,
            request=UpdateKnowledgebaseRequest(agent_id=AGENT_ID),
        )
        assert result.agent_id == AGENT_ID
        agent_repo.push_knowledge_base_id.assert_awaited_once()

    asyncio.run(_run())


def test_knowledgebase_service_detach_pulls_agent_ids() -> None:
    kb_repo = MagicMock()
    job_repo = MagicMock()
    s3 = MagicMock()

    kb_repo.find_by_id_for_organization = AsyncMock(
        return_value={
            "_id": KB_ID,
            "name": "Policy",
            "source_type": "file",
            "storage_type": "vector",
            "status": "ready",
            "organization_id": ORG_ID,
            "agent_id": AGENT_ID,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    kb_repo.update = AsyncMock(
        return_value={
            "_id": KB_ID,
            "name": "Policy",
            "source_type": "file",
            "storage_type": "vector",
            "status": "ready",
            "organization_id": ORG_ID,
            "agent_id": None,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    agent_repo = _agent_repo_with_catalog(
        pull_knowledge_base_id=AsyncMock(return_value=True),
    )

    service = KnowledgebaseService(
        knowledgebase_repository=kb_repo,
        job_log_repository=job_repo,
        agent_repository=agent_repo,
        s3_connector=s3,
    )

    async def _run() -> None:
        result = await service.update(
            current_user=_current_user(),
            knowledgebase_id=KB_ID,
            request=UpdateKnowledgebaseRequest(agent_id=None),
        )
        assert result.agent_id is None
        agent_repo.pull_knowledge_base_id.assert_awaited_once()

    asyncio.run(_run())


def test_knowledgebase_service_update_not_found() -> None:
    kb_repo = MagicMock()
    kb_repo.find_by_id_for_organization = AsyncMock(return_value=None)

    service = KnowledgebaseService(
        knowledgebase_repository=kb_repo,
        job_log_repository=MagicMock(),
        agent_repository=MagicMock(),
        s3_connector=MagicMock(),
    )

    async def _run() -> None:
        with pytest.raises(KnowledgebaseNotFoundError):
            await service.update(
                current_user=_current_user(),
                knowledgebase_id=KB_ID,
                request=UpdateKnowledgebaseRequest(agent_id=AGENT_ID),
            )

    asyncio.run(_run())


def test_tool_service_attach_moves_between_agents() -> None:
    tool_repo = MagicMock()
    connector_repo = MagicMock()

    tool_repo.find_by_id_for_organization = AsyncMock(
        return_value={
            "_id": TOOL_ID,
            "name": "customer_lookup",
            "description": "Lookup",
            "executor": "mongo_find_one",
            "connector_id": "6a3f8c12d8139334274fbbfe",
            "config": {},
            "status": "active",
            "organization_id": ORG_ID,
            "agent_id": AGENT_ID,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    tool_repo.find_by_name_for_agent = AsyncMock(return_value=None)
    tool_repo.update = AsyncMock(
        return_value={
            "_id": TOOL_ID,
            "name": "customer_lookup",
            "description": "Lookup",
            "executor": "mongo_find_one",
            "connector_id": "6a3f8c12d8139334274fbbfe",
            "config": {},
            "status": "active",
            "organization_id": ORG_ID,
            "agent_id": OTHER_AGENT_ID,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    agent_repo = _agent_repo_with_catalog(
        find_by_id_for_organization=AsyncMock(return_value={"_id": OTHER_AGENT_ID, "capability_catalog": {}}),
        pull_tool_id=AsyncMock(return_value=True),
        push_tool_id=AsyncMock(return_value=True),
    )

    service = ToolService(
        tool_repository=tool_repo,
        agent_repository=agent_repo,
        connector_repository=connector_repo,
    )

    async def _run() -> None:
        result = await service.update(
            current_user=_current_user(),
            tool_id=TOOL_ID,
            request=UpdateToolRequest(agent_id=OTHER_AGENT_ID),
        )
        assert result.agent_id == OTHER_AGENT_ID
        agent_repo.pull_tool_id.assert_awaited_once()
        agent_repo.push_tool_id.assert_awaited_once()

    asyncio.run(_run())


def test_tool_service_move_preserves_routing_hint_when_not_in_patch() -> None:
    tool_repo = MagicMock()
    connector_repo = MagicMock()

    tool_repo.find_by_id_for_organization = AsyncMock(
        return_value={
            "_id": TOOL_ID,
            "name": "customer_lookup",
            "description": "Lookup",
            "executor": "mongo_find_one",
            "connector_id": "6a3f8c12d8139334274fbbfe",
            "config": {},
            "status": "active",
            "organization_id": ORG_ID,
            "agent_id": AGENT_ID,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    tool_repo.find_by_name_for_agent = AsyncMock(return_value=None)
    tool_repo.update = AsyncMock(
        return_value={
            "_id": TOOL_ID,
            "name": "customer_lookup",
            "description": "Lookup",
            "executor": "mongo_find_one",
            "connector_id": "6a3f8c12d8139334274fbbfe",
            "config": {},
            "status": "active",
            "organization_id": ORG_ID,
            "agent_id": OTHER_AGENT_ID,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )

    async def _find_agent(*, agent_id: str, organization_id: str) -> dict[str, object]:
        if agent_id == AGENT_ID:
            return {
                "_id": AGENT_ID,
                "capability_catalog": {
                    "tools": {TOOL_ID: {"routing_hint": "Use for balance questions"}},
                },
            }
        return {
            "_id": OTHER_AGENT_ID,
            "capability_catalog": {
                "tools": {TOOL_ID: {"routing_hint": "Use for balance questions"}},
            },
        }

    agent_repo = _agent_repo_with_catalog(
        find_by_id_for_organization=AsyncMock(side_effect=_find_agent),
        pull_tool_id=AsyncMock(return_value=True),
        push_tool_id=AsyncMock(return_value=True),
    )

    service = ToolService(
        tool_repository=tool_repo,
        agent_repository=agent_repo,
        connector_repository=connector_repo,
    )

    async def _run() -> None:
        await service.update(
            current_user=_current_user(),
            tool_id=TOOL_ID,
            request=UpdateToolRequest(agent_id=OTHER_AGENT_ID),
        )
        upsert_call = agent_repo.upsert_capability_catalog_entry.await_args
        assert upsert_call is not None
        assert upsert_call.kwargs["routing_hint"] == "Use for balance questions"

    asyncio.run(_run())


def test_tool_service_attach_name_conflict() -> None:
    tool_repo = MagicMock()
    agent_repo = MagicMock()

    tool_repo.find_by_id_for_organization = AsyncMock(
        return_value={
            "_id": TOOL_ID,
            "name": "customer_lookup",
            "description": "Lookup",
            "executor": "mongo_find_one",
            "connector_id": "6a3f8c12d8139334274fbbfe",
            "config": {},
            "status": "active",
            "organization_id": ORG_ID,
            "agent_id": None,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    tool_repo.find_by_name_for_agent = AsyncMock(return_value={"_id": "other"})
    agent_repo.find_by_id_for_organization = AsyncMock(return_value={"_id": AGENT_ID})

    service = ToolService(
        tool_repository=tool_repo,
        agent_repository=agent_repo,
        connector_repository=MagicMock(),
    )

    async def _run() -> None:
        with pytest.raises(ToolNameExistsError):
            await service.update(
                current_user=_current_user(),
                tool_id=TOOL_ID,
                request=UpdateToolRequest(agent_id=AGENT_ID),
            )

    asyncio.run(_run())


def test_tool_service_detach() -> None:
    tool_repo = MagicMock()

    tool_repo.find_by_id_for_organization = AsyncMock(
        return_value={
            "_id": TOOL_ID,
            "name": "customer_lookup",
            "description": "Lookup",
            "executor": "mongo_find_one",
            "connector_id": "6a3f8c12d8139334274fbbfe",
            "config": {},
            "status": "active",
            "organization_id": ORG_ID,
            "agent_id": AGENT_ID,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    tool_repo.update = AsyncMock(
        return_value={
            "_id": TOOL_ID,
            "name": "customer_lookup",
            "description": "Lookup",
            "executor": "mongo_find_one",
            "connector_id": "6a3f8c12d8139334274fbbfe",
            "config": {},
            "status": "active",
            "organization_id": ORG_ID,
            "agent_id": None,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    agent_repo = _agent_repo_with_catalog(
        pull_tool_id=AsyncMock(return_value=True),
    )

    service = ToolService(
        tool_repository=tool_repo,
        agent_repository=agent_repo,
        connector_repository=MagicMock(),
    )

    async def _run() -> None:
        result = await service.update(
            current_user=_current_user(),
            tool_id=TOOL_ID,
            request=UpdateToolRequest(agent_id=None),
        )
        assert result.agent_id is None
        agent_repo.pull_tool_id.assert_awaited_once()

    asyncio.run(_run())


def test_tool_service_update_not_found() -> None:
    tool_repo = MagicMock()
    tool_repo.find_by_id_for_organization = AsyncMock(return_value=None)

    service = ToolService(
        tool_repository=tool_repo,
        agent_repository=MagicMock(),
        connector_repository=MagicMock(),
    )

    async def _run() -> None:
        with pytest.raises(ToolNotFoundError):
            await service.update(
                current_user=_current_user(),
                tool_id=TOOL_ID,
                request=UpdateToolRequest(agent_id=AGENT_ID),
            )

    asyncio.run(_run())


def test_tool_service_attach_agent_not_found() -> None:
    tool_repo = MagicMock()
    agent_repo = MagicMock()

    tool_repo.find_by_id_for_organization = AsyncMock(
        return_value={
            "_id": TOOL_ID,
            "name": "customer_lookup",
            "description": "Lookup",
            "executor": "mongo_find_one",
            "connector_id": "6a3f8c12d8139334274fbbfe",
            "config": {},
            "status": "active",
            "organization_id": ORG_ID,
            "agent_id": None,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    agent_repo.find_by_id_for_organization = AsyncMock(return_value=None)

    service = ToolService(
        tool_repository=tool_repo,
        agent_repository=agent_repo,
        connector_repository=MagicMock(),
    )

    async def _run() -> None:
        with pytest.raises(AgentNotFoundError):
            await service.update(
                current_user=_current_user(),
                tool_id=TOOL_ID,
                request=UpdateToolRequest(agent_id=AGENT_ID),
            )

    asyncio.run(_run())


def test_workflow_service_attach_updates_agent_ids() -> None:
    workflow_repo = MagicMock()

    workflow_repo.find_by_id_for_organization = AsyncMock(
        return_value={
            "_id": WORKFLOW_ID,
            "name": "hello",
            "description": None,
            "organization_id": ORG_ID,
            "agent_id": None,
            "status": "draft",
            "nodes": [],
            "edges": [],
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    workflow_repo.update = AsyncMock(
        return_value={
            "_id": WORKFLOW_ID,
            "name": "hello",
            "description": None,
            "organization_id": ORG_ID,
            "agent_id": AGENT_ID,
            "status": "draft",
            "nodes": [],
            "edges": [],
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    agent_repo = _agent_repo_with_catalog(
        push_workflow_id=AsyncMock(return_value=True),
    )

    from app.schemas.workflow import UpdateWorkflowRequest
    from app.services.workflow_service import WorkflowService

    service = WorkflowService(
        workflow_repository=workflow_repo,
        agent_repository=agent_repo,
    )

    async def _run() -> None:
        result = await service.update(
            current_user=_current_user(),
            workflow_id=WORKFLOW_ID,
            request=UpdateWorkflowRequest(agent_id=AGENT_ID),
        )
        assert result.agent_id == AGENT_ID
        agent_repo.push_workflow_id.assert_awaited_once()

    asyncio.run(_run())


def test_workflow_service_detach_pulls_agent_ids() -> None:
    workflow_repo = MagicMock()

    workflow_repo.find_by_id_for_organization = AsyncMock(
        return_value={
            "_id": WORKFLOW_ID,
            "name": "hello",
            "description": None,
            "organization_id": ORG_ID,
            "agent_id": AGENT_ID,
            "status": "draft",
            "nodes": [],
            "edges": [],
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    workflow_repo.update = AsyncMock(
        return_value={
            "_id": WORKFLOW_ID,
            "name": "hello",
            "description": None,
            "organization_id": ORG_ID,
            "agent_id": None,
            "status": "draft",
            "nodes": [],
            "edges": [],
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    agent_repo = _agent_repo_with_catalog(
        pull_workflow_id=AsyncMock(return_value=True),
    )

    from app.schemas.workflow import UpdateWorkflowRequest
    from app.services.workflow_service import WorkflowService

    service = WorkflowService(
        workflow_repository=workflow_repo,
        agent_repository=agent_repo,
    )

    async def _run() -> None:
        result = await service.update(
            current_user=_current_user(),
            workflow_id=WORKFLOW_ID,
            request=UpdateWorkflowRequest(agent_id=None),
        )
        assert result.agent_id is None
        agent_repo.pull_workflow_id.assert_awaited_once()

    asyncio.run(_run())

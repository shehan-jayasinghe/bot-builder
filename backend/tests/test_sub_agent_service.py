import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.domain.constants.sub_agent_constants import MAX_SUB_AGENTS_PER_AGENT
from app.domain.models.current_user import CurrentUser
from app.schemas.sub_agent import CreateSubAgentRequest, ParameterType, SubAgentParameter, UpdateSubAgentRequest
from app.services.sub_agent_service import SubAgentService
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.sub_agent import (
    SubAgentInvalidCapabilityError,
    SubAgentLimitReachedError,
    SubAgentNameExistsError,
    SubAgentNotFoundError,
)


ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = "6a3b7c61d8139334274fbbf1"
SUB_AGENT_ID = "6a3f9012d8139334274fbc00"
TOOL_ID = "6a3f9012d8139334274fbc01"
KB_ID = "6a3f9012d8139334274fbc02"
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


def _saved_document() -> dict:
    return {
        "_id": SUB_AGENT_ID,
        "name": "research_agent",
        "description": "Research specialist",
        "instructions": "You are a research assistant focused on factual answers.",
        "tool_ids": [TOOL_ID],
        "knowledge_base_ids": [KB_ID],
        "workflow_ids": [],
        "parameters": [
            {
                "name": "query",
                "type": "string",
                "description": "Research question",
                "required": True,
            }
        ],
        "status": "active",
        "agent_id": AGENT_ID,
        "organization_id": ORG_ID,
        "created_at": NOW,
        "updated_at": NOW,
    }


def _service_with_mocks() -> tuple[SubAgentService, object, object, object, object, object]:
    sub_agent_repo = type("SubAgentRepo", (), {})()
    agent_repo = type("AgentRepo", (), {})()
    tool_repo = type("ToolRepo", (), {})()
    kb_repo = type("KbRepo", (), {})()
    workflow_repo = type("WorkflowRepo", (), {})()

    service = SubAgentService(
        sub_agent_repository=sub_agent_repo,
        agent_repository=agent_repo,
        tool_repository=tool_repo,
        knowledgebase_repository=kb_repo,
        workflow_repository=workflow_repo,
    )
    return service, sub_agent_repo, agent_repo, tool_repo, kb_repo, workflow_repo


def test_sub_agent_service_create() -> None:
    async def _run() -> None:
        service, sub_agent_repo, agent_repo, tool_repo, kb_repo, workflow_repo = _service_with_mocks()
        agent_repo.find_by_id_for_organization = AsyncMock(
            return_value={"_id": AGENT_ID, "capability_catalog": {}},
        )
        agent_repo.upsert_capability_catalog_entry = AsyncMock(return_value=True)
        sub_agent_repo.count_by_agent = AsyncMock(return_value=0)
        sub_agent_repo.find_by_name_for_agent = AsyncMock(return_value=None)
        tool_repo.find_by_id_for_agent = AsyncMock(return_value={"_id": TOOL_ID})
        kb_repo.find_by_id_for_organization = AsyncMock(return_value={"_id": KB_ID, "agent_id": AGENT_ID})
        workflow_repo.find_by_id_for_organization = AsyncMock()
        sub_agent_repo.create = AsyncMock(return_value=_saved_document())
        agent_repo.push_sub_agent_id = AsyncMock(return_value=True)

        result = await service.create(
            current_user=_current_user(),
            agent_id=AGENT_ID,
            request=CreateSubAgentRequest(
                name="research_agent",
                description="Research specialist",
                instructions="You are a research assistant focused on factual answers.",
                tool_ids=[TOOL_ID],
                knowledge_base_ids=[KB_ID],
                parameters=[
                    SubAgentParameter(
                        name="query",
                        type=ParameterType.STRING,
                        description="Research question",
                    )
                ],
            ),
        )

        assert result.id == SUB_AGENT_ID
        assert result.name == "research_agent"
        sub_agent_repo.create.assert_awaited_once()
        agent_repo.push_sub_agent_id.assert_awaited_once()

    asyncio.run(_run())


def test_sub_agent_service_create_enforces_limit() -> None:
    async def _run() -> None:
        service, sub_agent_repo, agent_repo, *_ = _service_with_mocks()
        agent_repo.find_by_id_for_organization = AsyncMock(return_value={"_id": AGENT_ID})
        sub_agent_repo.count_by_agent = AsyncMock(return_value=MAX_SUB_AGENTS_PER_AGENT)

        with pytest.raises(SubAgentLimitReachedError):
            await service.create(
                current_user=_current_user(),
                agent_id=AGENT_ID,
                request=CreateSubAgentRequest(
                    name="research_agent",
                    instructions="You are a research assistant focused on factual answers.",
                ),
            )

    asyncio.run(_run())


def test_sub_agent_service_create_rejects_duplicate_name() -> None:
    async def _run() -> None:
        service, sub_agent_repo, agent_repo, *_ = _service_with_mocks()
        agent_repo.find_by_id_for_organization = AsyncMock(return_value={"_id": AGENT_ID})
        sub_agent_repo.count_by_agent = AsyncMock(return_value=0)
        sub_agent_repo.find_by_name_for_agent = AsyncMock(return_value={"_id": SUB_AGENT_ID})

        with pytest.raises(SubAgentNameExistsError):
            await service.create(
                current_user=_current_user(),
                agent_id=AGENT_ID,
                request=CreateSubAgentRequest(
                    name="research_agent",
                    instructions="You are a research assistant focused on factual answers.",
                ),
            )

    asyncio.run(_run())


def test_sub_agent_service_create_validates_tool_on_parent() -> None:
    async def _run() -> None:
        service, sub_agent_repo, agent_repo, tool_repo, *_ = _service_with_mocks()
        agent_repo.find_by_id_for_organization = AsyncMock(return_value={"_id": AGENT_ID})
        sub_agent_repo.count_by_agent = AsyncMock(return_value=0)
        sub_agent_repo.find_by_name_for_agent = AsyncMock(return_value=None)
        tool_repo.find_by_id_for_agent = AsyncMock(return_value=None)

        with pytest.raises(SubAgentInvalidCapabilityError):
            await service.create(
                current_user=_current_user(),
                agent_id=AGENT_ID,
                request=CreateSubAgentRequest(
                    name="research_agent",
                    instructions="You are a research assistant focused on factual answers.",
                    tool_ids=[TOOL_ID],
                ),
            )

    asyncio.run(_run())


def test_sub_agent_service_get_not_found() -> None:
    async def _run() -> None:
        service, sub_agent_repo, agent_repo, *_ = _service_with_mocks()
        agent_repo.find_by_id_for_organization = AsyncMock(return_value={"_id": AGENT_ID})
        sub_agent_repo.find_by_id_for_agent = AsyncMock(return_value=None)

        with pytest.raises(SubAgentNotFoundError):
            await service.get_by_id(
                current_user=_current_user(),
                agent_id=AGENT_ID,
                sub_agent_id=SUB_AGENT_ID,
            )

    asyncio.run(_run())


def test_sub_agent_service_list_by_agent() -> None:
    async def _run() -> None:
        service, sub_agent_repo, agent_repo, *_ = _service_with_mocks()
        agent_repo.find_by_id_for_organization = AsyncMock(return_value={"_id": AGENT_ID})
        sub_agent_repo.find_all_by_agent = AsyncMock(return_value=[_saved_document()])

        result = await service.list_by_agent(current_user=_current_user(), agent_id=AGENT_ID)

        assert result.total == 1
        assert result.items[0].tool_count == 1
        assert result.items[0].parameter_count == 1

    asyncio.run(_run())


def test_sub_agent_service_update_instructions() -> None:
    async def _run() -> None:
        service, sub_agent_repo, agent_repo, *_ = _service_with_mocks()
        agent_repo.find_by_id_for_organization = AsyncMock(return_value={"_id": AGENT_ID})
        sub_agent_repo.find_by_id_for_agent = AsyncMock(return_value=_saved_document())
        sub_agent_repo.update = AsyncMock(
            return_value={
                **_saved_document(),
                "instructions": "Updated instructions for research tasks here.",
            }
        )

        result = await service.update(
            current_user=_current_user(),
            agent_id=AGENT_ID,
            sub_agent_id=SUB_AGENT_ID,
            request=UpdateSubAgentRequest(
                instructions="Updated instructions for research tasks here.",
            ),
        )

        assert "Updated instructions" in result.instructions
        sub_agent_repo.update.assert_awaited_once()

    asyncio.run(_run())


def test_sub_agent_service_update_agent_not_found() -> None:
    async def _run() -> None:
        service, _, agent_repo, *_ = _service_with_mocks()
        agent_repo.find_by_id_for_organization = AsyncMock(return_value=None)

        with pytest.raises(AgentNotFoundError):
            await service.list_by_agent(current_user=_current_user(), agent_id=AGENT_ID)

    asyncio.run(_run())

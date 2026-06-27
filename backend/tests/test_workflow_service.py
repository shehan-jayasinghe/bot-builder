import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.domain.constants.workflow_constants import (
    DEFAULT_STARTER_EDGES,
    DEFAULT_STARTER_NODES,
    MAX_WORKFLOWS_PER_ORGANIZATION,
)
from app.domain.models.current_user import CurrentUser
from app.schemas.workflow import CreateWorkflowRequest, UpdateWorkflowRequest
from app.services.workflow_service import WorkflowService
from app.services.workflow_validator import validate_workflow_for_publish
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.workflow import (
    WorkflowLimitReachedError,
    WorkflowNotFoundError,
    WorkflowValidationError,
)


ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = "6a3b7c61d8139334274fbbf1"
WORKFLOW_ID = "6a3f9012d8139334274fbc00"
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


def test_workflow_service_create_defaults() -> None:
    async def _run() -> None:
        workflow_repo = type("Repo", (), {})()
        workflow_repo.count_by_organization = AsyncMock(return_value=0)
        workflow_repo.create = AsyncMock(
            return_value={
                "_id": "6a3f9012d8139334274fbc00",
                "name": "Welcome",
                "description": None,
                "agent_id": None,
                "status": "draft",
                "nodes": DEFAULT_STARTER_NODES,
                "edges": DEFAULT_STARTER_EDGES,
                "organization_id": ORG_ID,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )

        agent_repo = type("AgentRepo", (), {})()
        agent_repo.find_by_id_for_organization = AsyncMock()

        service = WorkflowService(workflow_repository=workflow_repo, agent_repository=agent_repo)
        result = await service.create(current_user=_current_user(), request=CreateWorkflowRequest())

        assert result.name == "Welcome"
        assert result.status == "draft"
        assert result.nodes == DEFAULT_STARTER_NODES
        workflow_repo.create.assert_awaited_once()
        saved = workflow_repo.create.await_args.kwargs["document"]
        assert saved["organization_id"] == ORG_ID
        assert saved["nodes"] == DEFAULT_STARTER_NODES

    asyncio.run(_run())


def test_workflow_service_create_validates_agent() -> None:
    async def _run() -> None:
        workflow_repo = type("Repo", (), {})()
        workflow_repo.count_by_organization = AsyncMock(return_value=0)

        agent_repo = type("AgentRepo", (), {})()
        agent_repo.find_by_id_for_organization = AsyncMock(return_value=None)

        service = WorkflowService(workflow_repository=workflow_repo, agent_repository=agent_repo)

        with pytest.raises(AgentNotFoundError):
            await service.create(
                current_user=_current_user(),
                request=CreateWorkflowRequest(agent_id=AGENT_ID),
            )

    asyncio.run(_run())


def test_workflow_service_create_enforces_limit() -> None:
    async def _run() -> None:
        workflow_repo = type("Repo", (), {})()
        workflow_repo.count_by_organization = AsyncMock(
            return_value=MAX_WORKFLOWS_PER_ORGANIZATION
        )

        agent_repo = type("AgentRepo", (), {})()
        service = WorkflowService(workflow_repository=workflow_repo, agent_repository=agent_repo)

        with pytest.raises(WorkflowLimitReachedError):
            await service.create(current_user=_current_user(), request=CreateWorkflowRequest())

    asyncio.run(_run())


def test_workflow_service_list_by_organization() -> None:
    async def _run() -> None:
        workflow_repo = type("Repo", (), {})()
        workflow_repo.find_all_by_organization = AsyncMock(
            return_value=[
                {
                    "_id": WORKFLOW_ID,
                    "name": "Welcome",
                    "description": None,
                    "agent_id": None,
                    "status": "draft",
                    "nodes": DEFAULT_STARTER_NODES,
                    "edges": DEFAULT_STARTER_EDGES,
                    "organization_id": ORG_ID,
                    "created_at": NOW,
                    "updated_at": NOW,
                }
            ]
        )

        agent_repo = type("AgentRepo", (), {})()
        service = WorkflowService(workflow_repository=workflow_repo, agent_repository=agent_repo)
        result = await service.list_by_organization(current_user=_current_user())

        assert result.total == 1
        assert result.items[0].name == "Welcome"
        assert result.items[0].node_count == 2
        workflow_repo.find_all_by_organization.assert_awaited_once_with(
            organization_id=ORG_ID,
            status=None,
            agent_id=None,
        )

    asyncio.run(_run())


def test_workflow_service_get_by_id() -> None:
    async def _run() -> None:
        workflow_repo = type("Repo", (), {})()
        workflow_repo.find_by_id_for_organization = AsyncMock(
            return_value={
                "_id": WORKFLOW_ID,
                "name": "Welcome",
                "description": None,
                "agent_id": None,
                "status": "draft",
                "nodes": DEFAULT_STARTER_NODES,
                "edges": DEFAULT_STARTER_EDGES,
                "organization_id": ORG_ID,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )

        agent_repo = type("AgentRepo", (), {})()
        service = WorkflowService(workflow_repository=workflow_repo, agent_repository=agent_repo)
        result = await service.get_by_id(current_user=_current_user(), workflow_id=WORKFLOW_ID)

        assert result.id == WORKFLOW_ID
        assert result.nodes == DEFAULT_STARTER_NODES
        workflow_repo.find_by_id_for_organization.assert_awaited_once_with(
            workflow_id=WORKFLOW_ID,
            organization_id=ORG_ID,
        )

    asyncio.run(_run())


def test_workflow_service_get_by_id_not_found() -> None:
    async def _run() -> None:
        workflow_repo = type("Repo", (), {})()
        workflow_repo.find_by_id_for_organization = AsyncMock(return_value=None)

        agent_repo = type("AgentRepo", (), {})()
        service = WorkflowService(workflow_repository=workflow_repo, agent_repository=agent_repo)

        with pytest.raises(WorkflowNotFoundError):
            await service.get_by_id(current_user=_current_user(), workflow_id=WORKFLOW_ID)

    asyncio.run(_run())


def test_workflow_service_update_name_and_nodes() -> None:
    async def _run() -> None:
        workflow_repo = type("Repo", (), {})()
        workflow_repo.find_by_id_for_organization = AsyncMock(
            return_value={
                "_id": WORKFLOW_ID,
                "name": "Welcome",
                "description": None,
                "agent_id": None,
                "status": "draft",
                "nodes": DEFAULT_STARTER_NODES,
                "edges": DEFAULT_STARTER_EDGES,
                "organization_id": ORG_ID,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )
        workflow_repo.update = AsyncMock(
            return_value={
                "_id": WORKFLOW_ID,
                "name": "Billing flow",
                "description": None,
                "agent_id": None,
                "status": "draft",
                "nodes": DEFAULT_STARTER_NODES,
                "edges": DEFAULT_STARTER_EDGES,
                "organization_id": ORG_ID,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )

        agent_repo = type("AgentRepo", (), {})()
        service = WorkflowService(workflow_repository=workflow_repo, agent_repository=agent_repo)
        result = await service.update(
            current_user=_current_user(),
            workflow_id=WORKFLOW_ID,
            request=UpdateWorkflowRequest(name="Billing flow"),
        )

        assert result.name == "Billing flow"
        workflow_repo.update.assert_awaited_once()
        assert workflow_repo.update.await_args.kwargs["updates"] == {"name": "Billing flow"}

    asyncio.run(_run())


def test_workflow_service_update_clears_agent_id() -> None:
    async def _run() -> None:
        workflow_repo = type("Repo", (), {})()
        workflow_repo.find_by_id_for_organization = AsyncMock(
            return_value={
                "_id": WORKFLOW_ID,
                "name": "Welcome",
                "description": None,
                "agent_id": AGENT_ID,
                "status": "draft",
                "nodes": DEFAULT_STARTER_NODES,
                "edges": DEFAULT_STARTER_EDGES,
                "organization_id": ORG_ID,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )
        workflow_repo.update = AsyncMock(
            return_value={
                "_id": WORKFLOW_ID,
                "name": "Welcome",
                "description": None,
                "agent_id": None,
                "status": "draft",
                "nodes": DEFAULT_STARTER_NODES,
                "edges": DEFAULT_STARTER_EDGES,
                "organization_id": ORG_ID,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )

        agent_repo = type("AgentRepo", (), {})()
        agent_repo.pull_workflow_id = AsyncMock(return_value=True)
        service = WorkflowService(workflow_repository=workflow_repo, agent_repository=agent_repo)
        await service.update(
            current_user=_current_user(),
            workflow_id=WORKFLOW_ID,
            request=UpdateWorkflowRequest(agent_id=None),
        )

        assert workflow_repo.update.await_args.kwargs["updates"] == {"agent_id": None}

    asyncio.run(_run())


def test_validate_workflow_for_publish_accepts_starter_graph() -> None:
    validate_workflow_for_publish(nodes=DEFAULT_STARTER_NODES, edges=DEFAULT_STARTER_EDGES)


def test_validate_workflow_for_publish_rejects_missing_start_edge() -> None:
    with pytest.raises(WorkflowValidationError, match="Start node must connect"):
        validate_workflow_for_publish(nodes=DEFAULT_STARTER_NODES, edges=[])


def test_workflow_service_publish_sets_status() -> None:
    async def _run() -> None:
        workflow_repo = type("Repo", (), {})()
        workflow_repo.find_by_id_for_organization = AsyncMock(
            return_value={
                "_id": WORKFLOW_ID,
                "name": "Welcome",
                "status": "draft",
                "nodes": DEFAULT_STARTER_NODES,
                "edges": DEFAULT_STARTER_EDGES,
                "organization_id": ORG_ID,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )
        workflow_repo.update = AsyncMock(
            return_value={
                "_id": WORKFLOW_ID,
                "name": "Welcome",
                "status": "published",
                "nodes": DEFAULT_STARTER_NODES,
                "edges": DEFAULT_STARTER_EDGES,
                "organization_id": ORG_ID,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )

        agent_repo = type("AgentRepo", (), {})()
        service = WorkflowService(workflow_repository=workflow_repo, agent_repository=agent_repo)
        result = await service.publish(current_user=_current_user(), workflow_id=WORKFLOW_ID)

        assert result.status == "published"
        workflow_repo.update.assert_awaited_once_with(
            workflow_id=WORKFLOW_ID,
            organization_id=ORG_ID,
            updates={"status": "published"},
        )

    asyncio.run(_run())


def test_workflow_service_update_reverts_published_to_draft() -> None:
    async def _run() -> None:
        workflow_repo = type("Repo", (), {})()
        workflow_repo.find_by_id_for_organization = AsyncMock(
            return_value={
                "_id": WORKFLOW_ID,
                "name": "Welcome",
                "status": "published",
                "nodes": DEFAULT_STARTER_NODES,
                "edges": DEFAULT_STARTER_EDGES,
                "organization_id": ORG_ID,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )
        workflow_repo.update = AsyncMock(
            return_value={
                "_id": WORKFLOW_ID,
                "name": "Updated",
                "status": "draft",
                "nodes": DEFAULT_STARTER_NODES,
                "edges": DEFAULT_STARTER_EDGES,
                "organization_id": ORG_ID,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )

        agent_repo = type("AgentRepo", (), {})()
        service = WorkflowService(workflow_repository=workflow_repo, agent_repository=agent_repo)
        await service.update(
            current_user=_current_user(),
            workflow_id=WORKFLOW_ID,
            request=UpdateWorkflowRequest(name="Updated"),
        )

        assert workflow_repo.update.await_args.kwargs["updates"] == {
            "name": "Updated",
            "status": "draft",
        }

    asyncio.run(_run())

import asyncio
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId

from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeOrchestrator
from app.domain.models.tracker import Tracker
from app.schemas.chat import ChatRequest
from app.services.assistant_loader import ResolvedChannelAgent
from app.services.chat_completion_service import ChatCompletionService
from app.shared.exceptions.agent import AgentNotFoundError

ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = ObjectId("6a3b7c61d8139334274fbbf1")


def test_chat_completion_returns_unavailable_when_channel_missing() -> None:
    async def _run() -> None:
        service = ChatCompletionService(
            assistant_loader=AsyncMock(),
            agent_repository=AsyncMock(),
            tracker_service=AsyncMock(),
            runtime_bundle_loader=AsyncMock(),
        )
        service._assistant_loader.try_resolve.return_value = None

        response = await service.complete(
            webhook_id="missing",
            request=ChatRequest(sender_id="user-1", message="Hi"),
        )

        assert response.messages[0].text.startswith("This assistant is temporarily unavailable")

    asyncio.run(_run())


def test_chat_completion_runs_orchestrator_and_persists() -> None:
    async def _run() -> None:
        assistant_loader = AsyncMock()
        agent_repository = AsyncMock()
        tracker_service = AsyncMock()
        runtime_bundle_loader = AsyncMock()
        orchestrator = AsyncMock()

        assistant_loader.try_resolve.return_value = ResolvedChannelAgent(
            agent_doc={"_id": AGENT_ID, "organization_id": ORG_ID},
            organization_id=ORG_ID,
            webhook_id="wh-1",
        )
        tracker = Tracker(sender_id="user-1", assistant_id=str(AGENT_ID))
        tracker_service.load_or_create.return_value = tracker

        bundle = RuntimeBundle(
            orchestrator=RuntimeOrchestrator(
                id=str(AGENT_ID),
                name="Bot",
                system_prompt="Help users.",
            ),
            organization_id=ORG_ID,
        )
        runtime_bundle_loader.load.return_value = bundle
        runtime_bundle_loader.load_connectors_for_tools.return_value = {}
        orchestrator.run_turn.return_value = ["Hello there"]

        service = ChatCompletionService(
            assistant_loader=assistant_loader,
            agent_repository=agent_repository,
            tracker_service=tracker_service,
            runtime_bundle_loader=runtime_bundle_loader,
            orchestrator=orchestrator,
        )

        response = await service.complete(
            webhook_id="wh-1",
            request=ChatRequest(sender_id="user-1", message="Hi"),
        )

        assert response.messages[0].text == "Hello there"
        tracker_service.persist.assert_awaited_once()
        orchestrator.run_turn.assert_awaited_once()

    asyncio.run(_run())


def test_preview_chat_raises_when_agent_missing() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        agent_repository.find_by_id_for_organization.return_value = None

        service = ChatCompletionService(
            assistant_loader=AsyncMock(),
            agent_repository=agent_repository,
            tracker_service=AsyncMock(),
            runtime_bundle_loader=AsyncMock(),
        )

        with pytest.raises(AgentNotFoundError):
            await service.complete_preview(
                agent_id=str(AGENT_ID),
                organization_id=ORG_ID,
                request=ChatRequest(sender_id="preview-1", message="Hi"),
            )

    asyncio.run(_run())


def test_preview_chat_runs_orchestrator() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        tracker_service = AsyncMock()
        runtime_bundle_loader = AsyncMock()
        orchestrator = AsyncMock()

        agent_repository.find_by_id_for_organization.return_value = {
            "_id": AGENT_ID,
            "organization_id": ORG_ID,
            "name": "Bot",
            "system_prompt": "Help users.",
        }
        tracker = Tracker(sender_id="preview-1", assistant_id=str(AGENT_ID))
        tracker_service.load_or_create.return_value = tracker

        bundle = RuntimeBundle(
            orchestrator=RuntimeOrchestrator(
                id=str(AGENT_ID),
                name="Bot",
                system_prompt="Help users.",
            ),
            organization_id=ORG_ID,
        )
        runtime_bundle_loader.load.return_value = bundle
        runtime_bundle_loader.load_connectors_for_tools.return_value = {}
        orchestrator.run_turn.return_value = ["Preview reply"]

        service = ChatCompletionService(
            assistant_loader=AsyncMock(),
            agent_repository=agent_repository,
            tracker_service=tracker_service,
            runtime_bundle_loader=runtime_bundle_loader,
            orchestrator=orchestrator,
        )

        response = await service.complete_preview(
            agent_id=str(AGENT_ID),
            organization_id=ORG_ID,
            request=ChatRequest(sender_id="preview-1", message="Hi"),
        )

        assert response.messages[0].text == "Preview reply"
        tracker_service.load_or_create.assert_awaited_once()
        call_kwargs = tracker_service.load_or_create.await_args.kwargs
        assert call_kwargs["source"] == "preview"
        assert call_kwargs["organization_id"] == ORG_ID

    asyncio.run(_run())

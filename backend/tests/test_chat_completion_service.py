import asyncio
from unittest.mock import AsyncMock

from bson import ObjectId

from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeOrchestrator
from app.domain.models.tracker import Tracker
from app.schemas.chat import ChatRequest
from app.services.assistant_loader import ResolvedChannelAgent
from app.services.chat_completion_service import ChatCompletionService

ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = ObjectId("6a3b7c61d8139334274fbbf1")


def test_chat_completion_returns_unavailable_when_channel_missing() -> None:
    async def _run() -> None:
        service = ChatCompletionService(
            assistant_loader=AsyncMock(),
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

from typing import Any

from app.domain.models.tracker import Tracker
from app.infrastructure.db.repositories.mongo.tracker_repository import TrackerRepository
from app.infrastructure.db.repositories.redis.tracker_session_store import TrackerSessionStore


class TrackerService:
    def __init__(
        self,
        tracker_repository: TrackerRepository,
        tracker_session_store: TrackerSessionStore,
    ) -> None:
        self._tracker_repository = tracker_repository
        self._tracker_session_store = tracker_session_store

    async def load_or_create(
        self,
        *,
        sender_id: str,
        assistant_id: str,
        message: str | None = None,
        metadata: dict[str, Any] | None = None,
        source: str | None = None,
        organization_id: str | None = None,
    ) -> Tracker:
        tracker: Tracker | None = None

        cached = await self._tracker_session_store.get(
            assistant_id=assistant_id,
            sender_id=sender_id,
        )
        if cached is not None:
            tracker = Tracker.from_payload(cached)

        if tracker is None:
            doc = await self._tracker_repository.find_by_session(
                sender_id=sender_id,
                assistant_id=assistant_id,
            )
            if doc is not None:
                tracker = Tracker.from_document(doc)

        if tracker is None:
            tracker = Tracker(sender_id=sender_id, assistant_id=assistant_id)

        if source is not None:
            tracker.set_source(source)
        if organization_id is not None:
            tracker.set_organization_id(organization_id)

        if message is not None:
            tracker.append_user_message(message=message, metadata=metadata or {})
            await self._tracker_session_store.set(
                assistant_id=assistant_id,
                sender_id=sender_id,
                payload=tracker.to_payload(),
            )

        return tracker

    async def save_session(self, tracker: Tracker) -> None:
        await self._tracker_session_store.set(
            assistant_id=tracker.assistant_id,
            sender_id=tracker.sender_id,
            payload=tracker.to_payload(),
        )

    async def persist(self, tracker: Tracker, assistant_replies: list[str]) -> None:
        tracker.append_assistant_replies(assistant_replies)
        await self._tracker_repository.upsert(tracker)
        await self._tracker_session_store.set(
            assistant_id=tracker.assistant_id,
            sender_id=tracker.sender_id,
            payload=tracker.to_payload(),
        )

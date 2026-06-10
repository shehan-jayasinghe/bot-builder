import json
import logging
from typing import TYPE_CHECKING, Any

from app.config import settings

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_REDIS_KEY_PREFIX = "trackers:"


class TrackerSessionStore:
    def __init__(self, redis: "Redis | None") -> None:
        self._redis = redis

    @staticmethod
    def _key(*, assistant_id: str, sender_id: str) -> str:
        return f"{_REDIS_KEY_PREFIX}{assistant_id}:{sender_id}"

    async def get(self, *, assistant_id: str, sender_id: str) -> dict[str, Any] | None:
        if self._redis is None:
            return None

        redis_key = self._key(assistant_id=assistant_id, sender_id=sender_id)
        try:
            cached = await self._redis.get(redis_key)
            if not cached:
                return None
            return json.loads(cached)
        except Exception:
            logger.exception("Failed to load tracker from Redis key=%s", redis_key)
            return None

    async def set(self, *, assistant_id: str, sender_id: str, payload: dict[str, Any]) -> None:
        if self._redis is None:
            return

        redis_key = self._key(assistant_id=assistant_id, sender_id=sender_id)
        try:
            await self._redis.set(
                redis_key,
                json.dumps(payload, default=str),
                ex=settings.redis_session_ttl,
            )
        except Exception:
            logger.exception("Failed to cache tracker in Redis key=%s", redis_key)

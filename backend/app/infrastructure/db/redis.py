import logging
from typing import TYPE_CHECKING

from redis.exceptions import ConnectionError as RedisConnectionError

from app.config import settings

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_redis_client: "Redis | None" = None


async def connect_redis() -> None:
    global _redis_client

    if _redis_client is not None:
        return

    from redis.asyncio import Redis

    logger.info("Connecting to Redis at %s", settings.redis_url)

    try:
        client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        await client.ping()
        _redis_client = client
        logger.info("Redis connected")
    except (RedisConnectionError, OSError) as e:
        _redis_client = None
        logger.warning("Redis unavailable; session cache disabled: %s", e)
    except Exception:
        _redis_client = None
        logger.exception("Failed to connect to Redis; session cache disabled")


async def disconnect_redis() -> None:
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        logger.info("Redis connection closed")

    _redis_client = None


def get_redis() -> "Redis | None":
    return _redis_client

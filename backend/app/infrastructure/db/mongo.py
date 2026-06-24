import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import settings
from app.shared.utils.url import safe_uri

logger = logging.getLogger(__name__)

_motor_client: AsyncIOMotorClient | None = None
_motor_db: AsyncIOMotorDatabase | None = None


async def connect_mongo() -> None:
    global _motor_client, _motor_db

    if _motor_client is not None:
        return

    logger.info("Connecting to MongoDB at %s", safe_uri(settings.mongo_uri))

    try:
        _motor_client = AsyncIOMotorClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=5000,  # fail fast if unreachable
            connectTimeoutMS=5000,
        )
        _motor_db = _motor_client[settings.mongo_db]

        # Verify connection (ping admin or your DB)
        await _motor_client.admin.command("ping")
        logger.info("MongoDB connected. Database: %s", settings.mongo_db)

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        _motor_client = None
        _motor_db = None
        logger.exception("Failed to connect to MongoDB")
        raise RuntimeError(f"Could not connect to MongoDB: {e}") from e


async def disconnect_mongo() -> None:
    global _motor_client, _motor_db

    if _motor_client is not None:
        _motor_client.close()
        logger.info("MongoDB connection closed")

    _motor_client = None
    _motor_db = None


def get_motor_db() -> AsyncIOMotorDatabase:
    if _motor_db is None:
        raise RuntimeError("MongoDB is not connected. Did the app lifespan run?")
    return _motor_db


def get_motor_client() -> AsyncIOMotorClient:
    if _motor_client is None:
        raise RuntimeError("MongoDB is not connected. Did the app lifespan run?")
    return _motor_client

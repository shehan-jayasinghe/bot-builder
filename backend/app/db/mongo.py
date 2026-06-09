from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

_motor_client: AsyncIOMotorClient | None = None
_motor_db: AsyncIOMotorDatabase | None = None


async def connect_mongo() -> None:
    global _motor_client, _motor_db

    # TODO: add connection error handling and retries
    _motor_client = AsyncIOMotorClient(settings.mongo_uri)
    _motor_db = _motor_client[settings.mongo_db]


async def disconnect_mongo() -> None:
    global _motor_client, _motor_db

    if _motor_client is not None:
        _motor_client.close()

    _motor_client = None
    _motor_db = None


def get_motor_db() -> AsyncIOMotorDatabase:
    if _motor_db is None:
        raise RuntimeError("MongoDB is not connected. Did the app lifespan run?")

    return _motor_db

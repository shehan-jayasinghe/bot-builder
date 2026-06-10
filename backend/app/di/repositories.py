from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.infrastructure.db.mongo import get_motor_db
from app.infrastructure.db.redis import get_redis
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.channel_repository import ChannelRepository
from app.infrastructure.db.repositories.mongo.tracker_repository import TrackerRepository
from app.infrastructure.db.repositories.redis.tracker_session_store import TrackerSessionStore


def get_channel_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> ChannelRepository:
    return ChannelRepository(db=db)


def get_agent_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> AgentRepository:
    return AgentRepository(db=db)


def get_tracker_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> TrackerRepository:
    return TrackerRepository(db=db)


def get_tracker_session_store() -> TrackerSessionStore:
    return TrackerSessionStore(redis=get_redis())

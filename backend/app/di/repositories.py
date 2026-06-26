from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.infrastructure.db.mongo import get_motor_db
from app.infrastructure.db.redis import get_redis
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.channel_repository import ChannelRepository
from app.infrastructure.db.repositories.mongo.connector_repository import ConnectorRepository
from app.infrastructure.db.repositories.mongo.job_log_repository import JobLogRepository
from app.infrastructure.db.repositories.mongo.knowledgebase_repository import KnowledgebaseRepository
from app.infrastructure.db.repositories.mongo.organization_repository import OrganizationRepository
from app.infrastructure.db.repositories.mongo.tool_repository import ToolRepository
from app.infrastructure.db.repositories.mongo.tracker_repository import TrackerRepository
from app.infrastructure.db.repositories.mongo.user_repository import UserRepository
from app.infrastructure.db.repositories.redis.tracker_session_store import TrackerSessionStore


def get_channel_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> ChannelRepository:
    return ChannelRepository(db=db)


def get_agent_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> AgentRepository:
    return AgentRepository(db=db)


def get_tracker_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> TrackerRepository:
    return TrackerRepository(db=db)


def get_tracker_session_store() -> TrackerSessionStore:
    return TrackerSessionStore(redis=get_redis())


def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> UserRepository:
    return UserRepository(db=db)


def get_organization_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> OrganizationRepository:
    return OrganizationRepository(db=db)


def get_knowledgebase_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> KnowledgebaseRepository:
    return KnowledgebaseRepository(db=db)


def get_job_log_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> JobLogRepository:
    return JobLogRepository(db=db)


def get_connector_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> ConnectorRepository:
    return ConnectorRepository(db=db)


def get_tool_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> ToolRepository:
    return ToolRepository(db=db)

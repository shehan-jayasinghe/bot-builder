from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient

from app.di.repositories import get_organization_repository, get_user_repository
from app.infrastructure.db.mongo import get_motor_client
from app.infrastructure.db.repositories.mongo.organization_repository import OrganizationRepository
from app.infrastructure.db.repositories.mongo.user_repository import UserRepository
from app.infrastructure.external.clerk_client import ClerkClient
from app.services.registration_service import RegistrationService


def get_clerk_client() -> ClerkClient:
    return ClerkClient()


def get_registration_service(
    clerk_client: ClerkClient = Depends(get_clerk_client),
    user_repository: UserRepository = Depends(get_user_repository),
    organization_repository: OrganizationRepository = Depends(get_organization_repository),
    motor_client: AsyncIOMotorClient = Depends(get_motor_client),
) -> RegistrationService:
    return RegistrationService(
        clerk_client=clerk_client,
        user_repository=user_repository,
        organization_repository=organization_repository,
        motor_client=motor_client,
    )

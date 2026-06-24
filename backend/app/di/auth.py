from fastapi import Depends, Header

from app.di.repositories import get_organization_repository, get_user_repository
from app.domain.models.current_user import CurrentUser
from app.infrastructure.auth.clerk_authenticator import ClerkAuthenticator
from app.infrastructure.auth.clerk_jwt import ClerkJwtVerifier
from app.infrastructure.db.repositories.mongo.organization_repository import OrganizationRepository
from app.infrastructure.db.repositories.mongo.user_repository import UserRepository
from app.services.user_service import UserService


def get_clerk_jwt_verifier() -> ClerkJwtVerifier:
    return ClerkJwtVerifier()


def get_clerk_authenticator(
    jwt_verifier: ClerkJwtVerifier = Depends(get_clerk_jwt_verifier),
    user_repository: UserRepository = Depends(get_user_repository),
    organization_repository: OrganizationRepository = Depends(get_organization_repository),
) -> ClerkAuthenticator:
    return ClerkAuthenticator(
        jwt_verifier=jwt_verifier,
        user_repository=user_repository,
        organization_repository=organization_repository,
    )


async def get_current_user(
    authorization: str | None = Header(default=None),
    authenticator: ClerkAuthenticator = Depends(get_clerk_authenticator),
) -> CurrentUser:
    return await authenticator.authenticate(authorization)


def get_user_service() -> UserService:
    return UserService()

import logging
from typing import Any

from app.domain.models.current_user import CurrentUser
from app.infrastructure.auth.clerk_jwt import ClerkJwtVerifier
from app.infrastructure.db.repositories.mongo.organization_repository import OrganizationRepository
from app.infrastructure.db.repositories.mongo.user_repository import UserRepository
from app.shared.exceptions.auth import (
    OrganizationNotFoundError,
    UnauthorizedError,
    UserDisabledError,
    UserNotFoundError,
)

logger = logging.getLogger(__name__)


class ClerkAuthenticator:
    def __init__(
        self,
        jwt_verifier: ClerkJwtVerifier,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self._jwt = jwt_verifier
        self._users = user_repository
        self._organizations = organization_repository

    async def authenticate(self, authorization: str | None) -> CurrentUser:
        token = self._extract_bearer_token(authorization)
        claims = self._jwt.decode(token)
        clerk_id = str(claims.get("sub", "")).strip()
        if not clerk_id:
            raise UnauthorizedError("Invalid authentication token")

        user_doc = await self._users.find_by_clerk_id(clerk_id)
        if user_doc is None:
            logger.warning("Authenticated Clerk user has no Mongo record clerk_id=%s", clerk_id)
            raise UserNotFoundError("User is not registered")

        if str(user_doc.get("status", "active")) != "active":
            raise UserDisabledError("User account is disabled")

        org_doc = await self._organizations.find_by_id(str(user_doc["organization_id"]))
        if org_doc is None:
            raise OrganizationNotFoundError("Organization not found for user")

        current_user = self._to_current_user(user_doc=user_doc, org_doc=org_doc)
        logger.debug("Authenticated user_id=%s organization_id=%s", current_user.user_id, current_user.organization_id)
        return current_user

    @staticmethod
    def _extract_bearer_token(authorization: str | None) -> str:
        if not authorization or not authorization.startswith("Bearer "):
            raise UnauthorizedError("Missing or invalid Authorization header")

        token = authorization.removeprefix("Bearer ").strip()
        if not token:
            raise UnauthorizedError("Missing authentication token")
        return token

    @staticmethod
    def _to_current_user(*, user_doc: dict[str, Any], org_doc: dict[str, Any]) -> CurrentUser:
        return CurrentUser(
            user_id=str(user_doc["_id"]),
            organization_id=str(user_doc["organization_id"]),
            clerk_id=str(user_doc["clerk_id"]),
            email=str(user_doc["email"]),
            first_name=str(user_doc["first_name"]),
            last_name=str(user_doc["last_name"]),
            user_type=str(user_doc.get("user_type", "owner")),
            is_root=bool(user_doc.get("is_root", False)),
            status=str(user_doc.get("status", "active")),
            organization_name=str(org_doc["name"]),
            organization_industry=org_doc.get("industry"),
        )

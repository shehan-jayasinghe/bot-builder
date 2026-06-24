import logging

from motor.motor_asyncio import AsyncIOMotorClient

from app.infrastructure.db.repositories.mongo.organization_repository import OrganizationRepository
from app.infrastructure.db.repositories.mongo.user_repository import UserRepository
from app.infrastructure.external.clerk_client import ClerkClient
from app.schemas.auth import (
    OrganizationResponse,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationResponse,
    UserResponse,
    VerifyEmailResponse,
)
from app.shared.exceptions.auth import (
    AuthError,
    ClerkUserCreationError,
    EmailAlreadyExistsError,
    RegistrationFailedError,
    UserNotFoundError,
)

logger = logging.getLogger(__name__)


class RegistrationService:
    def __init__(
        self,
        clerk_client: ClerkClient,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        motor_client: AsyncIOMotorClient,
    ) -> None:
        self._clerk = clerk_client
        self._users = user_repository
        self._organizations = organization_repository
        self._motor_client = motor_client

    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        email = str(payload.email).lower()

        existing = await self._users.find_by_email(email)
        if existing is not None:
            raise EmailAlreadyExistsError(f"User already registered with email: {email}")

        created = await self._clerk.create_user(
            email=email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )

        try:
            org_doc, user_doc = await self._persist_registration(
                clerk_id=created.clerk_id,
                payload=payload,
                email=email,
            )
        except Exception as e:
            logger.exception("Registration persistence failed for clerk_id=%s", created.clerk_id)
            await self._clerk.delete_user(created.clerk_id)
            raise RegistrationFailedError("Could not complete registration") from e

        verification_sent, verification_id = await self._send_verification_code(
            email_address_id=created.email_address_id,
            email=email,
        )

        return RegisterResponse(
            user=self._to_user_response(user_doc),
            organization=self._to_organization_response(org_doc),
            email_verified=False,
            verification_sent=verification_sent,
            verification_id=verification_id,
        )

    async def resend_verification(self, email: str) -> ResendVerificationResponse:
        normalized_email = email.lower()
        user_doc = await self._users.find_by_email(normalized_email)
        if user_doc is None:
            raise UserNotFoundError("No account found for this email address")

        clerk_id = str(user_doc["clerk_id"])
        email_address_id = await self._clerk.get_primary_email_address_id(clerk_id, email=normalized_email)
        if not email_address_id:
            raise AuthError("Could not find email address for verification")

        verification_sent, verification_id = await self._send_verification_code(
            email_address_id=email_address_id,
            email=normalized_email,
        )

        if verification_sent:
            return ResendVerificationResponse(
                message="Verification code sent. Please check your inbox.",
                verification_sent=True,
                verification_id=verification_id,
            )

        return ResendVerificationResponse(
            message="Could not send verification code. Please try again later.",
            verification_sent=False,
            verification_id=None,
        )

    async def verify_email(self, email: str, code: str, verification_id: str) -> VerifyEmailResponse:
        normalized_email = email.lower()
        user_doc = await self._users.find_by_email(normalized_email)
        if user_doc is None:
            raise UserNotFoundError("No account found for this email address")

        clerk_id = str(user_doc["clerk_id"])
        email_address_id = await self._clerk.get_primary_email_address_id(clerk_id, email=normalized_email)
        if not email_address_id:
            raise AuthError("Could not find email address for verification")

        try:
            verified = await self._clerk.attempt_email_verification(
                email_address_id=email_address_id,
                code=code,
                verification_id=verification_id,
            )
        except ClerkUserCreationError as e:
            raise AuthError(str(e)) from e

        if not verified:
            raise AuthError("Invalid or expired verification code")

        return VerifyEmailResponse(
            message="Email verified successfully. You can now sign in.",
            email_verified=True,
        )

    async def _send_verification_code(self, *, email_address_id: str, email: str) -> tuple[bool, str | None]:
        try:
            verification_id = await self._clerk.send_email_verification_code(
                email_address_id=email_address_id,
            )
            return True, verification_id
        except ClerkUserCreationError:
            logger.exception("Failed to send verification code to %s", email)
            return False, None

    async def _persist_registration(
        self,
        *,
        clerk_id: str,
        payload: RegisterRequest,
        email: str,
    ) -> tuple[dict, dict]:
        try:
            return await self._persist_with_transaction(clerk_id=clerk_id, payload=payload, email=email)
        except Exception as e:
            if not self._is_transaction_unsupported_error(e):
                raise
            logger.warning("Mongo transactions unavailable; falling back to sequential persistence")
            return await self._persist_sequential(clerk_id=clerk_id, payload=payload, email=email)

    async def _persist_with_transaction(
        self,
        *,
        clerk_id: str,
        payload: RegisterRequest,
        email: str,
    ) -> tuple[dict, dict]:
        async with await self._motor_client.start_session() as session:
            async with session.start_transaction():
                org_doc = await self._organizations.create(
                    name=payload.organization_name,
                    industry=payload.industry,
                    session=session,
                )
                user_doc = await self._users.create(
                    clerk_id=clerk_id,
                    email=email,
                    first_name=payload.first_name,
                    last_name=payload.last_name,
                    organization_id=org_doc["_id"],
                    session=session,
                )
                await self._organizations.set_owner(
                    organization_id=org_doc["_id"],
                    owner_user_id=str(user_doc["_id"]),
                    session=session,
                )
                org_doc["owner_user_id"] = str(user_doc["_id"])

        logger.info(
            "Registered user id=%s org id=%s clerk_id=%s",
            user_doc["_id"],
            org_doc["_id"],
            clerk_id,
        )
        return org_doc, user_doc

    async def _persist_sequential(
        self,
        *,
        clerk_id: str,
        payload: RegisterRequest,
        email: str,
    ) -> tuple[dict, dict]:
        org_doc: dict | None = None
        user_doc: dict | None = None

        try:
            org_doc = await self._organizations.create(
                name=payload.organization_name,
                industry=payload.industry,
            )
            user_doc = await self._users.create(
                clerk_id=clerk_id,
                email=email,
                first_name=payload.first_name,
                last_name=payload.last_name,
                organization_id=org_doc["_id"],
            )
            await self._organizations.set_owner(
                organization_id=org_doc["_id"],
                owner_user_id=str(user_doc["_id"]),
            )
            org_doc["owner_user_id"] = str(user_doc["_id"])
        except Exception:
            if user_doc is not None:
                await self._users.delete_by_id(user_doc["_id"])
            if org_doc is not None:
                await self._organizations.delete_by_id(org_doc["_id"])
            raise

        logger.info(
            "Registered user id=%s org id=%s clerk_id=%s",
            user_doc["_id"],
            org_doc["_id"],
            clerk_id,
        )
        return org_doc, user_doc

    @staticmethod
    def _is_transaction_unsupported_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return "replica set" in message or "transaction" in message

    @staticmethod
    def _to_user_response(doc: dict) -> UserResponse:
        first_name = str(doc["first_name"])
        last_name = str(doc["last_name"])
        return UserResponse(
            id=str(doc["_id"]),
            clerk_id=str(doc["clerk_id"]),
            email=doc["email"],
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}".strip(),
            user_type=str(doc.get("user_type", "owner")),
            is_root=bool(doc.get("is_root", True)),
            organization_id=str(doc["organization_id"]),
            status=str(doc.get("status", "active")),
        )

    @staticmethod
    def _to_organization_response(doc: dict) -> OrganizationResponse:
        return OrganizationResponse(
            id=str(doc["_id"]),
            name=str(doc["name"]),
            industry=doc.get("industry"),
            status=str(doc.get("status", "active")),
        )

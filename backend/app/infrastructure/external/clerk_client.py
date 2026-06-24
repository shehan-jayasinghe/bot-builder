import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings
from app.shared.exceptions.auth import ClerkUserCreationError

logger = logging.getLogger(__name__)

CLERK_API_BASE = "https://api.clerk.com/v1"


@dataclass(frozen=True)
class ClerkCreatedUser:
    clerk_id: str
    email_address_id: str


class ClerkClient:
    def __init__(self, *, secret_key: str | None = None) -> None:
        self._secret_key = secret_key if secret_key is not None else settings.clerk_secret_key

    def _headers(self) -> dict[str, str]:
        if not self._secret_key:
            raise ClerkUserCreationError("Clerk is not configured. Set CLERK_SECRET_KEY.")
        return {
            "Authorization": f"Bearer {self._secret_key}",
            "Content-Type": "application/json",
        }

    async def create_user(
        self,
        *,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> ClerkCreatedUser:
        payload = {
            "email_address": [email],
            "email_address_identification_status": ["reserved"],
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{CLERK_API_BASE}/users",
                    headers=self._headers(),
                    json=payload,
                )
        except httpx.HTTPError as e:
            logger.exception("Clerk API request failed")
            raise ClerkUserCreationError("Could not reach Clerk to create user") from e

        if response.status_code >= 400:
            detail = self._extract_error_detail(response)
            logger.error("Clerk create user failed: status=%s detail=%s", response.status_code, detail)
            raise ClerkUserCreationError(detail)

        data = response.json()
        clerk_id = data.get("id")
        if not clerk_id:
            raise ClerkUserCreationError("Clerk did not return a user id")

        email_address_id = self._extract_primary_email_address_id(data, email)
        if not email_address_id:
            raise ClerkUserCreationError("Clerk did not return an email address id")

        logger.info("Created Clerk user id=%s email=%s (unverified)", clerk_id, email)
        return ClerkCreatedUser(clerk_id=str(clerk_id), email_address_id=email_address_id)

    async def send_email_verification_code(self, *, email_address_id: str) -> str:
        payload = {"strategy": "email_code"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{CLERK_API_BASE}/email_addresses/{email_address_id}/prepare_verification",
                    headers=self._headers(),
                    json=payload,
                )
        except httpx.HTTPError as e:
            logger.exception("Clerk verification email request failed")
            raise ClerkUserCreationError("Could not reach Clerk to send verification code") from e

        if response.status_code >= 400:
            detail = self._extract_error_detail(response)
            logger.error(
                "Clerk send verification code failed: status=%s detail=%s",
                response.status_code,
                detail,
            )
            raise ClerkUserCreationError(detail)

        verification_id = self._extract_verification_id(response.json())
        if not verification_id:
            raise ClerkUserCreationError("Clerk did not return a verification id")

        logger.info(
            "Sent Clerk email verification code for email_address_id=%s verification_id=%s",
            email_address_id,
            verification_id,
        )
        return verification_id

    async def attempt_email_verification(
        self,
        *,
        email_address_id: str,
        code: str,
        verification_id: str,
    ) -> bool:
        payload = {
            "code": code,
            "verification_id": verification_id,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{CLERK_API_BASE}/email_addresses/{email_address_id}/attempt_verification",
                    headers=self._headers(),
                    json=payload,
                )
        except httpx.HTTPError as e:
            logger.exception("Clerk email verification attempt failed")
            raise ClerkUserCreationError("Could not reach Clerk to verify email") from e

        if response.status_code >= 400:
            detail = self._extract_error_detail(response)
            raise ClerkUserCreationError(detail)

        data = response.json()
        if data.get("status") == "verified":
            return True

        verification = data.get("verification")
        if isinstance(verification, dict) and verification.get("status") == "verified":
            return True

        return False

    async def get_primary_email_address_id(self, clerk_id: str, *, email: str) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{CLERK_API_BASE}/users/{clerk_id}",
                    headers=self._headers(),
                )
        except httpx.HTTPError:
            logger.exception("Clerk get user failed clerk_id=%s", clerk_id)
            return None

        if response.status_code >= 400:
            logger.warning("Clerk get user failed clerk_id=%s status=%s", clerk_id, response.status_code)
            return None

        return self._extract_primary_email_address_id(response.json(), email)

    async def delete_user(self, clerk_id: str) -> None:
        if not self._secret_key:
            return

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.delete(
                    f"{CLERK_API_BASE}/users/{clerk_id}",
                    headers=self._headers(),
                )
            if response.status_code >= 400:
                logger.warning(
                    "Failed to rollback Clerk user id=%s status=%s",
                    clerk_id,
                    response.status_code,
                )
        except httpx.HTTPError:
            logger.exception("Failed to rollback Clerk user id=%s", clerk_id)

    @staticmethod
    def _extract_verification_id(data: dict[str, Any]) -> str | None:
        top_id = data.get("id")
        if top_id and str(data.get("object", "")).startswith("verification"):
            return str(top_id)

        verification = data.get("verification")
        if isinstance(verification, dict):
            nested_id = verification.get("id")
            if nested_id:
                return str(nested_id)

        return None

    @staticmethod
    def _extract_primary_email_address_id(data: dict[str, Any], email: str) -> str | None:
        email_addresses = data.get("email_addresses")
        if not isinstance(email_addresses, list):
            return None

        normalized_email = email.lower()
        primary_id = data.get("primary_email_address_id")

        for item in email_addresses:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            item_email = str(item.get("email_address", "")).lower()
            if item_id and item_email == normalized_email:
                return str(item_id)

        if primary_id:
            return str(primary_id)

        if email_addresses and isinstance(email_addresses[0], dict):
            first_id = email_addresses[0].get("id")
            if first_id:
                return str(first_id)

        return None

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            body: dict[str, Any] = response.json()
        except ValueError:
            return "Clerk request failed"

        errors = body.get("errors")
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                message = first.get("long_message") or first.get("message")
                if message:
                    return str(message)

        return str(body.get("message", "Clerk request failed"))

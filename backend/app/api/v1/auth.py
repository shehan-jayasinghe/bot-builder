from fastapi import APIRouter, Depends, status

from app.di.auth import get_current_user, get_user_service
from app.di.registration import get_registration_service
from app.domain.models.current_user import CurrentUser
from app.schemas.auth import (
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.services.registration_service import RegistrationService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    service: RegistrationService = Depends(get_registration_service),
) -> RegisterResponse:
    """
    Register a root user and organization.

    Creates a Clerk account with an unverified email, persists organization + user in MongoDB,
    then sends a Clerk email verification code.
    """
    return await service.register(body)


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    body: ResendVerificationRequest,
    service: RegistrationService = Depends(get_registration_service),
) -> ResendVerificationResponse:
    """Resend the Clerk email verification code for a registered account."""
    return await service.resend_verification(str(body.email))


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    body: VerifyEmailRequest,
    service: RegistrationService = Depends(get_registration_service),
) -> VerifyEmailResponse:
    """Verify a registered account email using the 6-digit code from Clerk."""
    return await service.verify_email(str(body.email), body.code, body.verification_id)


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> MeResponse:
    """Return the authenticated user and organization from MongoDB."""
    return user_service.get_me(current_user)

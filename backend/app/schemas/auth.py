from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    organization_name: str = Field(min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=100)


class OrganizationResponse(BaseModel):
    id: str
    name: str
    industry: str | None = None
    status: str = "active"


class UserResponse(BaseModel):
    id: str
    clerk_id: str
    email: EmailStr
    first_name: str
    last_name: str
    full_name: str
    user_type: str
    is_root: bool = True
    organization_id: str
    status: str = "active"


class RegisterResponse(BaseModel):
    user: UserResponse
    organization: OrganizationResponse
    email_verified: bool = False
    verification_sent: bool = False
    verification_id: str | None = None


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ResendVerificationResponse(BaseModel):
    message: str
    verification_sent: bool
    verification_id: str | None = None


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    verification_id: str = Field(min_length=1)


class VerifyEmailResponse(BaseModel):
    message: str
    email_verified: bool


class MeResponse(BaseModel):
    user: UserResponse
    organization: OrganizationResponse

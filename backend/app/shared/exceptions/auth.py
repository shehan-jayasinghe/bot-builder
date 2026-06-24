from app.shared.exceptions.base import CoreError


class AuthError(CoreError):
    """Base error for authentication and registration."""


class UnauthorizedError(AuthError):
    """JWT is missing, invalid, or expired."""


class UserNotFoundError(AuthError):
    """No MongoDB user exists for the authenticated Clerk account."""


class UserDisabledError(AuthError):
    """The user account is disabled."""


class OrganizationNotFoundError(AuthError):
    """The user's organization could not be found."""


class EmailAlreadyExistsError(AuthError):
    """A user with this email is already registered."""


class ClerkUserCreationError(AuthError):
    """Clerk rejected or failed user creation."""


class RegistrationFailedError(AuthError):
    """Organization or user persistence failed after Clerk user creation."""

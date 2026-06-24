import logging
from typing import Any

import jwt
from jwt import PyJWKClient
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError

from app.config import settings
from app.shared.exceptions.auth import UnauthorizedError

logger = logging.getLogger(__name__)


class ClerkJwtVerifier:
    def __init__(self, *, jwks_url: str | None = None, issuer: str | None = None) -> None:
        self._jwks_url = jwks_url if jwks_url is not None else settings.clerk_jwks_url
        self._issuer = issuer if issuer is not None else settings.clerk_issuer
        self._jwk_client: PyJWKClient | None = None

    def decode(self, token: str) -> dict[str, Any]:
        if not self._jwks_url:
            raise UnauthorizedError("Clerk JWT verification is not configured. Set CLERK_JWKS_URL.")

        if self._jwk_client is None:
            self._jwk_client = PyJWKClient(self._jwks_url)

        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": False,
            }
            decode_kwargs: dict[str, Any] = {
                "algorithms": ["RS256"],
                "options": options,
            }
            if self._issuer:
                decode_kwargs["issuer"] = self._issuer
                options["verify_iss"] = True
            else:
                options["verify_iss"] = False

            return jwt.decode(token, signing_key.key, **decode_kwargs)
        except ExpiredSignatureError as e:
            logger.warning("Clerk JWT expired")
            raise UnauthorizedError("Authentication token has expired") from e
        except (DecodeError, InvalidTokenError) as e:
            logger.warning("Clerk JWT invalid: %s", e)
            raise UnauthorizedError("Invalid authentication token") from e
        except Exception as e:
            logger.exception("Clerk JWT verification failed")
            raise UnauthorizedError("Failed to authenticate token") from e

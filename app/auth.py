"""Authentication and authorization utilities.

This module provides support for generating and validating HS256 JWT tokens.
It exposes a security dependency to enforce Bearer authentication on endpoints.
"""

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

# Initialize HTTPBearer security scheme
security_scheme = HTTPBearer(auto_error=False)


def create_access_token(user_id: str) -> str:
    """Generate a signed HS256 JWT access token for a user.

    Args:
        user_id: The unique identifier of the user (to be stored in the sub claim).

    Returns:
        str: The signed JWT access token.
    """
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_access_token(token: str) -> str:
    """Verify and decode a JWT access token.

    Args:
        token: The signed JWT bearer token string.

    Returns:
        str: The user ID extracted from the 'sub' claim.

    Raises:
        HTTPException: If the token is invalid, expired, or has no sub claim.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token is missing or invalid",
            )
        return user_id
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing or invalid",
        ) from exc


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> str:
    """FastAPI dependency that secures endpoints and returns the current user ID.

    Args:
        credentials: The HTTP Bearer authorization credentials.

    Returns:
        str: The authenticated user's ID.

    Raises:
        HTTPException: If the authorization header is missing or the token is invalid.
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing or invalid",
        )
    return verify_access_token(credentials.credentials)

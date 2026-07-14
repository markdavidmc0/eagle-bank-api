"""Router for authentication endpoints.

This module exposes the login and JWT generation endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import create_access_token
from app.database import get_db

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user",
)
def login(
    request: schemas.LoginRequest,
    db: Session = Depends(get_db),
) -> schemas.TokenResponse:
    """Authenticate a user and return a JWT bearer access token.

    Args:
        request: Schema with user login credentials.
        db: Active database session.

    Returns:
        schemas.TokenResponse: Signed JWT access token.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    db_user = crud.authenticate_user(db, request.email, request.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing or invalid",
        )
    token = create_access_token(db_user.id)
    return schemas.TokenResponse(accessToken=token, tokenType="bearer")

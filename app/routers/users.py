"""Router for User endpoints.

Exposes endpoints for creating, fetching, updating, and deleting users,
enforcing standard authorization checks.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import get_current_user_id
from app.database import get_db

router = APIRouter(prefix="/v1/users", tags=["user"])


@router.post(
    "",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
def create_user(
    request: schemas.CreateUserRequest,
    db: Session = Depends(get_db),
) -> schemas.UserResponse:
    """Create a new user.

    Args:
        request: Schema with new user details.
        db: Active database session.

    Returns:
        schemas.UserResponse: Created user details.
    """
    return crud.create_user(db, request)


@router.get(
    "/{userId}",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch user by ID",
)
def fetch_user(
    userId: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> schemas.UserResponse:
    """Fetch user by ID.

    Args:
        userId: ID of the user to fetch.
        current_user_id: ID of the currently authenticated user.
        db: Active database session.

    Returns:
        schemas.UserResponse: Retrieved user details.

    Raises:
        HTTPException: 404 if not found, 403 if unauthorized.
    """
    if userId != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not allowed to access the transaction",
        )

    db_user = crud.get_user(db, userId)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found",
        )
    return db_user


@router.patch(
    "/{userId}",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user by ID",
)
def update_user(
    userId: str,
    request: schemas.UpdateUserRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> schemas.UserResponse:
    """Update user by ID.

    Args:
        userId: ID of the user to update.
        request: Updated user fields.
        current_user_id: ID of the currently authenticated user.
        db: Active database session.

    Returns:
        schemas.UserResponse: Updated user details.

    Raises:
        HTTPException: 404 if not found, 403 if unauthorized.
    """
    if userId != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not allowed to access the transaction",
        )

    db_user = crud.update_user(db, userId, request)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found",
        )
    return db_user


@router.delete(
    "/{userId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user by ID",
)
def delete_user(
    userId: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Response:
    """Delete user by ID.

    Args:
        userId: ID of the user to delete.
        current_user_id: ID of the currently authenticated user.
        db: Active database session.

    Returns:
        Response: 204 No Content response on success.

    Raises:
        HTTPException: 404 if not found, 403 if unauthorized, 409 if associated with accounts.
    """
    if userId != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not allowed to access the transaction",
        )

    deleted = crud.delete_user(db, userId)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

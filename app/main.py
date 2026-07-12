"""Main entrypoint for the Eagle Bank API application.

Sets up the FastAPI application, registers API routes, configures global
exception handlers for strict spec-compliant error formats, and runs
database initialization on startup.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import models
from app.database import engine
from app.exceptions import BadRequestException
from app.routers import accounts, users

# Initialize database tables on startup (SQLite)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Take home tech task",
    description="REST API for Eagle Bank",
    version="v1.0.0",
)

# Register routers
app.include_router(users.router)
app.include_router(accounts.router)


# --- Global Exception Handlers ---
@app.exception_handler(BadRequestException)
async def bad_request_exception_handler(request: Request, exc: BadRequestException) -> JSONResponse:
    """Format and return standard BadRequestErrorResponse for domain validations."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": exc.message,
            "details": [
                {
                    "field": exc.field,
                    "message": exc.detail_message,
                    "type": exc.error_type,
                }
            ],
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Intercept and format FastAPI request validation errors into BadRequestErrorResponse."""
    details = []
    for error in exc.errors():
        # Get field name location
        loc = error.get("loc", [])
        # We clean the location string (omit 'body' or 'query' prefix)
        field = ".".join(str(part) for part in loc[1:]) if len(loc) > 1 else str(loc[0]) if loc else "unknown"
        details.append(
            {
                "field": field,
                "message": error.get("msg", "Validation error"),
                "type": error.get("type", "value_error"),
            }
        )

    message = (
        "Invalid details supplied" if request.method == "POST" else "The request didn't supply all the necessary data"
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": message,
            "details": details,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Format standard HTTPExceptions to return {"message": message} per OpenAPI."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Format general unhandled exceptions conforming to ErrorResponse."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred"},
    )

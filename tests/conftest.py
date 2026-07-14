"""Pytest fixtures and configuration.

Sets up an isolated, in-memory SQLite database, overrides the get_db dependency
for FastAPI, provides a TestClient, and exposes mock users, accounts, and
JWT authentication helpers.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token
from app.database import Base, get_db
from app.main import app

# Create in-memory SQLite engine for tests
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db")
def db_fixture() -> Generator[Session, None, None]:
    """Provide a clean, transaction-isolated database session per test.

    Yields:
        Session: Active SQLAlchemy session.
    """
    # Create all database tables
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all database tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def client_fixture(db: Session) -> Generator[TestClient, None, None]:
    """Provide a TestClient with overridden get_db dependency.

    Args:
        db: The isolated database session.

    Yields:
        TestClient: Fastapi TestClient.
    """

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user_data")
def test_user_data_fixture() -> dict:
    """Provide dictionary containing valid user registration payload."""
    return {
        "name": "John Doe",
        "address": {
            "line1": "123 High Street",
            "line2": "Flat 4B",
            "line3": "The Mews",
            "town": "London",
            "county": "Greater London",
            "postcode": "SW1A 1AA",
        },
        "phoneNumber": "+447700900077",
        "email": "john.doe@example.com",
        "password": "SecurePassword123!",
    }


@pytest.fixture(name="created_user")
def created_user_fixture(client: TestClient, test_user_data: dict) -> dict:
    """Create a user via API and return the user details dictionary.

    Args:
        client: TestClient instance.
        test_user_data: Dictionary representing create payload.

    Returns:
        dict: User record from API.
    """
    response = client.post("/v1/users", json=test_user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(created_user: dict) -> dict:
    """Generate authentication headers containing a signed JWT for created_user.

    Args:
        created_user: Details of the created user.

    Returns:
        dict: Headers dictionary with Authorization Bearer.
    """
    user_id = created_user["id"]
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}

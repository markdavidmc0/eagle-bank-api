"""Unit tests for user endpoints.

Verifies registration, fetching, updating, and deleting of users,
ensuring security checks and validation formats.
"""

from fastapi.testclient import TestClient

from app.auth import create_access_token


def test_create_user_success(client: TestClient, test_user_data: dict) -> None:
    """Test creating a user successfully.

    Given: A payload containing valid user registration details.
    When: A POST request is sent to /v1/users.
    Then: The server returns 201 Created and the created user schema.
    """
    response = client.post("/v1/users", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["id"].startswith("usr-")
    assert data["name"] == test_user_data["name"]
    assert data["email"] == test_user_data["email"]
    assert data["phoneNumber"] == test_user_data["phoneNumber"]
    assert data["address"]["line1"] == test_user_data["address"]["line1"]
    assert "createdTimestamp" in data
    assert "updatedTimestamp" in data


def test_create_user_duplicate_email(client: TestClient, created_user: dict, test_user_data: dict) -> None:
    """Test creating a user with a duplicate email address.

    Given: An email address is already registered in the system.
    When: Another user attempts to register with the same email.
    Then: The request fails with 400 Bad Request and details.
    """
    response = client.post("/v1/users", json=test_user_data)
    assert response.status_code == 400
    data = response.json()
    assert "message" in data
    assert "details" in data
    assert len(data["details"]) == 1
    assert data["details"][0]["field"] == "email"


def test_create_user_invalid_phone(client: TestClient, test_user_data: dict) -> None:
    """Test creating a user with an invalid phone format.

    Given: A phone number that does not match E.164 pattern.
    When: The user registration request is processed.
    Then: The request fails with 400 Bad Request.
    """
    payload = test_user_data.copy()
    payload["phoneNumber"] = "07700900077"  # No leading '+' and country code

    response = client.post("/v1/users", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "details" in data
    assert data["details"][0]["field"] == "phoneNumber"


def test_fetch_user_profile_success(client: TestClient, created_user: dict, auth_headers: dict) -> None:
    """Test fetching the authenticated user's own profile.

    Given: An authenticated user.
    When: They send a GET request to /v1/users/{userId} with their own ID.
    Then: The server returns 200 OK and their profile details.
    """
    user_id = created_user["id"]
    response = client.get(f"/v1/users/{user_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == user_id


def test_fetch_user_profile_forbidden(client: TestClient, created_user: dict, auth_headers: dict) -> None:
    """Test fetching a different user's profile.

    Given: An authenticated user.
    When: They attempt to access another user's profile ID.
    Then: The request is blocked with 403 Forbidden.
    """
    other_user_id = "usr-other123"
    response = client.get(f"/v1/users/{other_user_id}", headers=auth_headers)
    assert response.status_code == 403
    assert response.json()["message"] == "The user is not allowed to access the transaction"


def test_fetch_user_not_found(client: TestClient) -> None:
    """Test fetching a non-existent user profile with a valid JWT structure.

    Given: An authenticated user whose record is missing from the database.
    When: They send a GET request with their ID.
    Then: The server returns 404 Not Found.
    """
    missing_id = "usr-missing123"
    token = create_access_token(missing_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/v1/users/{missing_id}", headers=headers)
    assert response.status_code == 404
    assert response.json()["message"] == "User was not found"


def test_update_user_success(client: TestClient, created_user: dict, auth_headers: dict) -> None:
    """Test updating the user profile successfully.

    Given: An authenticated user.
    When: They send a PATCH request to update their name and address.
    Then: The details are updated, returning 200 OK.
    """
    user_id = created_user["id"]
    update_payload = {
        "name": "Jane Doe",
        "address": {
            "line1": "456 High Street",
            "town": "Manchester",
            "county": "Greater Manchester",
            "postcode": "M1 1AA",
        },
    }

    response = client.patch(f"/v1/users/{user_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["address"]["line1"] == "456 High Street"
    assert data["address"]["line2"] is None  # Omitted from payload defaults to None
    assert data["email"] == created_user["email"]  # Unchanged


def test_delete_user_success(client: TestClient, created_user: dict, auth_headers: dict) -> None:
    """Test deleting the user profile successfully.

    Given: An authenticated user with no associated bank accounts.
    When: They send a DELETE request to their own profile ID.
    Then: The user profile is deleted, returning 204 No Content.
    """
    user_id = created_user["id"]
    response = client.delete(f"/v1/users/{user_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify the user no longer exists (returns 404)
    get_response = client.get(f"/v1/users/{user_id}", headers=auth_headers)
    assert get_response.status_code == 404

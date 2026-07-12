"""Unit tests for bank account endpoints.

Verifies creation, listing, fetching, updating, and deleting of accounts,
ensuring security checks and foreign key constraints on user deletion.
"""

from fastapi.testclient import TestClient

from app.auth import create_access_token


def test_create_account_success(client: TestClient, auth_headers: dict) -> None:
    """Test creating a bank account successfully.

    Given: An authenticated user.
    When: They send a POST request to /v1/accounts.
    Then: An account is created starting with 01, balance 0.00, sort code 10-10-10.
    """
    payload = {"name": "My Savings", "accountType": "personal"}
    response = client.post("/v1/accounts", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert "accountNumber" in data
    assert data["accountNumber"].startswith("01")
    assert len(data["accountNumber"]) == 8
    assert data["sortCode"] == "10-10-10"
    assert data["name"] == "My Savings"
    assert data["accountType"] == "personal"
    assert data["balance"] == 0.00
    assert data["currency"] == "GBP"


def test_list_accounts(client: TestClient, auth_headers: dict) -> None:
    """Test listing accounts owned by user.

    Given: An authenticated user.
    When: They list accounts initially and then after creating one.
    Then: The list shows correct count and account details.
    """
    # 1. Initial list should be empty
    response = client.get("/v1/accounts", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["accounts"] == []

    # 2. Create an account
    client.post(
        "/v1/accounts",
        json={"name": "Primary", "accountType": "personal"},
        headers=auth_headers,
    )

    # 3. List accounts again
    list_response = client.get("/v1/accounts", headers=auth_headers)
    assert list_response.status_code == 200
    accounts = list_response.json()["accounts"]
    assert len(accounts) == 1
    assert accounts[0]["name"] == "Primary"


def test_fetch_account_success(client: TestClient, created_user: dict, auth_headers: dict) -> None:
    """Test fetching a bank account successfully.

    Given: An authenticated user who owns a bank account.
    When: They request details of that account.
    Then: The server returns 200 OK and account details.
    """
    # Create account
    create_resp = client.post(
        "/v1/accounts",
        json={"name": "Checking", "accountType": "personal"},
        headers=auth_headers,
    )
    account_number = create_resp.json()["accountNumber"]

    # Fetch account
    response = client.get(f"/v1/accounts/{account_number}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["accountNumber"] == account_number


def test_fetch_account_forbidden(client: TestClient, auth_headers: dict) -> None:
    """Test fetching someone else's bank account.

    Given: An authenticated user.
    When: They attempt to fetch an account owned by another user.
    Then: The server blocks the request with 403 Forbidden.
    """
    # Create an account under a different user
    other_user_id = "usr-other999"
    other_token = create_access_token(other_user_id)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Register the other user first so DB relationships don't fail foreign keys
    client.post(
        "/v1/users",
        json={
            "name": "Other User",
            "address": {
                "line1": "999 St",
                "town": "City",
                "county": "Cty",
                "postcode": "PC1",
            },
            "phoneNumber": "+447700900099",
            "email": "other.user@example.com",
        },
    )

    create_resp = client.post(
        "/v1/accounts",
        json={"name": "Secret Account", "accountType": "personal"},
        headers=other_headers,
    )
    other_account_num = create_resp.json()["accountNumber"]

    # Try to fetch using the first user's auth_headers
    response = client.get(f"/v1/accounts/{other_account_num}", headers=auth_headers)
    assert response.status_code == 403
    assert response.json()["message"] == "The user is not allowed to access the bank account details"


def test_update_account(client: TestClient, auth_headers: dict) -> None:
    """Test updating account name and type.

    Given: An authenticated owner of a bank account.
    When: They modify the account details.
    Then: The server updates and returns 200 OK.
    """
    create_resp = client.post(
        "/v1/accounts",
        json={"name": "Saver", "accountType": "personal"},
        headers=auth_headers,
    )
    account_number = create_resp.json()["accountNumber"]

    response = client.patch(
        f"/v1/accounts/{account_number}",
        json={"name": "Premium Saver"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Premium Saver"


def test_delete_account_success(client: TestClient, auth_headers: dict) -> None:
    """Test deleting a bank account.

    Given: An authenticated owner of an account.
    When: They request to delete the account.
    Then: The account is deleted, returning 204 No Content.
    """
    create_resp = client.post(
        "/v1/accounts",
        json={"name": "Temporary", "accountType": "personal"},
        headers=auth_headers,
    )
    account_number = create_resp.json()["accountNumber"]

    # Delete
    del_resp = client.delete(f"/v1/accounts/{account_number}", headers=auth_headers)
    assert del_resp.status_code == 204

    # Verify no longer exists
    get_resp = client.get(f"/v1/accounts/{account_number}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_delete_user_conflict_linked_account(client: TestClient, created_user: dict, auth_headers: dict) -> None:
    """Test user deletion constraint when associated with a bank account.

    Given: An authenticated user who has an active bank account.
    When: They attempt to delete their user profile.
    Then: The request fails with 409 Conflict.
    """
    # Create account
    client.post(
        "/v1/accounts",
        json={"name": "Checking", "accountType": "personal"},
        headers=auth_headers,
    )

    # Attempt to delete user
    user_id = created_user["id"]
    response = client.delete(f"/v1/users/{user_id}", headers=auth_headers)
    assert response.status_code == 409
    assert response.json()["message"] == "A user cannot be deleted when they are associated with a bank account"

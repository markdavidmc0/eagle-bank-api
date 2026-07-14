"""Unit tests for transaction endpoints.

Verifies deposits, withdrawals, balance limits, insufficient funds,
listing transactions, fetching transactions, and security boundaries.
"""

from fastapi.testclient import TestClient


def test_deposit_and_withdrawal_flow(client: TestClient, auth_headers: dict) -> None:
    """Test depositing and withdrawing money.

    Given: An authenticated bank account owner with 0.00 GBP balance.
    When: They deposit 100.50 GBP and then withdraw 40.20 GBP.
    Then: The balance increases to 100.50, then decreases to 60.30, and transactions are logged.
    """
    # 1. Create account
    create_resp = client.post(
        "/v1/accounts",
        json={"name": "Wallet", "accountType": "personal"},
        headers=auth_headers,
    )
    account_number = create_resp.json()["accountNumber"]

    # 2. Deposit 100.50 GBP
    deposit_payload = {"amount": 100.50, "currency": "GBP", "type": "deposit", "reference": "Salary"}
    dep_resp = client.post(
        f"/v1/accounts/{account_number}/transactions",
        json=deposit_payload,
        headers=auth_headers,
    )
    assert dep_resp.status_code == 201
    dep_data = dep_resp.json()
    assert dep_data["id"].startswith("tan-")
    assert dep_data["amount"] == 100.50
    assert dep_data["type"] == "deposit"
    assert dep_data["reference"] == "Salary"
    assert "userId" in dep_data

    # Check account balance is updated
    acc_resp = client.get(f"/v1/accounts/{account_number}", headers=auth_headers)
    assert acc_resp.json()["balance"] == 100.50

    # 3. Withdraw 40.20 GBP
    withdrawal_payload = {
        "amount": 40.20,
        "currency": "GBP",
        "type": "withdrawal",
        "reference": "Coffee",
    }
    with_resp = client.post(
        f"/v1/accounts/{account_number}/transactions",
        json=withdrawal_payload,
        headers=auth_headers,
    )
    assert with_resp.status_code == 201
    with_data = with_resp.json()
    assert with_data["amount"] == 40.20
    assert with_data["type"] == "withdrawal"

    # Check balance is updated
    acc_resp = client.get(f"/v1/accounts/{account_number}", headers=auth_headers)
    assert acc_resp.json()["balance"] == 60.30


def test_deposit_exceeds_maximum_balance(client: TestClient, auth_headers: dict) -> None:
    """Test depositing that would make the balance exceed 10000.00.

    Given: An account with 0.00 balance.
    When: A deposit of 10000.01 GBP is attempted.
    Then: The request fails with 400 Bad Request.
    """
    create_resp = client.post(
        "/v1/accounts",
        json={"name": "Wallet", "accountType": "personal"},
        headers=auth_headers,
    )
    account_number = create_resp.json()["accountNumber"]

    deposit_payload = {
        "amount": 10000.01,
        "currency": "GBP",
        "type": "deposit",
        "reference": "Too much",
    }
    response = client.post(
        f"/v1/accounts/{account_number}/transactions",
        json=deposit_payload,
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert response.json()["message"] == "Invalid details supplied"


def test_withdrawal_insufficient_funds(client: TestClient, auth_headers: dict) -> None:
    """Test withdrawing more money than available balance.

    Given: An account with 50.00 GBP balance.
    When: A withdrawal of 50.01 GBP is attempted.
    Then: The request fails with 422 Unprocessable Entity and Insufficient funds message.
    """
    create_resp = client.post(
        "/v1/accounts",
        json={"name": "Wallet", "accountType": "personal"},
        headers=auth_headers,
    )
    account_number = create_resp.json()["accountNumber"]

    # Deposit 50.00 GBP
    client.post(
        f"/v1/accounts/{account_number}/transactions",
        json={"amount": 50.00, "currency": "GBP", "type": "deposit"},
        headers=auth_headers,
    )

    # Attempt withdrawal of 50.01 GBP
    withdrawal_payload = {"amount": 50.01, "currency": "GBP", "type": "withdrawal"}
    response = client.post(
        f"/v1/accounts/{account_number}/transactions",
        json=withdrawal_payload,
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert response.json()["message"] == "Insufficient funds to process transaction"


def test_list_and_fetch_transactions(client: TestClient, auth_headers: dict) -> None:
    """Test listing and fetching transactions by ID.

    Given: An account with multiple transactions.
    When: The owner lists all transactions or fetches a specific one.
    Then: The details are returned with 200 OK.
    """
    # Create account
    create_resp = client.post(
        "/v1/accounts",
        json={"name": "Wallet", "accountType": "personal"},
        headers=auth_headers,
    )
    account_number = create_resp.json()["accountNumber"]

    # Execute 2 deposits
    t1 = client.post(
        f"/v1/accounts/{account_number}/transactions",
        json={"amount": 10.00, "currency": "GBP", "type": "deposit", "reference": "A"},
        headers=auth_headers,
    ).json()
    client.post(
        f"/v1/accounts/{account_number}/transactions",
        json={"amount": 20.00, "currency": "GBP", "type": "deposit", "reference": "B"},
        headers=auth_headers,
    )

    # List transactions
    list_resp = client.get(f"/v1/accounts/{account_number}/transactions", headers=auth_headers)
    assert list_resp.status_code == 200
    transactions = list_resp.json()["transactions"]
    assert len(transactions) == 2

    # Fetch individual transaction
    t1_id = t1["id"]
    fetch_resp = client.get(f"/v1/accounts/{account_number}/transactions/{t1_id}", headers=auth_headers)
    assert fetch_resp.status_code == 200
    assert fetch_resp.json()["id"] == t1_id
    assert fetch_resp.json()["reference"] == "A"


def test_fetch_transaction_not_found(client: TestClient, auth_headers: dict) -> None:
    """Test fetching a non-existent transaction.

    Given: An active bank account.
    When: A transaction request is made with a missing transaction ID.
    Then: The request fails with 404 Not Found and 'Bank account was not found' message.
    """
    create_resp = client.post(
        "/v1/accounts",
        json={"name": "Wallet", "accountType": "personal"},
        headers=auth_headers,
    )
    account_number = create_resp.json()["accountNumber"]

    response = client.get(f"/v1/accounts/{account_number}/transactions/tan-missing", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Bank account was not found"

# Eagle Bank API

[![CI Pipeline](https://github.com/markdavidmc0/eagle-bank-api/actions/workflows/ci.yml/badge.svg)](https://github.com/markdavidmc0/eagle-bank-api/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-green.svg)](https://fastapi.tiangolo.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A highly secure, robust, and spec-compliant FastAPI REST API designed for **Eagle Bank**. This API manages user profiles, bank accounts, and concurrency-safe monetary ledger transactions (deposits/withdrawals) with full compliance to the OpenAPI 3.1.0 specification.

---

## ✨ Features

- **Robust User Management**: Detailed user profile registration, secure updates, lookups, and deletion protections (e.g., preventing deletion when linked accounts are active).
- **Secure Ledger Transactions**: Concurrency-safe deposit and withdrawal endpoints backed by pessimistic row locking (`with_for_update`) to prevent race conditions on account balances.
- **Bcrypt Password Hashing**: Ensures industry-standard credential security by salting and hashing user passwords using bcrypt before persisting them to the database.
- **Stateless Bearer JWT Authentication**: Secures sensitive endpoints with HS256-signed JSON Web Tokens.
- **Strict Spec-Compliant Validation**: Custom Pydantic v2 schemas and validators rounding monetary attributes automatically, formatting nested structures, and standardizing ISO-8601 UTC timestamps.
- **Dynamic 400 Error Formatting**: Intercepts structural failures and returns tailored messages (`"Invalid details supplied"` for creations, `"The request didn't supply all the necessary data"` for updates/queries).

---

## 🛠️ Tooling & Prerequisites

- **Python**: `>=3.12`
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (for ultra-fast environment synchronization and dependency management)
- **Database**: SQLite (built-in, zero-setup required)
- **Linter & Formatter**: [Ruff](https://github.com/astral-sh/ruff)

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/markdavidmc0/eagle-bank-api.git
cd eagle-bank-api
```

### 2. Install Dependencies & Setup Environment
Use `uv` to automatically create a virtual environment and synchronize dependencies:
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies and create .venv
uv sync
```

### 3. Run the Development Server
Start the local server using `uvicorn`:
```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Access the API documentation (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Access the ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Testing & Verification

The testing suite utilizes **Pytest** with an isolated, in-memory SQLite database for unit tests, combined with **Schemathesis** for automated, spec-compliant API contract testing.

### Run the Complete Test Suite
```bash
uv run pytest
```

### Run API Contract Tests Only
```bash
uv run pytest tests/test_api.py
```

---

## 🧹 Code Quality & Style

This codebase adopts the **Google Docstring style** and uses **Ruff** for linting, style formatting, and import sorting.

### Run Linter Checks
```bash
uv run ruff check .
```

### Run Code Formatter
```bash
uv run ruff format .
```

---

## 🔒 Security & Concurrency Design

### Stateless Bearer JWT Flow
All private, profile-scoped endpoints require authorization. To access them:
1. Register a user at `POST /v1/users` with a secure password (minimum 8 characters).
2. Authenticate with credentials (email/password) at `POST /v1/auth/login` to obtain an `accessToken`.
3. Pass the token as a standard Bearer header on all subsequent requests:
   `Authorization: Bearer <JWT_TOKEN>`

Password security is strictly enforced at the database level by storing salted bcrypt hashes instead of plain-text passwords.

### Pessimistic Concurrency Lock
To avoid balance race conditions, the API secures database rows before modifying balances:
```python
# app/crud.py
account = db.scalar(
    select(BankAccount)
    .where(BankAccount.accountNumber == account_number)
    .with_for_update() # Row lock
)
```
This guarantees serial execution of competing balance operations on the same bank account.

---

## 🔗 API Endpoints Overview

| Method | Endpoint | Description | Auth Required | Implementation Reference |
|---|---|---|---|---|
| `POST` | `/v1/users` | Register a new user with password | No | [app/routers/users.py:L17-36](app/routers/users.py#L17-36) |
| `POST` | `/v1/auth/login` | Authenticate credentials and get JWT token | No | [app/routers/auth.py:L18-40](app/routers/auth.py#L18-40) |
| `GET` | `/v1/users/{userId}` | Fetch a user's details | Yes (Own Profile) | [app/routers/users.py:L39-75](app/routers/users.py#L39-75) |
| `PATCH` | `/v1/users/{userId}` | Update profile details | Yes (Own Profile) | [app/routers/users.py:L78-116](app/routers/users.py#L78-116) |
| `DELETE` | `/v1/users/{userId}` | Delete a user profile | Yes (Own Profile) | [app/routers/users.py:L119-154](app/routers/users.py#L119-154) |
| `POST` | `/v1/accounts` | Open a new bank account | Yes | [app/routers/accounts.py:L18-39](app/routers/accounts.py#L18-39) |
| `GET` | `/v1/accounts` | List accounts belonging to user | Yes | [app/routers/accounts.py:L42-62](app/routers/accounts.py#L42-62) |
| `GET` | `/v1/accounts/{accountNumber}` | Fetch specific account | Yes (Owner Only) | [app/routers/accounts.py:L65-102](app/routers/accounts.py#L65-102) |
| `PATCH` | `/v1/accounts/{accountNumber}` | Update account details | Yes (Owner Only) | [app/routers/accounts.py:L105-137](app/routers/accounts.py#L105-137) |
| `DELETE` | `/v1/accounts/{accountNumber}` | Close bank account | Yes (Owner Only) | [app/routers/accounts.py:L140-173](app/routers/accounts.py#L140-173) |
| `POST` | `/v1/accounts/{accountNumber}/transactions` | Create deposit/withdrawal | Yes (Owner Only) | [app/routers/accounts.py:L177-200](app/routers/accounts.py#L177-200) |
| `GET` | `/v1/accounts/{accountNumber}/transactions` | List account transactions | Yes (Owner Only) | [app/routers/accounts.py:L203-225](app/routers/accounts.py#L203-225) |
| `GET` | `/v1/accounts/{accountNumber}/transactions/{transactionId}` | Fetch single transaction | Yes (Owner Only) | [app/routers/accounts.py:L228-260](app/routers/accounts.py#L228-260) |

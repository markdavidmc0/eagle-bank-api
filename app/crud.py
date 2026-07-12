"""CRUD (Create, Read, Update, Delete) database operations.

This module encapsulates all database interactions for Users, Bank Accounts,
and Transactions, implementing business logic and authorization checks.
"""

import secrets
import string
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.exceptions import BadRequestException


def generate_id(prefix: str, length: int = 12) -> str:
    """Generate a secure alphanumeric random ID with a prefix.

    Args:
        prefix: Prefix for the ID (e.g., 'usr' or 'tan').
        length: Number of random characters to generate.

    Returns:
        str: Secure, unique ID of the form '<prefix>-<alphanumeric>'.
    """
    alphabet = string.ascii_letters + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}-{suffix}"


def generate_account_number(db: Session) -> str:
    """Generate a unique 8-digit bank account number starting with '01'.

    Args:
        db: Active database session.

    Returns:
        str: Uniquely generated account number.
    """
    while True:
        digits = "".join(secrets.choice(string.digits) for _ in range(6))
        account_number = f"01{digits}"
        # Verify uniqueness in database
        exists = db.scalar(select(models.BankAccount).where(models.BankAccount.accountNumber == account_number))
        if not exists:
            return account_number


# --- User CRUD ---
def create_user(db: Session, request: schemas.CreateUserRequest) -> models.User:
    """Create a new user in the database.

    Args:
        db: Database session.
        request: Schema containing the new user's details.

    Returns:
        models.User: The newly created database user.

    Raises:
        BadRequestException: If email already exists.
    """
    # Check if email is unique
    existing_user = db.scalar(select(models.User).where(models.User.email == request.email))
    if existing_user:
        raise BadRequestException(
            message="Invalid details supplied",
            field="email",
            detail_message="Email address is already registered",
            error_type="value_error.unique",
        )

    user_id = generate_id("usr")
    db_user = models.User(
        id=user_id,
        name=request.name,
        line1=request.address.line1,
        line2=request.address.line2,
        line3=request.address.line3,
        town=request.address.town,
        county=request.address.county,
        postcode=request.address.postcode,
        phoneNumber=request.phoneNumber,
        email=request.email,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: str) -> models.User | None:
    """Retrieve a user by ID.

    Args:
        db: Database session.
        user_id: ID of the user to fetch.

    Returns:
        models.User | None: The user model if found, else None.
    """
    return db.scalar(select(models.User).where(models.User.id == user_id))


def update_user(db: Session, user_id: str, request: schemas.UpdateUserRequest) -> models.User | None:
    """Update user details.

    Args:
        db: Database session.
        user_id: ID of the user to update.
        request: Schema with updated fields.

    Returns:
        models.User | None: The updated user model if found, else None.

    Raises:
        BadRequestException: If updated email is already registered by another user.
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    # If updating email, check for uniqueness conflicts
    if request.email and request.email != db_user.email:
        conflict = db.scalar(select(models.User).where(models.User.email == request.email))
        if conflict:
            raise BadRequestException(
                message="Invalid details supplied",
                field="email",
                detail_message="Email address is already registered",
                error_type="value_error.unique",
            )
        db_user.email = request.email

    if request.name is not None:
        db_user.name = request.name
    if request.phoneNumber is not None:
        db_user.phoneNumber = request.phoneNumber

    # Address nesting
    if request.address:
        db_user.line1 = request.address.line1
        db_user.line2 = request.address.line2
        db_user.line3 = request.address.line3
        db_user.town = request.address.town
        db_user.county = request.address.county
        db_user.postcode = request.address.postcode

    db_user.updatedTimestamp = datetime.now(UTC)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: str) -> bool:
    """Delete a user.

    Args:
        db: Database session.
        user_id: ID of the user to delete.

    Returns:
        bool: True if deleted successfully, False if user does not exist.

    Raises:
        HTTPException: If the user has active bank accounts.
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return False

    # Check for linked bank accounts
    has_accounts = db.scalar(select(models.BankAccount).where(models.BankAccount.userId == user_id))
    if has_accounts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user cannot be deleted when they are associated with a bank account",
        )

    db.delete(db_user)
    db.commit()
    return True


# --- Bank Account CRUD ---
def create_bank_account(db: Session, user_id: str, request: schemas.CreateBankAccountRequest) -> models.BankAccount:
    """Create a new bank account for an authenticated user.

    Args:
        db: Database session.
        user_id: ID of the authenticated user.
        request: Request schema with account details.

    Returns:
        models.BankAccount: The newly created bank account.
    """
    account_number = generate_account_number(db)
    db_account = models.BankAccount(
        accountNumber=account_number,
        name=request.name,
        accountType=request.accountType,
        balance=0.00,
        userId=user_id,
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def list_bank_accounts(db: Session, user_id: str) -> list[models.BankAccount]:
    """List all accounts owned by a user.

    Args:
        db: Database session.
        user_id: ID of the owning user.

    Returns:
        list[models.BankAccount]: List of accounts.
    """
    return list(db.scalars(select(models.BankAccount).where(models.BankAccount.userId == user_id)).all())


def get_bank_account(db: Session, account_number: str) -> models.BankAccount | None:
    """Fetch bank account details by account number.

    Args:
        db: Database session.
        account_number: Account number.

    Returns:
        models.BankAccount | None: Account model if found, else None.
    """
    return db.scalar(select(models.BankAccount).where(models.BankAccount.accountNumber == account_number))


def update_bank_account(
    db: Session,
    account_number: str,
    user_id: str,
    request: schemas.UpdateBankAccountRequest,
) -> models.BankAccount | None:
    """Update bank account details with ownership verification.

    Args:
        db: Database session.
        account_number: Account number.
        user_id: ID of the authenticated user requesting the update.
        request: Request schema with update fields.

    Returns:
        models.BankAccount | None: Updated account if found, else None.

    Raises:
        HTTPException: If user is not the owner (403 Forbidden).
    """
    db_account = get_bank_account(db, account_number)
    if not db_account:
        return None

    if db_account.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not allowed to update the bank account details",
        )

    if request.name is not None:
        db_account.name = request.name
    if request.accountType is not None:
        db_account.accountType = request.accountType

    db_account.updatedTimestamp = datetime.now(UTC)
    db.commit()
    db.refresh(db_account)
    return db_account


def delete_bank_account(db: Session, account_number: str, user_id: str) -> bool:
    """Delete a bank account with ownership verification.

    Args:
        db: Database session.
        account_number: Account number.
        user_id: ID of the authenticated user.

    Returns:
        bool: True if deleted successfully, False if account does not exist.

    Raises:
        HTTPException: If user is not the owner (403 Forbidden).
    """
    db_account = get_bank_account(db, account_number)
    if not db_account:
        return False

    if db_account.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not allowed to delete the bank account details",
        )

    db.delete(db_account)
    db.commit()
    return True


# --- Transaction CRUD ---
def create_transaction(
    db: Session,
    user_id: str,
    account_number: str,
    request: schemas.CreateTransactionRequest,
) -> models.Transaction:
    """Process a transaction on a bank account with concurrency safety.

    Locks the account row for updates to avoid balance race conditions.

    Args:
        db: Database session.
        user_id: ID of the authenticated user.
        account_number: Bank account number.
        request: Transaction details request.

    Returns:
        models.Transaction: The successfully executed transaction.

    Raises:
        HTTPException: 404 if account not found, 403 if unauthorized,
            422 if insufficient funds.
        BadRequestException: 400 if transaction would breach balance limits.
    """
    # Fetch account with row-level lock (with_for_update)
    db_account = db.scalar(
        select(models.BankAccount).where(models.BankAccount.accountNumber == account_number).with_for_update()
    )

    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account was not found",
        )

    # Verify account ownership
    if db_account.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not allowed to access the bank account details",
        )

    # Perform balance arithmetic and validations
    current_balance = db_account.balance
    amount = request.amount

    if request.type == "deposit":
        new_balance = round(current_balance + amount, 2)
        if new_balance > 10000.00:
            raise BadRequestException(
                message="Invalid details supplied",
                field="amount",
                detail_message="Deposit would exceed maximum allowed account balance of 10000.00",
            )
    else:  # withdrawal
        if current_balance < amount:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Insufficient funds to process transaction",
            )
        new_balance = round(current_balance - amount, 2)

    # Perform balance update
    db_account.balance = new_balance
    db_account.updatedTimestamp = datetime.now(UTC)

    # Save transaction record
    transaction_id = generate_id("tan")
    db_transaction = models.Transaction(
        id=transaction_id,
        amount=amount,
        currency=request.currency,
        type=request.type,
        reference=request.reference,
        userId=user_id,
        accountNumber=account_number,
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def list_transactions(db: Session, account_number: str, user_id: str) -> list[models.Transaction]:
    """List all transactions for a specific bank account.

    Args:
        db: Database session.
        account_number: Account number.
        user_id: ID of the authenticated user.

    Returns:
        list[models.Transaction]: List of transaction records.

    Raises:
        HTTPException: 404 if account not found, 403 if unauthorized.
    """
    db_account = get_bank_account(db, account_number)
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account was not found",
        )

    if db_account.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not allowed to access the transactions",
        )

    return list(db_account.transactions)


def get_transaction(db: Session, account_number: str, transaction_id: str, user_id: str) -> models.Transaction | None:
    """Retrieve details of a single transaction.

    Args:
        db: Database session.
        account_number: Account number.
        transaction_id: ID of the transaction.
        user_id: ID of the authenticated user.

    Returns:
        models.Transaction | None: Transaction model if found, else None.

    Raises:
        HTTPException: 404 if account not found, 403 if unauthorized.
    """
    db_account = get_bank_account(db, account_number)
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account was not found",
        )

    if db_account.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not allowed to access the transaction",
        )

    # Fetch transaction belonging to account and matching transaction_id
    return db.scalar(
        select(models.Transaction).where(
            models.Transaction.accountNumber == account_number,
            models.Transaction.id == transaction_id,
        )
    )

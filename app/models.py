"""Database models for Eagle Bank API.

This module defines the SQLAlchemy declarative models for Users,
Bank Accounts, and Transactions, mapping Python classes to SQLite tables.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """SQLAlchemy model representing a User.

    Attributes:
        id: Unique identifier in format 'usr-<alphanumeric>'.
        name: Name of the user.
        line1: Address line 1.
        line2: Address line 2 (optional).
        line3: Address line 3 (optional).
        town: Town/City.
        county: County.
        postcode: Postcode.
        phoneNumber: Phone number in E.164 format.
        email: Unique email address.
        createdTimestamp: DateTime when the user was created.
        updatedTimestamp: DateTime when the user was last updated.
        accounts: Relationship to BankAccounts owned by this user.
    """

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    line1 = Column(String, nullable=False)
    line2 = Column(String, nullable=True)
    line3 = Column(String, nullable=True)
    town = Column(String, nullable=False)
    county = Column(String, nullable=False)
    postcode = Column(String, nullable=False)
    phoneNumber = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    passwordHash = Column(String, nullable=False)
    createdTimestamp = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updatedTimestamp = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    accounts = relationship("BankAccount", back_populates="user", cascade="save-update, merge")


class BankAccount(Base):
    """SQLAlchemy model representing a Bank Account.

    Attributes:
        accountNumber: Unique 8-digit identifier in format '01xxxxxx'.
        sortCode: Sort code (always '10-10-10').
        name: Name of the bank account.
        accountType: Account type (always 'personal').
        balance: Account balance, capped between 0.00 and 10000.00.
        currency: Currency (always 'GBP').
        userId: ID of the user who owns this account.
        createdTimestamp: DateTime when the account was created.
        updatedTimestamp: DateTime when the account was last updated.
        user: Relationship back to the User model.
        transactions: Relationship to Transactions made on this account.
    """

    __tablename__ = "bank_accounts"

    accountNumber = Column(String, primary_key=True, index=True)
    sortCode = Column(String, default="10-10-10", nullable=False)
    name = Column(String, nullable=False)
    accountType = Column(String, default="personal", nullable=False)
    balance = Column(Float, default=0.00, nullable=False)
    currency = Column(String, default="GBP", nullable=False)
    userId = Column(String, ForeignKey("users.id"), nullable=False)
    createdTimestamp = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updatedTimestamp = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


class Transaction(Base):
    """SQLAlchemy model representing a Transaction.

    Attributes:
        id: Unique transaction identifier in format 'tan-<alphanumeric>'.
        amount: Transaction amount.
        currency: Currency (always 'GBP').
        type: Transaction type ('deposit' or 'withdrawal').
        reference: Optional transaction reference string.
        userId: ID of the user who initiated/created this transaction.
        accountNumber: Account number of the bank account this transaction was applied to.
        createdTimestamp: DateTime when the transaction was executed.
        account: Relationship back to the BankAccount model.
    """

    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="GBP", nullable=False)
    type = Column(String, nullable=False)
    reference = Column(String, nullable=True)
    userId = Column(String, ForeignKey("users.id"), nullable=False)
    accountNumber = Column(String, ForeignKey("bank_accounts.accountNumber"), nullable=False)
    createdTimestamp = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    account = relationship("BankAccount", back_populates="transactions")

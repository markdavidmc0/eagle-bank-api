"""Pydantic schemas for request validation and response serialization.

This module defines the validation rules and structural schemas for Users,
Bank Accounts, Transactions, and API error responses, ensuring compliance
with the OpenAPI specification.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator, model_validator


# --- Address Schemas ---
class Address(BaseModel):
    """Pydantic model representing a postal address."""

    line1: str = Field(..., description="First line of the address")
    line2: str | None = Field(default=None, description="Second line of the address")
    line3: str | None = Field(default=None, description="Third line of the address")
    town: str = Field(..., description="Town or City")
    county: str = Field(..., description="County")
    postcode: str = Field(..., description="Postcode")

    model_config = ConfigDict(from_attributes=True)


# --- User Schemas ---
class CreateUserRequest(BaseModel):
    """Schema for creating a new user."""

    name: str = Field(..., description="Name of the user")
    address: Address = Field(..., description="Postal address of the user")
    phoneNumber: str = Field(
        ...,
        pattern=r"^\+[1-9]\d{1,14}$",
        description="E.164 formatted phone number",
    )
    email: EmailStr = Field(..., description="Email address")


class UpdateUserRequest(BaseModel):
    """Schema for updating an existing user."""

    name: str | None = Field(default=None, description="Name of the user")
    address: Address | None = Field(default=None, description="Postal address of the user")
    phoneNumber: str | None = Field(
        default=None,
        pattern=r"^\+[1-9]\d{1,14}$",
        description="E.164 formatted phone number",
    )
    email: EmailStr | None = Field(default=None, description="Email address")


class UserResponse(BaseModel):
    """Schema for returning user details."""

    id: str = Field(..., pattern=r"^usr-[A-Za-z0-9]+$")
    name: str
    address: Address
    phoneNumber: str = Field(..., pattern=r"^\+[1-9]\d{1,14}$")
    email: EmailStr
    createdTimestamp: datetime
    updatedTimestamp: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def package_address(cls, data: Any) -> Any:
        """Repackage flattened address fields from DB into a nested address dictionary."""
        if hasattr(data, "line1"):
            # Check if address already exists on the object
            address_val = getattr(data, "address", None)
            if address_val is None:
                address = {
                    "line1": data.line1,
                    "line2": data.line2,
                    "line3": data.line3,
                    "town": data.town,
                    "county": data.county,
                    "postcode": data.postcode,
                }
                return {
                    "id": data.id,
                    "name": data.name,
                    "phoneNumber": data.phoneNumber,
                    "email": data.email,
                    "createdTimestamp": data.createdTimestamp,
                    "updatedTimestamp": data.updatedTimestamp,
                    "address": address,
                }
        elif isinstance(data, dict):
            if "address" not in data and "line1" in data:
                data["address"] = {
                    "line1": data.pop("line1"),
                    "line2": data.pop("line2", None),
                    "line3": data.pop("line3", None),
                    "town": data.pop("town"),
                    "county": data.pop("county"),
                    "postcode": data.pop("postcode"),
                }
        return data

    @field_serializer("createdTimestamp", "updatedTimestamp")
    def serialize_datetime(self, dt: datetime, _info: Any) -> str:
        """Format datetime as standard ISO 8601 string ending with Z."""
        return dt.isoformat().replace("+00:00", "Z")


# --- Bank Account Schemas ---
class CreateBankAccountRequest(BaseModel):
    """Schema for creating a bank account."""

    name: str = Field(..., min_length=1, description="Account name")
    accountType: Literal["personal"] = Field(..., description="Type of bank account")


class UpdateBankAccountRequest(BaseModel):
    """Schema for updating a bank account."""

    name: str | None = Field(default=None, min_length=1, description="Account name")
    accountType: Literal["personal"] | None = Field(default=None, description="Type of bank account")


class BankAccountResponse(BaseModel):
    """Schema for returning bank account details."""

    accountNumber: str = Field(..., pattern=r"^01\d{6}$")
    sortCode: Literal["10-10-10"] = Field(default="10-10-10")
    name: str
    accountType: Literal["personal"] = Field(default="personal")
    balance: float = Field(..., ge=0.00, le=10000.00)
    currency: Literal["GBP"] = Field(default="GBP")
    createdTimestamp: datetime
    updatedTimestamp: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("balance")
    @classmethod
    def round_balance(cls, value: float) -> float:
        """Round the balance to exactly two decimal places."""
        return round(value, 2)

    @field_serializer("createdTimestamp", "updatedTimestamp")
    def serialize_datetime(self, dt: datetime, _info: Any) -> str:
        """Format datetime as standard ISO 8601 string ending with Z."""
        return dt.isoformat().replace("+00:00", "Z")


class ListBankAccountsResponse(BaseModel):
    """Schema for returning a list of bank accounts."""

    accounts: list[BankAccountResponse]


# --- Transaction Schemas ---
class CreateTransactionRequest(BaseModel):
    """Schema for creating a bank transaction."""

    amount: float = Field(..., ge=0.00, le=10000.00)
    currency: Literal["GBP"] = Field(..., description="Currency (always GBP)")
    type: Literal["deposit", "withdrawal"] = Field(..., description="Transaction type")
    reference: str | None = Field(default=None, description="Optional transaction reference")

    @field_validator("amount")
    @classmethod
    def round_amount(cls, value: float) -> float:
        """Round the transaction amount to exactly two decimal places."""
        return round(value, 2)


class TransactionResponse(BaseModel):
    """Schema for returning transaction details."""

    id: str = Field(..., pattern=r"^tan-[A-Za-z0-9]+$")
    amount: float = Field(..., ge=0.00, le=10000.00)
    currency: Literal["GBP"] = Field(default="GBP")
    type: Literal["deposit", "withdrawal"]
    reference: str | None = Field(default=None)
    userId: str = Field(..., pattern=r"^usr-[A-Za-z0-9]+$")
    createdTimestamp: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("amount")
    @classmethod
    def round_amount(cls, value: float) -> float:
        """Round the transaction amount to exactly two decimal places."""
        return round(value, 2)

    @field_serializer("createdTimestamp")
    def serialize_datetime(self, dt: datetime, _info: Any) -> str:
        """Format datetime as standard ISO 8601 string ending with Z."""
        return dt.isoformat().replace("+00:00", "Z")


class ListTransactionsResponse(BaseModel):
    """Schema for returning a list of transaction details."""

    transactions: list[TransactionResponse]


# --- Error Schemas ---
class ErrorResponse(BaseModel):
    """Schema for standard error responses."""

    message: str


class BadRequestErrorResponseDetail(BaseModel):
    """Schema for detailed validation error fields."""

    field: str
    message: str
    type: str


class BadRequestErrorResponse(BaseModel):
    """Schema for validation and request bad data responses."""

    message: str
    details: list[BadRequestErrorResponseDetail]

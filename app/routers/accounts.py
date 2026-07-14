"""Router for Bank Account and Transaction endpoints.

Exposes endpoints to create, fetch, list, update, and delete bank accounts,
and to create, fetch, and list transactions associated with those accounts.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import get_current_user_id
from app.database import get_db

router = APIRouter(prefix="/v1/accounts", tags=["account", "transaction"])


# --- Bank Account Endpoints ---
@router.post(
    "",
    response_model=schemas.BankAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bank account",
)
def create_account(
    request: schemas.CreateBankAccountRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> schemas.BankAccountResponse:
    """Create a new bank account.

    Args:
        request: Schema with new account details.
        current_user_id: ID of the currently authenticated user.
        db: Active database session.

    Returns:
        schemas.BankAccountResponse: Created bank account details.
    """
    return crud.create_bank_account(db, current_user_id, request)


@router.get(
    "",
    response_model=schemas.ListBankAccountsResponse,
    status_code=status.HTTP_200_OK,
    summary="List bank accounts",
)
def list_accounts(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> schemas.ListBankAccountsResponse:
    """List all accounts belonging to the authenticated user.

    Args:
        current_user_id: ID of the currently authenticated user.
        db: Active database session.

    Returns:
        schemas.ListBankAccountsResponse: List of bank accounts.
    """
    accounts = crud.list_bank_accounts(db, current_user_id)
    return schemas.ListBankAccountsResponse(accounts=accounts)


@router.get(
    "/{accountNumber}",
    response_model=schemas.BankAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch bank account by account number",
)
def fetch_account(
    accountNumber: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> schemas.BankAccountResponse:
    """Fetch bank account by account number.

    Args:
        accountNumber: Account number of the bank account.
        current_user_id: ID of the currently authenticated user.
        db: Active database session.

    Returns:
        schemas.BankAccountResponse: Bank account details.

    Raises:
        HTTPException: 404 if not found, 403 if unauthorized.
    """
    db_account = crud.get_bank_account(db, accountNumber)
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account was not found",
        )

    if db_account.userId != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not allowed to access the bank account details",
        )

    return db_account


@router.patch(
    "/{accountNumber}",
    response_model=schemas.BankAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Update bank account by account number",
)
def update_account(
    accountNumber: str,
    request: schemas.UpdateBankAccountRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> schemas.BankAccountResponse:
    """Update bank account by account number.

    Args:
        accountNumber: Account number of the bank account.
        request: Updated account fields.
        current_user_id: ID of the currently authenticated user.
        db: Active database session.

    Returns:
        schemas.BankAccountResponse: Updated bank account details.

    Raises:
        HTTPException: 404 if not found, 403 if unauthorized.
    """
    db_account = crud.update_bank_account(db, accountNumber, current_user_id, request)
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account was not found",
        )
    return db_account


@router.delete(
    "/{accountNumber}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete bank account by account number",
)
def delete_account(
    accountNumber: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Response:
    """Delete bank account by account number.

    Args:
        accountNumber: Account number of the bank account.
        current_user_id: ID of the currently authenticated user.
        db: Active database session.

    Returns:
        Response: 204 No Content response on success.

    Raises:
        HTTPException: 404 if not found, 403 if unauthorized.
    """
    deleted = crud.delete_bank_account(db, accountNumber, current_user_id)
    if not deleted:
        # Check if it actually existed
        db_account = crud.get_bank_account(db, accountNumber)
        if not db_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account was not found",
            )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Transaction Endpoints ---
@router.post(
    "/{accountNumber}/transactions",
    response_model=schemas.TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a transaction",
)
def create_transaction(
    accountNumber: str,
    request: schemas.CreateTransactionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> schemas.TransactionResponse:
    """Create a new transaction (deposit/withdrawal) on a bank account.

    Args:
        accountNumber: Account number of the bank account.
        request: Transaction details request.
        current_user_id: ID of the currently authenticated user.
        db: Active database session.

    Returns:
        schemas.TransactionResponse: Created transaction details.
    """
    return crud.create_transaction(db, current_user_id, accountNumber, request)


@router.get(
    "/{accountNumber}/transactions",
    response_model=schemas.ListTransactionsResponse,
    status_code=status.HTTP_200_OK,
    summary="List transactions",
)
def list_transactions(
    accountNumber: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> schemas.ListTransactionsResponse:
    """List all transactions for a specific bank account.

    Args:
        accountNumber: Account number of the bank account.
        current_user_id: ID of the currently authenticated user.
        db: Active database session.

    Returns:
        schemas.ListTransactionsResponse: List of transaction details.
    """
    transactions = crud.list_transactions(db, accountNumber, current_user_id)
    return schemas.ListTransactionsResponse(transactions=transactions)


@router.get(
    "/{accountNumber}/transactions/{transactionId}",
    response_model=schemas.TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch transaction by ID",
)
def fetch_transaction(
    accountNumber: str,
    transactionId: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> schemas.TransactionResponse:
    """Fetch a single transaction by ID.

    Args:
        accountNumber: Account number of the bank account.
        transactionId: ID of the transaction to fetch.
        current_user_id: ID of the currently authenticated user.
        db: Active database session.

    Returns:
        schemas.TransactionResponse: Transaction details.

    Raises:
        HTTPException: 404 if not found (or account not found).
    """
    db_transaction = crud.get_transaction(db, accountNumber, transactionId, current_user_id)
    if not db_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account was not found",
        )
    return db_transaction

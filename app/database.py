"""Database connection and session management.

This module initializes the SQLAlchemy engine, configures session factories,
and provides a dependency to acquire a database session per request.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.session import Session

from app.config import settings

# For SQLite, check_same_thread needs to be False to support multithreaded requests in FastAPI.
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session.

    Yields:
        Session: A transaction-scoped SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

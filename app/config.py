"""Configuration module for Eagle Bank API.

This module loads environment variables and provides a settings class
for configuring the application's database, security, and other settings.
"""

import os


class Settings:
    """Application settings class.

    Attributes:
        DATABASE_URL: The connection string for the database.
        JWT_SECRET_KEY: Secret key used to sign JWT tokens.
        JWT_ALGORITHM: Algorithm used for JWT encoding/decoding.
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Lifetime of the JWT token.
    """

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./eagle_bank.db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "eagle_bank_secure_jwt_secret_key_101010")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


settings = Settings()

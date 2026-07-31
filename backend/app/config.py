"""
config.py - Application configuration.

This module reads configuration values from a ".env" file (if one exists)
and provides them to the rest of the application through a single
`settings` object. Keeping configuration in one place makes the project
easy to set up on any machine.

The most important setting is DATABASE_URL. It tells SQLAlchemy which
database to connect to:

    PostgreSQL (recommended for the final project):
        postgresql://USERNAME:PASSWORD@localhost:5432/appointment_db

    SQLite (built into Python, great for a quick demo with no setup):
        sqlite:///./app.db

If no .env file exists, the default values below are used.
"""

from pathlib import Path

from pydantic_settings import BaseSettings

# The BASE_DIR points to the "backend" folder.
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Settings loaded from the .env file (or defaults)."""

    # Database connection string.
    # The default is SQLite so the project runs immediately with zero setup.
    DATABASE_URL: str = "sqlite:///./app.db"

    # Secret key used to sign JWT tokens.
    # IMPORTANT: change this to a long random string for a real deployment.
    SECRET_KEY: str = "dev-secret-key-change-me-in-production"

    # Algorithm used to sign JWT tokens (HS256 = HMAC with SHA-256).
    ALGORITHM: str = "HS256"

    # How long a login token stays valid (in minutes). 1440 = 24 hours.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Tell pydantic-settings where to find the .env file.
    model_config = {"env_file": BASE_DIR / ".env", "env_file_encoding": "utf-8"}


# Create one global settings object that every other module imports.
settings = Settings()

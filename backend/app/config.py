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

    # Groq API settings (ShifaBook AI Health Assistant).
    # The API key is SECRET: it lives ONLY in backend/.env locally and in
    # Railway variables in production - never in React code or on GitHub.
    # Leave the key empty and the AI endpoints return a clear message.
    GROQ_API_KEY: str = ""
    # Model used for text analysis (PDFs/notes) and chat. Text models are
    # fastest for reading documents.
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    # Model used automatically when the patient uploads an IMAGE (JPG/PNG/
    # WEBP). This must be a vision-capable model. Older vision previews
    # (llama-3.2-*-vision-preview) have been decommissioned on Groq.
    # qwen/qwen3.6-27b outputs excessive reasoning; groq/compound is more concise.
    GROQ_VISION_MODEL: str = "groq/compound"

    # Tell pydantic-settings where to find the .env file.
    model_config = {"env_file": BASE_DIR / ".env", "env_file_encoding": "utf-8"}


# Create one global settings object that every other module imports.
settings = Settings()

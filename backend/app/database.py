"""
database.py - Database connection and session management.

This module is the "bridge" between the Python application and the
database. It does three things:

1. Creates the database engine (the connection to PostgreSQL/SQLite).
2. Creates a SessionLocal class used to talk to the database.
3. Provides a Base class that all of our table models inherit from.

The get_db() function is a dependency that FastAPI calls automatically
for every request that needs database access. It opens a fresh session,
gives it to the endpoint, and closes it when the request finishes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# --- 1. Create the engine -------------------------------------------------
# SQLite needs an extra argument so that multiple threads can safely
# share the same database file. PostgreSQL does not need it.
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

# --- 2. Create the session factory ----------------------------------------
# A "session" represents a conversation with the database. We use the
# factory to create one new session per request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 3. Declarative base --------------------------------------------------
# Every table model (Doctor, Patient, Appointment) inherits from Base.
# SQLAlchemy reads the model classes and builds the matching tables.
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session to endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

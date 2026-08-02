"""
deps.py - Shared FastAPI dependencies.

FastAPI "dependencies" are small helper functions that run before an
endpoint. They are the perfect place for authentication checks.

    get_current_patient: reads the token from the request, verifies it,
                         loads the matching Patient, and either returns
                         it or raises 401 Unauthorized.

    get_current_doctor:  same idea, but for doctors.

Because these are dependencies, every protected endpoint only needs to
add one parameter and FastAPI + this code handle the security for it.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .security import decode_access_token

# HTTPBearer tells FastAPI to look for the token in the
# "Authorization: Bearer <token>" header of every request.
bearer_scheme = HTTPBearer(auto_error=False)

# The message returned when a user is not allowed to do something.
CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _get_current_user(credentials, db, expected_role):
    """Shared helper used by both auth dependencies below."""
    # 1. There must be an Authorization header with a token.
    if credentials is None:
        raise CREDENTIALS_ERROR

    # 2. The token must have a valid signature and not be expired.
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        raise CREDENTIALS_ERROR

    user_id = payload.get("sub")
    role = payload.get("role")

    # 3. The token's role must match the role this endpoint requires.
    if role != expected_role or not user_id:
        raise CREDENTIALS_ERROR

    # 4. Load the real user row from the database.
    if expected_role == "doctor":
        user = db.query(models.Doctor).filter(models.Doctor.id == int(user_id)).first()
    else:
        user = db.query(models.Patient).filter(models.Patient.id == int(user_id)).first()

    if user is None:
        raise CREDENTIALS_ERROR

    return user


def get_current_patient(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Dependency that returns the Patient from a valid patient token."""
    return _get_current_user(credentials, db, expected_role="patient")


def get_current_doctor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Dependency that returns the Doctor from a valid doctor token."""
    return _get_current_user(credentials, db, expected_role="doctor")


def get_optional_patient(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Like get_current_patient, but returns None if not logged in.

    Used by public endpoints (e.g. search) that want to personalise the
    response (favourites) without forcing a login.
    """
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        return None
    if payload.get("role") != "patient":
        return None
    return db.query(models.Patient).filter(models.Patient.id == int(payload["sub"])).first()

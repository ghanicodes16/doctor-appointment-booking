"""
routers/auth.py - Authentication endpoints.

This router handles everything related to logging in and registering:

    POST /api/auth/register        -> create a new patient account
    POST /api/auth/login/patient   -> patient login, returns a JWT
    POST /api/auth/login/doctor    -> doctor login, returns a JWT

Note: doctors are NOT allowed to register themselves. Doctor accounts
are created by the database seed script (admin creates them). This is a
common real-world rule and keeps things secure.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _build_token_response(user, role: str) -> schemas.Token:
    """Build the login response: a JWT token plus basic user info."""
    token = create_access_token(user.id, role)
    return schemas.Token(
        access_token=token,
        role=role,
        user={"id": user.id, "name": user.name, "email": user.email},
    )


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register_patient(data: schemas.PatientRegister, db: Session = Depends(get_db)):
    """Create a new patient account and log them in automatically."""
    # Make sure the email is not already used by another patient.
    existing = db.query(models.Patient).filter(models.Patient.email == data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in.",
        )

    # Create the patient row. We store only the bcrypt hash of the password.
    patient = models.Patient(
        name=data.name,
        email=data.email.lower(),
        phone=data.phone,
        password_hash=hash_password(data.password),
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # Log the patient in right away by returning a token.
    return _build_token_response(patient, role="patient")


@router.post("/login/patient", response_model=schemas.Token)
def login_patient(data: schemas.PatientLogin, db: Session = Depends(get_db)):
    """Log a patient in and return a JWT access token."""
    patient = db.query(models.Patient).filter(models.Patient.email == data.email.lower()).first()

    # If the email doesn't exist OR the password is wrong, return the
    # same generic error. This stops attackers from guessing which
    # emails are registered.
    if not patient or not verify_password(data.password, patient.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return _build_token_response(patient, role="patient")


@router.post("/login/doctor", response_model=schemas.Token)
def login_doctor(data: schemas.DoctorLogin, db: Session = Depends(get_db)):
    """Log a doctor in and return a JWT access token."""
    doctor = db.query(models.Doctor).filter(models.Doctor.email == data.email.lower()).first()

    if not doctor or not verify_password(data.password, doctor.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return _build_token_response(doctor, role="doctor")

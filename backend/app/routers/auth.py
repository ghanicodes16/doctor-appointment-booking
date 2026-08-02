"""
routers/auth.py - Authentication endpoints.

    POST /api/auth/register          -> create a new patient account
    POST /api/auth/register/doctor   -> create a new doctor account (self-registration)
    POST /api/auth/login/patient     -> patient login, returns a JWT
    POST /api/auth/login/doctor      -> doctor login, returns a JWT

Doctor accounts are now self-registered by doctors in Pakistan (they
provide their PMDC/PMC licence number etc.). Verification by an admin
is a future-ready step: new accounts get is_verified=False but remain
bookable for this academic version.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import create_access_token, hash_password, verify_password
from ..utils import attach_rating

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _build_token_response(user, role: str, extra: dict | None = None) -> schemas.Token:
    """Build the login response: a JWT token plus basic user info."""
    token = create_access_token(user.id, role)
    user_info = {"id": user.id, "name": user.name, "email": user.email}
    if extra:
        user_info.update(extra)
    return schemas.Token(access_token=token, role=role, user=user_info)


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register_patient(data: schemas.PatientRegister, db: Session = Depends(get_db)):
    """Create a new patient account and log them in automatically."""
    existing = db.query(models.Patient).filter(models.Patient.email == data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in.",
        )

    patient = models.Patient(
        name=data.name,
        email=data.email.lower(),
        phone=data.phone,
        password_hash=hash_password(data.password),
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return _build_token_response(patient, role="patient")


@router.post("/register/doctor", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register_doctor(data: schemas.DoctorRegister, db: Session = Depends(get_db)):
    """Create a new doctor account with a full Pakistan-focused profile."""
    if db.query(models.Doctor).filter(models.Doctor.email == data.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in.",
        )

    # If the doctor also registered as a patient, that is fine - different tables.
    doctor = models.Doctor(
        name=data.name,
        email=data.email.lower(),
        phone=data.phone,
        password_hash=hash_password(data.password),
        pmdc_number=data.pmdc_number,
        gender=data.gender,
        profile_photo=data.profile_photo,
        date_of_birth=data.date_of_birth,
        years_of_experience=data.years_of_experience,
        qualifications=data.qualifications,
        specialization=data.specialization,
        languages=data.languages,          # already joined by the schema validator
        biography=data.biography,
        hospital_name=data.hospital_name,
        clinic_address=data.clinic_address,
        city=data.city,
        province=data.province,
        first_visit_fee=data.first_visit_fee,
        followup_fee=data.followup_fee,
        online_fee=data.online_fee or 0,
        is_verified=False,                 # future admin verification step
        booking_enabled=True,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return _build_token_response(doctor, role="doctor", extra={"city": doctor.city})


@router.post("/login/patient", response_model=schemas.Token)
def login_patient(data: schemas.PatientLogin, db: Session = Depends(get_db)):
    """Log a patient in and return a JWT access token."""
    patient = db.query(models.Patient).filter(models.Patient.email == data.email.lower()).first()
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
    return _build_token_response(doctor, role="doctor", extra={"city": doctor.city})

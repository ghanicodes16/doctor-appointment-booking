"""
schemas.py - Pydantic schemas (data validation).

Pydantic schemas define the *shape* of data that flows in and out of the
API. They have two big advantages:

1. Validation - we describe the rules (required, min length, email
   format...) and Pydantic automatically rejects bad data with a 422
   error.
2. Documentation - FastAPI uses these schemas to generate the automatic
   API documentation at /docs.

We keep separate schemas for "input" (what the client sends) and
"output" (what the API returns). Output schemas never contain password
hashes for safety.
"""

from datetime import date, datetime, time

import enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Auth schemas (login / register input)
# ---------------------------------------------------------------------------

class PatientRegister(BaseModel):
    """Data a new patient must send to create an account."""
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=6, description="Minimum 6 characters")


class PatientLogin(BaseModel):
    """Data a patient sends to log in."""
    email: EmailStr
    password: str


class DoctorLogin(BaseModel):
    """Data a doctor sends to log in."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """The response sent back after a successful login/registration.

    It contains the JWT access token and basic info about the user.
    """
    access_token: str
    token_type: str = "bearer"
    role: str          # "patient" or "doctor"
    user: dict         # name, email, id of the logged-in user


# ---------------------------------------------------------------------------
# User schemas (output)
# ---------------------------------------------------------------------------

class DoctorOut(BaseModel):
    """Public information about a doctor (no password hash)."""
    id: int
    name: str
    email: EmailStr
    phone: str
    specialty: str

    # Allow building this schema straight from a SQLAlchemy model object.
    model_config = ConfigDict(from_attributes=True)


class PatientOut(BaseModel):
    """Public information about a patient (no password hash)."""
    id: int
    name: str
    email: EmailStr
    phone: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Appointment schemas
# ---------------------------------------------------------------------------

class AppointmentCreate(BaseModel):
    """Data a patient sends when booking an appointment."""
    doctor_id: int
    appointment_date: date
    appointment_time: str = Field(pattern=r"^\d{2}:\d{2}$", description="Time in 24h format, e.g. '09:30'")


class AppointmentUpdate(BaseModel):
    """Data a patient sends when rescheduling an appointment."""
    appointment_date: date
    appointment_time: str = Field(pattern=r"^\d{2}:\d{2}$", description="Time in 24h format, e.g. '09:30'")


class AppointmentStatusUpdate(BaseModel):
    """Data a doctor sends to change an appointment status."""
    status: str = Field(description="Either 'Completed' or 'Cancelled'")


class AppointmentOut(BaseModel):
    """Complete appointment information returned to the client.

    It includes the doctor and patient details so the frontend can
    display everything in one card/row without extra API calls.
    """
    id: int
    doctor_id: int
    patient_id: int
    appointment_date: date
    appointment_time: str          # formatted as "HH:MM"
    status: str
    created_at: datetime
    doctor: DoctorOut | None = None
    patient: PatientOut | None = None

    model_config = ConfigDict(from_attributes=True)

    # Convert the database `time` value (e.g. 09:30:00) into "09:30".
    # mode="before" runs BEFORE validation, so the value already arrives
    # as a clean string for the rest of the pipeline.
    @field_validator("appointment_time", mode="before")
    @classmethod
    def serialize_time(cls, value):
        if isinstance(value, time):
            return value.strftime("%H:%M")
        return value

    # Convert the database enum value (AppointmentStatus.BOOKED) into
    # its plain string "Booked".
    @field_validator("status", mode="before")
    @classmethod
    def serialize_status(cls, value):
        if isinstance(value, enum.Enum):
            return value.value
        return value


class AvailableSlotsOut(BaseModel):
    """The list of free time slots for a doctor on a given date."""
    doctor_id: int
    appointment_date: date
    available_slots: list[str]      # e.g. ["09:00", "09:30", ...]

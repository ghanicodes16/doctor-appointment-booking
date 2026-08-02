"""
schemas.py - Pydantic schemas (data validation).

Pydantic schemas define the *shape* of data that flows in and out of the
API. They validate incoming data and document outgoing data. FastAPI
uses them to generate the automatic documentation at /docs.

This file contains schemas for:
    - authentication (register / login)
    - doctor profiles, registration and updates
    - availability management (schedule, unavailable dates, blocked slots)
    - appointments and slots
    - search results
    - favorites, notifications, reviews
    - dashboard analytics
"""

from datetime import date, datetime, time

import enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Regex for Pakistani mobile numbers: 03XX-XXXXXXX or +92 3XX-XXXXXXX
PK_PHONE_PATTERN = r"^(\+92|0092|0)?3\d{2}[-\s]?\d{7}$"


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------

class PatientRegister(BaseModel):
    """Data a new patient sends to create an account."""
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(pattern=PK_PHONE_PATTERN, description="Pakistani number, e.g. 03001234567")
    password: str = Field(min_length=6, description="Minimum 6 characters")


class PatientLogin(BaseModel):
    email: EmailStr
    password: str


class DoctorLogin(BaseModel):
    email: EmailStr
    password: str


class DoctorRegister(BaseModel):
    """Data a doctor sends to self-register (Pakistan healthcare platform)."""
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(pattern=PK_PHONE_PATTERN)
    password: str = Field(min_length=6)
    pmdc_number: str = Field(min_length=3, max_length=50, description="PMDC/PMC registration number")
    gender: str = Field(description="Male, Female or Other")
    date_of_birth: date
    years_of_experience: int = Field(ge=0, le=70)
    qualifications: str = Field(min_length=2, description="e.g. MBBS, FCPS (Cardiology)")
    specialization: str = Field(min_length=2, description="e.g. Cardiologist")
    hospital_name: str = Field(min_length=2)
    clinic_address: str = Field(min_length=5)
    city: str = Field(min_length=2)
    province: str = Field(min_length=2)
    languages: list[str] = Field(min_length=1)
    biography: str = Field(min_length=20, description="A short introduction (at least 20 chars)")
    profile_photo: str | None = None
    first_visit_fee: int = Field(ge=0, description="Fee in PKR")
    followup_fee: int = Field(ge=0, description="Fee in PKR")
    online_fee: int | None = Field(default=0, ge=0, description="0 = not offering online consultation")

    # Convert the list of languages into a comma-separated string for storage.
    @field_validator("languages")
    @classmethod
    def languages_to_string(cls, value):
        if isinstance(value, list):
            return ",".join(value)
        return value


class Token(BaseModel):
    """Login/registration response: the JWT + basic user info."""
    access_token: str
    token_type: str = "bearer"
    role: str                      # "patient" or "doctor"
    user: dict                     # id, name, email (+ city for doctors)


class PatientOut(BaseModel):
    """Public patient profile (no password hash)."""
    id: int
    name: str
    email: EmailStr
    phone: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Doctor schemas
# ---------------------------------------------------------------------------

class DoctorUpdate(BaseModel):
    """Any subset of profile fields a doctor can update."""
    name: str | None = None
    phone: str | None = Field(default=None, pattern=PK_PHONE_PATTERN)
    pmdc_number: str | None = None
    gender: str | None = None
    profile_photo: str | None = None
    date_of_birth: date | None = None
    years_of_experience: int | None = Field(default=None, ge=0, le=70)
    qualifications: str | None = None
    specialization: str | None = None
    languages: list[str] | None = None
    biography: str | None = None
    hospital_name: str | None = None
    clinic_address: str | None = None
    city: str | None = None
    province: str | None = None
    first_visit_fee: int | None = Field(default=None, ge=0)
    followup_fee: int | None = Field(default=None, ge=0)
    online_fee: int | None = Field(default=None, ge=0)

    @field_validator("languages")
    @classmethod
    def languages_to_string(cls, value):
        if isinstance(value, list):
            return ",".join(value)
        return value


class DoctorOut(BaseModel):
    """Public doctor profile returned to the frontend.

    rating_avg / rating_count / is_favorite are computed per-request and
    attached by the backend (they are not stored on the doctor row).
    """
    id: int
    name: str
    email: EmailStr
    phone: str
    pmdc_number: str | None = None
    gender: str | None = None
    profile_photo: str | None = None
    date_of_birth: date | None = None
    years_of_experience: int = 0
    qualifications: str | None = None
    specialization: str
    languages: list[str] = []
    biography: str | None = None
    hospital_name: str | None = None
    clinic_address: str | None = None
    city: str | None = None
    province: str | None = None
    first_visit_fee: int = 0
    followup_fee: int = 0
    online_fee: int = 0
    is_verified: bool = False
    booking_enabled: bool = True
    patients_treated: int = 0
    is_online_available: bool = False
    is_clinic_available: bool = False
    rating_avg: float = 0
    rating_count: int = 0
    is_favorite: bool = False

    model_config = ConfigDict(from_attributes=True)

    # The database stores languages as "English, Urdu" -> expose as a list.
    @field_validator("languages", mode="before")
    @classmethod
    def split_languages(cls, value):
        if isinstance(value, str) and value:
            return [lang.strip() for lang in value.split(",")]
        return value or []


# ---------------------------------------------------------------------------
# Availability schemas
# ---------------------------------------------------------------------------

class ScheduleItem(BaseModel):
    """One working day of a doctor's weekly schedule."""
    day_of_week: int = Field(ge=0, le=6, description="0=Monday ... 6=Sunday")
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    duration_minutes: int = Field(ge=15, le=60)
    is_available: bool = True


class ScheduleIn(BaseModel):
    """The full weekly schedule (list of working days)."""
    schedule: list[ScheduleItem]


class ScheduleOut(BaseModel):
    id: int
    doctor_id: int
    day_of_week: int
    start_time: str
    end_time: str
    duration_minutes: int
    is_available: bool

    model_config = ConfigDict(from_attributes=True)

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def time_to_str(cls, value):
        if isinstance(value, time):
            return value.strftime("%H:%M")
        return value


class UnavailableDateIn(BaseModel):
    date: date
    reason: str = Field(default="Off", max_length=50)


class UnavailableDateOut(BaseModel):
    id: int
    doctor_id: int
    date: date
    reason: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BlockedSlotIn(BaseModel):
    date: date
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")


class BlockedSlotOut(BaseModel):
    id: int
    doctor_id: int
    date: date
    start_time: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("start_time", mode="before")
    @classmethod
    def time_to_str(cls, value):
        if isinstance(value, time):
            return value.strftime("%H:%M")
        return value


# ---------------------------------------------------------------------------
# Appointment schemas
# ---------------------------------------------------------------------------

class AppointmentCreate(BaseModel):
    """Data a patient sends when booking an appointment."""
    doctor_id: int
    appointment_date: date
    appointment_time: str = Field(pattern=r"^\d{2}:\d{2}$")


class AppointmentUpdate(BaseModel):
    """Data a patient sends when rescheduling an appointment."""
    appointment_date: date
    appointment_time: str = Field(pattern=r"^\d{2}:\d{2}$")


class AppointmentStatusUpdate(BaseModel):
    status: str = Field(description="'Completed' or 'Cancelled'")


class AppointmentOut(BaseModel):
    """Complete appointment info incl. doctor/patient + fee details."""
    id: int
    doctor_id: int
    patient_id: int
    appointment_date: date
    appointment_time: str
    status: str
    consultation_fee: int | None = None
    visit_type: str | None = None
    created_at: datetime
    doctor: DoctorOut | None = None
    patient: PatientOut | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("appointment_time", mode="before")
    @classmethod
    def serialize_time(cls, value):
        if isinstance(value, time):
            return value.strftime("%H:%M")
        return value

    @field_validator("status", mode="before")
    @classmethod
    def serialize_status(cls, value):
        if isinstance(value, enum.Enum):
            return value.value
        return value


class AvailableSlotsOut(BaseModel):
    """Free time slots for a doctor on a date.

    is_available=False means the doctor cannot be booked that day (the
    frontend then shows the "Doctor is unavailable" message).
    """
    doctor_id: int
    appointment_date: date
    is_available: bool
    message: str | None = None
    available_slots: list[str]


# ---------------------------------------------------------------------------
# Search / catalog schemas
# ---------------------------------------------------------------------------

class SpecializationOut(BaseModel):
    id: int
    name: str
    keywords: str | None = None
    doctor_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SymptomOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Engagement schemas
# ---------------------------------------------------------------------------

class NotificationOut(BaseModel):
    id: int
    recipient_role: str
    recipient_id: int
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    patient_name: str | None = None
    rating: int
    comment: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Dashboard analytics schemas
# ---------------------------------------------------------------------------

class DoctorStatsOut(BaseModel):
    today_count: int
    upcoming_count: int
    total_patients: int
    monthly_count: int
    weekly: dict                    # {"labels": [...], "counts": [...]}
    total_revenue: int
    monthly_revenue: int
    profile_completion: int         # percentage 0-100


class PatientStatsOut(BaseModel):
    total: int
    upcoming: int
    completed: int
    cancelled: int
    favorite_count: int

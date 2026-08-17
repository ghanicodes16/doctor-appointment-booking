"""
models.py - Database table definitions (ORM models).

ORM stands for "Object Relational Mapping". It lets us work with
database tables as if they were normal Python classes. Each class below
maps to one table in PostgreSQL:

    Doctor             ->  doctors                   (extended profile)
    Patient            ->  patients
    Appointment        ->  appointments
    Specialization     ->  specializations
    Symptom            ->  symptoms
    SymptomMapping     ->  symptom_mappings
    DoctorSchedule     ->  doctor_schedules          (weekly availability)
    UnavailableDate    ->  doctor_unavailable_dates  (vacation / emergency / off)
    BlockedSlot        ->  blocked_slots             (block a specific slot)
    PatientFavorite    ->  patient_favorites
    Notification       ->  notifications
    Review             ->  reviews                   (future-ready)

Relationships:
    - A Doctor has many Appointments, Schedules, UnavailableDates,
      BlockedSlots, Favorites and Reviews (one-to-many).
    - A Patient has many Appointments, Favorites, Reviews (one-to-many).
    - An Appointment belongs to one Doctor and one Patient.
    - A Symptom maps to one Specialization.
"""

from datetime import date, datetime, time

import enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from .database import Base


class AppointmentStatus(str, enum.Enum):
    """The possible states an appointment can be in."""

    BOOKED = "Booked"          # The patient has booked this slot.
    COMPLETED = "Completed"    # The doctor has finished this visit.
    CANCELLED = "Cancelled"    # The appointment was cancelled.


# ---------------------------------------------------------------------------
# Doctor
# ---------------------------------------------------------------------------

class Doctor(Base):
    """Represents a doctor (now with a full Pakistan-focused profile).

    Doctors self-register and provide PMDC/PMC licence info, clinic
    details, fees, working hours and more. They can update their own
    profile and manage their availability.
    """

    __tablename__ = "doctors"

    # --- Core login / identity -----------------------------------------
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)                        # Full name
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # --- Professional details ------------------------------------------
    pmdc_number = Column(String(50), nullable=True)                   # PMDC/PMC registration/licence number
    gender = Column(String(20), nullable=True)                        # Male / Female / Other
    profile_photo = Column(Text, nullable=True)                       # photo URL or base64
    date_of_birth = Column(Date, nullable=True)
    years_of_experience = Column(Integer, default=0, nullable=False)
    qualifications = Column(Text, nullable=True)                      # e.g. "MBBS, FCPS (Cardiology)"
    specialization = Column(String(120), nullable=False, index=True)  # e.g. "Cardiologist"
    languages = Column(String(200), nullable=True)                    # comma separated, e.g. "English, Urdu"
    biography = Column(Text, nullable=True)                           # about the doctor

    # --- Clinic information --------------------------------------------
    hospital_name = Column(String(200), nullable=True)
    clinic_address = Column(String(300), nullable=True)
    city = Column(String(80), nullable=True, index=True)
    province = Column(String(50), nullable=True)                      # Punjab, Sindh, KPK, Balochistan, etc.

    # --- Fees (in PKR) --------------------------------------------------
    first_visit_fee = Column(Integer, default=0, nullable=False)      # First consultation fee
    followup_fee = Column(Integer, default=0, nullable=False)          # Follow-up fee
    online_fee = Column(Integer, default=0, nullable=False)            # Online consultation fee (0 = not offered)

    # --- Status ----------------------------------------------------------
    is_verified = Column(Boolean, default=False, nullable=False)       # admin verification (future admin panel)
    booking_enabled = Column(Boolean, default=True, nullable=False)    # master switch for accepting bookings
    patients_treated = Column(Integer, default=0, nullable=False)      # running counter, incremented on completion

    # --- Relationships ---------------------------------------------------
    appointments = relationship("Appointment", back_populates="doctor")
    schedules = relationship("DoctorSchedule", back_populates="doctor", cascade="all, delete-orphan")
    unavailable_dates = relationship("UnavailableDate", back_populates="doctor", cascade="all, delete-orphan")
    blocked_slots = relationship("BlockedSlot", back_populates="doctor", cascade="all, delete-orphan")
    favorites = relationship("PatientFavorite", back_populates="doctor")
    reviews = relationship("Review", back_populates="doctor")

    @property
    def is_online_available(self) -> bool:
        """True if the doctor offers online consultation."""
        return self.online_fee > 0

    @property
    def is_clinic_available(self) -> bool:
        """True if the doctor has clinic details filled in."""
        return bool(self.hospital_name or self.clinic_address)


class Patient(Base):
    """Represents a patient who books appointments."""

    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    appointments = relationship("Appointment", back_populates="patient")
    favorites = relationship("PatientFavorite", back_populates="patient")
    reviews = relationship("Review", back_populates="patient")
    ai_reports = relationship("AIReport", back_populates="patient")
    ai_conversations = relationship("AIConversation", back_populates="patient")


class Appointment(Base):
    """Represents one booked appointment between a doctor and a patient."""

    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    appointment_date = Column(Date, nullable=False, index=True)
    appointment_time = Column(Time, nullable=False)
    # We use the SAME name as the native PostgreSQL enum type created in
    # sql/schema.sql ("appointment_status") and store the enum *value*
    # ("Booked") instead of the member name ("BOOKED").
    status = Column(
        Enum(AppointmentStatus, name="appointment_status", values_callable=lambda e: [m.value for m in e]),
        default=AppointmentStatus.BOOKED,
        nullable=False,
    )
    consultation_fee = Column(Integer, nullable=True)                 # fee captured at booking time (PKR)
    visit_type = Column(String(20), nullable=True)                    # "First" or "Follow-up"
    created_at = Column(DateTime, default=datetime.now)

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

    # DB-level guarantee against double booking for the same doctor slot.
    # A PARTIAL unique index (PostgreSQL + SQLite): only *active* rows
    # (Booked/Completed) block a slot, so a cancelled appointment frees
    # its time for re-booking.
    __table_args__ = (
        Index(
            "uq_doctor_slot_active",
            "doctor_id",
            "appointment_date",
            "appointment_time",
            unique=True,
            postgresql_where=text("status <> 'Cancelled'"),
            sqlite_where=text("status <> 'Cancelled'"),
        ),
    )

    def to_time_string(self) -> str:
        """Return the appointment time formatted as 'HH:MM' (e.g. '09:30')."""
        return self.appointment_time.strftime("%H:%M") if self.appointment_time else ""


# ---------------------------------------------------------------------------
# Specializations, Symptoms and mapping (smart search)
# ---------------------------------------------------------------------------

class Specialization(Base):
    """Canonical list of medical specializations (used for search + UI)."""

    __tablename__ = "specializations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)           # e.g. "Dentist"
    keywords = Column(Text, nullable=True)                            # extra search keywords, comma separated

    symptoms = relationship("SymptomMapping", back_populates="specialization")


class Symptom(Base):
    """Common diseases / symptoms a patient might type in the search box."""

    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)           # e.g. "Tooth Pain"

    mappings = relationship("SymptomMapping", back_populates="symptom")


class SymptomMapping(Base):
    """Maps a symptom to the medical specialization that treats it.

    Example: "Tooth Pain" -> "Dentist".
    """

    __tablename__ = "symptom_mappings"

    id = Column(Integer, primary_key=True, index=True)
    symptom_id = Column(Integer, ForeignKey("symptoms.id"), nullable=False)
    specialization_id = Column(Integer, ForeignKey("specializations.id"), nullable=False)

    symptom = relationship("Symptom", back_populates="mappings")
    specialization = relationship("Specialization", back_populates="symptoms")


# ---------------------------------------------------------------------------
# Doctor availability
# ---------------------------------------------------------------------------

class DoctorSchedule(Base):
    """One day of the weekly schedule for a doctor.

    A doctor can set working days, clinic hours and the length of each
    appointment. Example: Monday, 09:00 - 17:00, 30 minute appointments.
    """

    __tablename__ = "doctor_schedules"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)                     # 0=Monday ... 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=30)    # 15, 20, 30 or 60
    is_available = Column(Boolean, default=True, nullable=False)      # can be switched off per day

    doctor = relationship("Doctor", back_populates="schedules")

    __table_args__ = (
        UniqueConstraint("doctor_id", "day_of_week", name="uq_doctor_day"),
    )


class UnavailableDate(Base):
    """A date on which the doctor is unavailable (vacation/emergency/off)."""

    __tablename__ = "doctor_unavailable_dates"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    reason = Column(String(50), nullable=True)                        # "Vacation" / "Emergency" / "Off"

    doctor = relationship("Doctor", back_populates="unavailable_dates")


class BlockedSlot(Base):
    """A specific time slot the doctor has blocked on a specific date."""

    __tablename__ = "blocked_slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)

    doctor = relationship("Doctor", back_populates="blocked_slots")


# ---------------------------------------------------------------------------
# Social / engagement
# ---------------------------------------------------------------------------

class PatientFavorite(Base):
    """A patient's favourite doctor (bookmark for quick access)."""

    __tablename__ = "patient_favorites"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

    patient = relationship("Patient", back_populates="favorites")
    doctor = relationship("Doctor", back_populates="favorites")

    __table_args__ = (
        UniqueConstraint("patient_id", "doctor_id", name="uq_patient_doctor"),
    )


class Notification(Base):
    """An in-app notification sent to a doctor or a patient."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_role = Column(String(20), nullable=False, index=True)   # "doctor" or "patient"
    recipient_id = Column(Integer, nullable=False, index=True)
    message = Column(String(300), nullable=False)
    notification_type = Column(String(30), default="info", nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class Review(Base):
    """A rating + comment left by a patient about a doctor (future-ready)."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)                          # 1 to 5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    doctor = relationship("Doctor", back_populates="reviews")
    patient = relationship("Patient", back_populates="reviews")


# ---------------------------------------------------------------------------
# AI Health Assistant (real Groq API)
# ---------------------------------------------------------------------------

class AIReport(Base):
    """An uploaded medical document analyzed by the ShifaBook AI assistant.

    The raw file is stored privately in backend/uploads (never served
    publicly). Only extracted text + the analysis result are kept in the
    database for the patient to view and chat about.
    """

    __tablename__ = "ai_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=True)         # private file path
    file_type = Column(String(20), nullable=False)           # jpg / jpeg / png / webp / pdf
    file_size = Column(Integer, nullable=False, default=0)   # bytes
    report_type = Column(String(100), nullable=True)
    extracted_text = Column(Text, nullable=True)
    analysis_result = Column(Text, nullable=True)            # JSON string
    urgency_level = Column(String(20), nullable=True)        # green / orange / red
    recommended_specialty = Column(String(100), nullable=True)
    analysis_status = Column(String(20), nullable=False, default="pending")  # pending / analyzing / analyzed / failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    patient = relationship("Patient", back_populates="ai_reports")
    conversations = relationship("AIConversation", back_populates="report", cascade="all, delete-orphan")


class AIConversation(Base):
    """A chat thread about one AI report."""

    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    report_id = Column(Integer, ForeignKey("ai_reports.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    patient = relationship("Patient", back_populates="ai_conversations")
    report = relationship("AIReport", back_populates="conversations")
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan")


class AIMessage(Base):
    """One message in an AI chat thread (role: "user" or "assistant")."""

    __tablename__ = "ai_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    conversation = relationship("AIConversation", back_populates="messages")


# ---------------------------------------------------------------------------
# Helper: standard slot durations and Pakistan helpers
# ---------------------------------------------------------------------------

VALID_DURATIONS = (15, 20, 30, 60)


def generate_slots(start: time, end: time, duration_minutes: int) -> list:
    """Generate appointment slot start-times between start and end.

    Example: start=09:00, end=17:00, duration=30 -> 09:00, 09:30, ... 16:30.
    Slots always align to the requested duration.
    """
    slots = []
    current = datetime.combine(date.today(), start)
    end_dt = datetime.combine(date.today(), end)
    while current + duration_minutes_to_timedelta(duration_minutes) <= end_dt:
        slots.append(current.time())
        current += duration_minutes_to_timedelta(duration_minutes)
    return slots


def duration_minutes_to_timedelta(minutes: int):
    from datetime import timedelta
    return timedelta(minutes=minutes)


def format_time_12h(value: time) -> str:
    """Return a time in 12-hour format, e.g. 14:30 -> '02:30 PM'."""
    return value.strftime("%I:%M %p").lstrip("0") if value else ""

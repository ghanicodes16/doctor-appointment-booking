"""
models.py - Database table definitions (ORM models).

ORM stands for "Object Relational Mapping". It lets us work with
database tables as if they were normal Python classes. Each class below
maps to one table in PostgreSQL:

    Doctor      ->  doctors        table
    Patient     ->  patients       table
    Appointment ->  appointments   table

A column is created with Column(...) and given a type such as Integer,
String, Date or Time.

Relationships are the connections between tables:
    - A Doctor has many Appointments (one-to-many).
    - A Patient has many Appointments (one-to-many).
    - An Appointment belongs to one Doctor and one Patient
      (many-to-one, done with Foreign Keys).
"""

from datetime import datetime, time

import enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class AppointmentStatus(str, enum.Enum):
    """The possible states an appointment can be in."""

    BOOKED = "Booked"          # The patient has booked this slot.
    COMPLETED = "Completed"    # The doctor has finished this visit.
    CANCELLED = "Cancelled"    # The appointment was cancelled.


class Doctor(Base):
    """Represents a doctor who can receive appointment bookings."""

    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)                 # Unique ID.
    name = Column(String(100), nullable=False)                         # Full name.
    email = Column(String(100), unique=True, nullable=False, index=True)  # Login email (must be unique).
    phone = Column(String(20), nullable=False)                         # Contact phone number.
    specialty = Column(String(100), nullable=False)                    # e.g. Cardiologist.
    password_hash = Column(String(255), nullable=False)                # Hashed password (never plain text).
    created_at = Column(DateTime, default=datetime.now)                # When this account was created.

    # "appointments" lets us easily fetch all appointments of a doctor:
    #   doctor.appointments -> list of Appointment objects.
    appointments = relationship("Appointment", back_populates="doctor")


class Patient(Base):
    """Represents a patient who books appointments."""

    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)                 # Unique ID.
    name = Column(String(100), nullable=False)                         # Full name.
    email = Column(String(100), unique=True, nullable=False, index=True)  # Login email (must be unique).
    phone = Column(String(20), nullable=False)                         # Contact phone number.
    password_hash = Column(String(255), nullable=False)                # Hashed password.
    created_at = Column(DateTime, default=datetime.now)                # When this account was created.

    appointments = relationship("Appointment", back_populates="patient")


class Appointment(Base):
    """Represents one booked appointment between a doctor and a patient."""

    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)                 # Unique appointment ID.
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    appointment_date = Column(Date, nullable=False, index=True)        # Which day (e.g. 2026-08-10).
    appointment_time = Column(Time, nullable=False)                    # Which time (e.g. 09:30).
    # We use the SAME name as the native PostgreSQL enum type created in
    # sql/schema.sql ("appointment_status") and tell SQLAlchemy to store
    # the enum *value* ("Booked") instead of the member name ("BOOKED").
    # This keeps the ORM and the raw SQL schema perfectly in sync.
    status = Column(
        Enum(AppointmentStatus, name="appointment_status", values_callable=lambda e: [m.value for m in e]),
        default=AppointmentStatus.BOOKED,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.now)                # When the booking was made.

    # Links back to the full Doctor / Patient rows so we can easily show
    # the patient's name, the doctor's name, phone numbers, etc.
    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

    # IMPORTANT: this UNIQUE constraint is the database-level guarantee
    # that prevents double booking. The database will reject any attempt
    # to insert a second appointment for the SAME doctor on the SAME
    # date at the SAME time.
    __table_args__ = (
        UniqueConstraint(
            "doctor_id",
            "appointment_date",
            "appointment_time",
            name="uq_doctor_slot",  # short name for this constraint
        ),
    )

    def to_time_string(self) -> str:
        """Return the appointment time formatted as 'HH:MM' (e.g. '09:30')."""
        return self.appointment_time.strftime("%H:%M") if self.appointment_time else ""


def available_slots() -> list:
    """Return the list of time slots a doctor can be booked for.

    Slots run from 09:00 to 16:30 in 30-minute steps. Having one fixed
    list keeps the booking logic simple and predictable.
    """
    slots = []
    for hour in range(9, 17):          # hours 9 ... 16
        for minute in (0, 30):         # minutes :00 and :30
            slot = time(hour, minute)
            # Skip 17:00 - that would be outside working hours.
            if hour == 16 and minute == 30:
                continue
            slots.append(slot)
    return slots

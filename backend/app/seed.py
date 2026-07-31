"""
seed.py - Sample data for the project.

This script fills the database with demo doctors, patients and
appointments so that you can log in and explore the application right
away. It is called automatically on every backend start, but it only
adds data if the doctors table is empty (it is "idempotent", meaning
running it many times is safe).

Demo login credentials:

    DOCTORS (password: doctor123)
      smitchell@clinic.com  -> Dr. Sarah Mitchell
      jcarter@clinic.com    -> Dr. John Carter
      erodriguez@clinic.com -> Dr. Emily Rodriguez
      mchen@clinic.com      -> Dr. Michael Chen
      lpark@clinic.com      -> Dr. Linda Park

    PATIENTS (password: patient123)
      alice@example.com     -> Alice Johnson
      bob@example.com       -> Bob Smith
      carol@example.com     -> Carol Davis
"""

from datetime import date, time, timedelta

from . import models
from .database import Base, SessionLocal, engine
from .security import hash_password

DOCTOR_PASSWORD = "doctor123"
PATIENT_PASSWORD = "patient123"


def _create_doctors():
    """Create the five demo doctors."""
    doctors = [
        models.Doctor(name="Sarah Mitchell", email="smitchell@clinic.com", phone="555-0101",
                      specialty="Cardiologist", password_hash=hash_password(DOCTOR_PASSWORD)),
        models.Doctor(name="John Carter", email="jcarter@clinic.com", phone="555-0102",
                      specialty="General Physician", password_hash=hash_password(DOCTOR_PASSWORD)),
        models.Doctor(name="Emily Rodriguez", email="erodriguez@clinic.com", phone="555-0103",
                      specialty="Dermatologist", password_hash=hash_password(DOCTOR_PASSWORD)),
        models.Doctor(name="Michael Chen", email="mchen@clinic.com", phone="555-0104",
                      specialty="Pediatrician", password_hash=hash_password(DOCTOR_PASSWORD)),
        models.Doctor(name="Linda Park", email="lpark@clinic.com", phone="555-0105",
                      specialty="Neurologist", password_hash=hash_password(DOCTOR_PASSWORD)),
    ]
    return doctors


def _create_patients():
    """Create the three demo patients."""
    return [
        models.Patient(name="Alice Johnson", email="alice@example.com", phone="555-0201",
                       password_hash=hash_password(PATIENT_PASSWORD)),
        models.Patient(name="Bob Smith", email="bob@example.com", phone="555-0202",
                       password_hash=hash_password(PATIENT_PASSWORD)),
        models.Patient(name="Carol Davis", email="carol@example.com", phone="555-0203",
                       password_hash=hash_password(PATIENT_PASSWORD)),
    ]


def _create_appointments(db, doctors, patients):
    """Create a few sample appointments so the dashboards are not empty.

    We book some slots for today and tomorrow. Because the booking rules
    are enforced, these slots will already appear as "taken" when a
    patient tries to book the same doctor/date/time.
    """
    today = date.today()
    return [
        models.Appointment(
            doctor_id=doctors[0].id, patient_id=patients[0].id,   # Sarah Mitchell <-> Alice
            appointment_date=today, appointment_time=time(9, 0),
        ),
        models.Appointment(
            doctor_id=doctors[1].id, patient_id=patients[1].id,   # John Carter <-> Bob
            appointment_date=today, appointment_time=time(10, 30),
        ),
        models.Appointment(
            doctor_id=doctors[2].id, patient_id=patients[2].id,   # Emily Rodriguez <-> Carol
            appointment_date=today + timedelta(days=1), appointment_time=time(9, 0),
        ),
        models.Appointment(
            doctor_id=doctors[3].id, patient_id=patients[0].id,   # Michael Chen <-> Alice (yesterday)
            appointment_date=today - timedelta(days=1), appointment_time=time(11, 0),
            status=models.AppointmentStatus.COMPLETED,
        ),
        models.Appointment(
            doctor_id=doctors[4].id, patient_id=patients[1].id,   # Linda Park <-> Bob (two days ago)
            appointment_date=today - timedelta(days=2), appointment_time=time(14, 0),
            status=models.AppointmentStatus.COMPLETED,
        ),
    ]


def seed_data():
    """Create tables (if missing) and insert demo data (if empty)."""
    # Create all tables that do not exist yet.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # If doctors already exist, seeding was done before - stop here.
        if db.query(models.Doctor).count() > 0:
            print("[seed] Doctors already exist, skipping sample data.")
            return

        doctors = _create_doctors()
        patients = _create_patients()
        db.add_all(doctors)
        db.add_all(patients)
        db.commit()

        # Reload the objects so they have their database ids.
        for obj in doctors:
            db.refresh(obj)
        for obj in patients:
            db.refresh(obj)

        appointments = _create_appointments(db, doctors, patients)
        db.add_all(appointments)
        db.commit()

        print("[seed] Sample data created: 5 doctors, 3 patients, 5 appointments.")
        print("[seed] Doctor login password: doctor123 | Patient login password: patient123")
    finally:
        db.close()


# Allow running the seed manually from the command line:
#   python -m app.seed
if __name__ == "__main__":
    seed_data()

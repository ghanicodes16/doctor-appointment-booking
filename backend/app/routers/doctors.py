"""
routers/doctors.py - Doctor endpoints.

Endpoints in this file:

    GET  /api/doctors                          -> list all doctors (public)
    GET  /api/doctors/{doctor_id}              -> one doctor (public)
    GET  /api/doctors/me                       -> current doctor's profile (doctor only)
    GET  /api/doctors/me/appointments          -> appointments for the logged-in doctor (doctor only)
    PATCH /api/doctors/me/appointments/{id}/status -> mark completed/cancelled (doctor only)

The public "list doctors" endpoint is what the patient booking page
calls to show which doctors are available.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_doctor

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])


@router.get("", response_model=list[schemas.DoctorOut])
def list_doctors(db: Session = Depends(get_db)):
    """Return every doctor in the database (no login required)."""
    return db.query(models.Doctor).order_by(models.Doctor.name).all()


@router.get("/me", response_model=schemas.DoctorOut)
def get_my_profile(doctor: models.Doctor = Depends(get_current_doctor)):
    """Return the profile of the currently logged-in doctor."""
    return doctor


@router.get("/{doctor_id}", response_model=schemas.DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Return a single doctor by id (no login required).

    NOTE: this route is declared AFTER "/me", so requests to
    /api/doctors/me are matched by the endpoint above and never by this
    one. FastAPI matches routes in the order they are defined.
    """
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    return doctor


@router.get("/me/appointments", response_model=list[schemas.AppointmentOut])
def get_doctor_appointments(
    appointment_date: date | None = Query(default=None, description="Filter by date (YYYY-MM-DD)"),
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Return all appointments for the logged-in doctor.

    If ?date=YYYY-MM-DD is provided, only appointments on that exact
    date are returned. Otherwise every appointment is returned.
    """
    query = (
        db.query(models.Appointment)
        .filter(models.Appointment.doctor_id == doctor.id)
        .order_by(models.Appointment.appointment_date, models.Appointment.appointment_time)
    )

    if appointment_date is not None:
        query = query.filter(models.Appointment.appointment_date == appointment_date)

    appointments = query.all()

    # We are not inside a session that keeps relationships loaded by
    # default, so we explicitly load doctor and patient for each row.
    for appointment in appointments:
        appointment.doctor = appointment.doctor
        appointment.patient = appointment.patient

    return appointments


@router.patch("/me/appointments/{appointment_id}/status", response_model=schemas.AppointmentOut)
def update_appointment_status(
    appointment_id: int,
    data: schemas.AppointmentStatusUpdate,
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Let a doctor mark an appointment as Completed or Cancelled."""
    allowed = {models.AppointmentStatus.COMPLETED.value, models.AppointmentStatus.CANCELLED.value}
    if data.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be either 'Completed' or 'Cancelled'.",
        )

    appointment = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.id == appointment_id,
            models.Appointment.doctor_id == doctor.id,  # doctors can only change their own appointments
        )
        .first()
    )

    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    appointment.status = models.AppointmentStatus(data.status)
    db.commit()
    db.refresh(appointment)
    return appointment

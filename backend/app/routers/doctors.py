"""
routers/doctors.py - Doctor endpoints.

Public:
    GET    /api/doctors                                   list all doctors
    GET    /api/doctors/{id}                              one doctor's public profile
    GET    /api/doctors/{id}/schedule                     working days (for the booking UI)
    GET    /api/doctors/{id}/reviews                      reviews for a doctor

Doctor-only:
    GET    /api/doctors/me                                own profile
    PATCH  /api/doctors/me                                update profile + fees
    GET/PUT/PATCH /api/doctors/me/schedule                manage weekly working schedule
    POST/GET/DELETE /api/doctors/me/unavailable-dates     manage unavailable dates
    POST/GET/DELETE /api/doctors/me/blocked-slots         block specific slots
    PATCH  /api/doctors/me/booking                        enable/disable booking
    GET    /api/doctors/me/stats                          dashboard analytics
    GET    /api/doctors/me/appointments                   the doctor's appointments (+ date filter)
    PATCH  /api/doctors/me/appointments/{id}/status       mark Completed / Cancelled
"""

from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_doctor
from ..utils import attach_rating, notify, parse_time
from ..models import VALID_DURATIONS

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])

# Fields used to compute the "profile completion" percentage on the dashboard.
PROFILE_FIELDS = [
    "name", "email", "phone", "pmdc_number", "gender", "qualifications",
    "specialization", "hospital_name", "clinic_address", "city", "province",
    "biography", "first_visit_fee",
]


def _profile_completion(doctor) -> int:
    """Return 0-100 showing how complete a doctor's profile is."""
    filled = 0
    for field in PROFILE_FIELDS:
        value = getattr(doctor, field, None)
        if value not in (None, "", 0):
            filled += 1
    return round((filled / len(PROFILE_FIELDS)) * 100)


@router.get("", response_model=list[schemas.DoctorOut])
def list_doctors(db: Session = Depends(get_db)):
    """Return every doctor (with ratings attached)."""
    doctors = db.query(models.Doctor).order_by(models.Doctor.name).all()
    for doctor in doctors:
        attach_rating(db, doctor)
    return doctors


@router.get("/me", response_model=schemas.DoctorOut)
def get_my_profile(doctor: models.Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    """Return the currently logged-in doctor's full profile."""
    attach_rating(db, doctor)
    return doctor


@router.patch("/me", response_model=schemas.DoctorOut)
def update_my_profile(
    data: schemas.DoctorUpdate,
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Update any subset of the doctor's profile/fee fields."""
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "languages" and isinstance(value, list):
            value = ",".join(value)
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    attach_rating(db, doctor)
    return doctor


# ---------------------------------------------------------------------------
# Schedule (weekly availability)
# ---------------------------------------------------------------------------

@router.get("/me/schedule", response_model=list[schemas.ScheduleOut])
def get_my_schedule(doctor: models.Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    """Return the doctor's weekly working schedule."""
    return (
        db.query(models.DoctorSchedule)
        .filter(models.DoctorSchedule.doctor_id == doctor.id)
        .order_by(models.DoctorSchedule.day_of_week)
        .all()
    )


@router.put("/me/schedule", response_model=list[schemas.ScheduleOut])
def update_my_schedule(
    data: schemas.ScheduleIn,
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Replace the doctor's weekly schedule.

    The frontend sends the full list of working days; we delete the old
    schedule and insert the new one.
    """
    for item in data.schedule:
        if item.duration_minutes not in VALID_DURATIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment duration must be 15, 20, 30 or 60 minutes.",
            )
        start = parse_time(item.start_time)
        end = parse_time(item.end_time)
        if start >= end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time.",
            )

    db.query(models.DoctorSchedule).filter(models.DoctorSchedule.doctor_id == doctor.id).delete()
    for item in data.schedule:
        db.add(
            models.DoctorSchedule(
                doctor_id=doctor.id,
                day_of_week=item.day_of_week,
                start_time=parse_time(item.start_time),
                end_time=parse_time(item.end_time),
                duration_minutes=item.duration_minutes,
                is_available=item.is_available,
            )
        )
    db.commit()

    return (
        db.query(models.DoctorSchedule)
        .filter(models.DoctorSchedule.doctor_id == doctor.id)
        .order_by(models.DoctorSchedule.day_of_week)
        .all()
    )


# ---------------------------------------------------------------------------
# Unavailable dates
# ---------------------------------------------------------------------------

@router.get("/me/unavailable-dates", response_model=list[schemas.UnavailableDateOut])
def get_unavailable_dates(doctor: models.Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    """List the doctor's unavailable dates (vacations, emergency leave...)."""
    return (
        db.query(models.UnavailableDate)
        .filter(models.UnavailableDate.doctor_id == doctor.id)
        .order_by(models.UnavailableDate.date.desc())
        .all()
    )


@router.post("/me/unavailable-dates", response_model=schemas.UnavailableDateOut, status_code=status.HTTP_201_CREATED)
def add_unavailable_date(
    data: schemas.UnavailableDateIn,
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Mark a date as unavailable (vacation / emergency / off)."""
    exists = (
        db.query(models.UnavailableDate)
        .filter(
            models.UnavailableDate.doctor_id == doctor.id,
            models.UnavailableDate.date == data.date,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This date is already marked unavailable.")
    row = models.UnavailableDate(doctor_id=doctor.id, date=data.date, reason=data.reason)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/me/unavailable-dates/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_unavailable_date(
    entry_id: int,
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Remove an unavailable date."""
    row = (
        db.query(models.UnavailableDate)
        .filter(models.UnavailableDate.id == entry_id, models.UnavailableDate.doctor_id == doctor.id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    db.delete(row)
    db.commit()


# ---------------------------------------------------------------------------
# Blocked slots
# ---------------------------------------------------------------------------

@router.get("/me/blocked-slots", response_model=list[schemas.BlockedSlotOut])
def get_blocked_slots(doctor: models.Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    """List the doctor's blocked time slots."""
    return (
        db.query(models.BlockedSlot)
        .filter(models.BlockedSlot.doctor_id == doctor.id)
        .order_by(models.BlockedSlot.date, models.BlockedSlot.start_time)
        .all()
    )


@router.post("/me/blocked-slots", response_model=schemas.BlockedSlotOut, status_code=status.HTTP_201_CREATED)
def add_blocked_slot(
    data: schemas.BlockedSlotIn,
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Block a specific time slot on a specific date."""
    row = models.BlockedSlot(doctor_id=doctor.id, date=data.date, start_time=parse_time(data.start_time))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/me/blocked-slots/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_blocked_slot(
    entry_id: int,
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Un-block a time slot."""
    row = (
        db.query(models.BlockedSlot)
        .filter(models.BlockedSlot.id == entry_id, models.BlockedSlot.doctor_id == doctor.id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    db.delete(row)
    db.commit()


@router.patch("/me/booking", response_model=schemas.DoctorOut)
def set_booking_enabled(
    data: dict,
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Enable or disable appointment booking.

    Body: {"booking_enabled": true/false}
    """
    value = data.get("booking_enabled")
    if value is None or not isinstance(value, bool):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="booking_enabled must be true or false.")
    doctor.booking_enabled = value
    db.commit()
    db.refresh(doctor)
    attach_rating(db, doctor)
    return doctor


# ---------------------------------------------------------------------------
# Dashboard analytics
# ---------------------------------------------------------------------------

@router.get("/me/stats", response_model=schemas.DoctorStatsOut)
def get_my_stats(doctor: models.Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    """Compute the numbers/charts for the doctor dashboard."""
    today = date.today()
    this_month_start = today.replace(day=1)

    # All appointments of this doctor.
    appointments = (
        db.query(models.Appointment)
        .filter(models.Appointment.doctor_id == doctor.id)
        .all()
    )

    today_count = sum(1 for a in appointments if a.appointment_date == today and a.status != models.AppointmentStatus.CANCELLED)
    upcoming_count = sum(1 for a in appointments if a.appointment_date >= today and a.status == models.AppointmentStatus.BOOKED)
    monthly_count = sum(1 for a in appointments if a.appointment_date >= this_month_start and a.status != models.AppointmentStatus.CANCELLED)
    total_patients = len({a.patient_id for a in appointments if a.status != models.AppointmentStatus.CANCELLED})

    # Revenue is based on the consultation fee of completed appointments.
    total_revenue = sum(a.consultation_fee or 0 for a in appointments if a.status == models.AppointmentStatus.COMPLETED)
    monthly_revenue = sum(
        a.consultation_fee or 0
        for a in appointments
        if a.status == models.AppointmentStatus.COMPLETED and a.appointment_date >= this_month_start
    )

    # Weekly chart: appointments for the current week (Mon..Sun).
    monday = today - timedelta(days=today.weekday())
    week_dates = [monday + timedelta(days=i) for i in range(7)]
    counts = [
        sum(1 for a in appointments if a.appointment_date == d and a.status != models.AppointmentStatus.CANCELLED)
        for d in week_dates
    ]
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return schemas.DoctorStatsOut(
        today_count=today_count,
        upcoming_count=upcoming_count,
        total_patients=total_patients,
        monthly_count=monthly_count,
        weekly={"labels": labels, "counts": counts},
        total_revenue=total_revenue,
        monthly_revenue=monthly_revenue,
        profile_completion=_profile_completion(doctor),
    )


# ---------------------------------------------------------------------------
# Appointments (doctor's own)
# ---------------------------------------------------------------------------

@router.get("/me/appointments", response_model=list[schemas.AppointmentOut])
def get_doctor_appointments(
    appointment_date: date | None = Query(default=None),
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Return all appointments for the logged-in doctor (optional date filter)."""
    query = (
        db.query(models.Appointment)
        .filter(models.Appointment.doctor_id == doctor.id)
        .order_by(models.Appointment.appointment_date, models.Appointment.appointment_time)
    )
    if appointment_date is not None:
        query = query.filter(models.Appointment.appointment_date == appointment_date)

    appointments = query.all()
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
    """Let a doctor mark an appointment Completed or Cancelled."""
    allowed = {models.AppointmentStatus.COMPLETED.value, models.AppointmentStatus.CANCELLED.value}
    if data.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be either 'Completed' or 'Cancelled'.",
        )

    appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id, models.Appointment.doctor_id == doctor.id)
        .first()
    )
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    appointment.status = models.AppointmentStatus(data.status)

    # Track patients treated: only increment once when an appointment
    # transitions to Completed for the first time.
    if data.status == models.AppointmentStatus.COMPLETED.value:
        doctor.patients_treated += 1

    db.commit()
    db.refresh(appointment)

    # Notify the patient about the status change.
    notify(
        db,
        role="patient",
        recipient_id=appointment.patient_id,
        message=f"Your appointment with Dr. {doctor.name} on {appointment.appointment_date} at "
        f"{appointment.to_time_string()} has been marked as {appointment.status.value}.",
        notification_type="status",
    )
    db.commit()

    appointment.doctor = appointment.doctor
    appointment.patient = appointment.patient
    return appointment


# ---------------------------------------------------------------------------
# Public endpoints (must be declared AFTER "/me" routes)
# ---------------------------------------------------------------------------

@router.get("/{doctor_id}", response_model=schemas.DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Return one doctor's public profile by id."""
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    attach_rating(db, doctor)
    return doctor


@router.get("/{doctor_id}/schedule", response_model=list[schemas.ScheduleOut])
def get_doctor_schedule(doctor_id: int, db: Session = Depends(get_db)):
    """Return a doctor's weekly schedule (used by the booking page)."""
    if db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    return (
        db.query(models.DoctorSchedule)
        .filter(models.DoctorSchedule.doctor_id == doctor_id, models.DoctorSchedule.is_available.is_(True))
        .order_by(models.DoctorSchedule.day_of_week)
        .all()
    )

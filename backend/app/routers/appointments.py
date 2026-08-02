"""
routers/appointments.py - Booking endpoints (core business logic).

    GET  /api/slots?doctor_id=&appointment_date=   free slots for a doctor+date
    POST /api/appointments                          book an appointment (patient)
    GET  /api/appointments                          the patient's appointments
    PATCH /api/appointments/{id}                    reschedule (patient)
    DELETE /api/appointments/{id}                   cancel (patient)

Booking rules:
    1. The doctor must exist and have booking enabled.
    2. The date cannot be in the past.
    3. The doctor must work on that weekday (weekly schedule).
    4. The date cannot be marked unavailable (vacation/emergency/off).
    5. The chosen time must be a valid slot within the clinic hours,
       aligned to the appointment duration and not blocked.
    6. The slot must not already be booked (double-booking prevention,
       reinforced by a UNIQUE constraint in the database).
"""

from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_patient
from ..utils import notify, parse_time

router = APIRouter(prefix="/api", tags=["Appointments"])

# The exact message shown to a patient when the doctor is unavailable.
UNAVAILABLE_MESSAGE = "Doctor is unavailable on this date. Please select another doctor or another available date."

# The exact message shown when a slot is already booked.
SLOT_BOOKED_MESSAGE = "This appointment slot is already booked. Please choose another date or time."


def get_schedule_for_day(db: Session, doctor_id: int, appointment_date: date):
    """Return the doctor's schedule for the weekday of `appointment_date`.

    Returns None if the doctor does not work on that weekday or if the
    day is marked unavailable in the schedule.
    """
    return (
        db.query(models.DoctorSchedule)
        .filter(
            models.DoctorSchedule.doctor_id == doctor_id,
            models.DoctorSchedule.day_of_week == appointment_date.weekday(),
            models.DoctorSchedule.is_available.is_(True),
        )
        .first()
    )


def get_unavailable_date(db: Session, doctor_id: int, appointment_date: date):
    """Return the UnavailableDate row for a doctor+date, or None."""
    return (
        db.query(models.UnavailableDate)
        .filter(
            models.UnavailableDate.doctor_id == doctor_id,
            models.UnavailableDate.date == appointment_date,
        )
        .first()
    )


def build_available_slots(db: Session, doctor, appointment_date: date):
    """Compute the free slots for a doctor on a date.

    Returns (is_available, message, [slot strings]).
    """
    # 1. Booking switch.
    if not doctor.booking_enabled:
        return False, UNAVAILABLE_MESSAGE, []

    # 2. Working day?
    schedule = get_schedule_for_day(db, doctor.id, appointment_date)
    if schedule is None:
        return False, UNAVAILABLE_MESSAGE, []

    # 3. Unavailable (vacation / emergency / off)?
    if get_unavailable_date(db, doctor.id, appointment_date) is not None:
        return False, UNAVAILABLE_MESSAGE, []

    # 4. Generate all slots within the clinic hours.
    duration = schedule.duration_minutes
    all_slots = models.generate_slots(schedule.start_time, schedule.end_time, duration)

    # 5. Remove blocked slots for that date.
    blocked = {
        b.start_time
        for b in db.query(models.BlockedSlot).filter(
            models.BlockedSlot.doctor_id == doctor.id,
            models.BlockedSlot.date == appointment_date,
        )
    }

    # 6. Remove already-booked slots.
    booked = {
        a.appointment_time
        for a in db.query(models.Appointment).filter(
            models.Appointment.doctor_id == doctor.id,
            models.Appointment.appointment_date == appointment_date,
            models.Appointment.status != models.AppointmentStatus.CANCELLED,
        )
    }

    free = [s.strftime("%H:%M") for s in all_slots if s not in blocked and s not in booked]
    return True, None, free


def calculate_fee(db: Session, doctor, patient_id: int) -> tuple[int, str]:
    """Decide the consultation fee + visit type.

    First visit -> first_visit_fee. If the patient has any previous
    appointment with this doctor -> follow-up -> followup_fee.
    """
    previous = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.doctor_id == doctor.id,
            models.Appointment.patient_id == patient_id,
            models.Appointment.status != models.AppointmentStatus.CANCELLED,
        )
        .first()
    )
    if previous is not None:
        return doctor.followup_fee, "Follow-up"
    return doctor.first_visit_fee, "First"


@router.get("/slots", response_model=schemas.AvailableSlotsOut)
def get_available_slots(
    doctor_id: int,
    appointment_date: date,
    db: Session = Depends(get_db),
):
    """Return the free time slots for a doctor on a date."""
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")

    if appointment_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot book an appointment for a past date.",
        )

    is_available, message, slots = build_available_slots(db, doctor, appointment_date)
    return schemas.AvailableSlotsOut(
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        is_available=is_available,
        message=message,
        available_slots=slots,
    )


@router.post("/appointments", response_model=schemas.AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(
    data: schemas.AppointmentCreate,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Book a new appointment with full availability validation."""
    doctor = db.query(models.Doctor).filter(models.Doctor.id == data.doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")

    if data.appointment_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot book an appointment for a past date.",
        )

    appointment_time = parse_time(data.appointment_time)

    # Availability checks -> friendly messages.
    is_available, message, _ = build_available_slots(db, doctor, data.appointment_date)
    if not is_available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message or UNAVAILABLE_MESSAGE)

    # Make sure the chosen time is actually one of the generated slots.
    schedule = get_schedule_for_day(db, doctor.id, data.appointment_date)
    if appointment_time not in models.generate_slots(schedule.start_time, schedule.end_time, schedule.duration_minutes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected time is not a valid slot. Please choose from the available slots.",
        )

    # Double-booking prevention (application level).
    if _slot_taken(db, doctor.id, data.appointment_date, appointment_time):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SLOT_BOOKED_MESSAGE)

    # Calculate the consultation fee (first visit vs follow-up).
    fee, visit_type = calculate_fee(db, doctor, patient.id)

    appointment = models.Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        appointment_date=data.appointment_date,
        appointment_time=appointment_time,
        status=models.AppointmentStatus.BOOKED,
        consultation_fee=fee,
        visit_type=visit_type,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Notify the doctor about the new booking.
    notify(
        db,
        role="doctor",
        recipient_id=doctor.id,
        message=f"New appointment booked by {patient.name} on {appointment.appointment_date} at "
        f"{appointment.to_time_string()} (fee Rs. {fee}).",
        notification_type="booking",
    )
    db.commit()

    appointment.doctor = appointment.doctor
    appointment.patient = appointment.patient
    return appointment


def _slot_taken(db: Session, doctor_id: int, appointment_date: date, appointment_time: time) -> bool:
    """Check whether a slot is already booked (excluding cancelled rows)."""
    existing = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.appointment_date == appointment_date,
            models.Appointment.appointment_time == appointment_time,
            models.Appointment.status != models.AppointmentStatus.CANCELLED,
        )
        .first()
    )
    return existing is not None


@router.get("/appointments", response_model=list[schemas.AppointmentOut])
def get_my_appointments(
    upcoming: bool | None = Query(default=None),
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Return the logged-in patient's appointments (optional upcoming filter)."""
    query = (
        db.query(models.Appointment)
        .filter(models.Appointment.patient_id == patient.id)
        .order_by(models.Appointment.appointment_date.desc(), models.Appointment.appointment_time.desc())
    )
    if upcoming is not None:
        today = date.today()
        if upcoming:
            query = query.filter(models.Appointment.appointment_date >= today)
        else:
            query = query.filter(models.Appointment.appointment_date < today)

    appointments = query.all()
    for appointment in appointments:
        appointment.doctor = appointment.doctor
        appointment.patient = appointment.patient
    return appointments


@router.patch("/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
def reschedule_appointment(
    appointment_id: int,
    data: schemas.AppointmentUpdate,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Reschedule one of the patient's appointments (new slot must be free)."""
    appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id, models.Appointment.patient_id == patient.id)
        .first()
    )
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    if appointment.status != models.AppointmentStatus.BOOKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only booked appointments can be rescheduled.",
        )

    doctor = appointment.doctor
    new_time = parse_time(data.appointment_time)

    if data.appointment_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot book an appointment for a past date.",
        )

    is_available, message, _ = build_available_slots(db, doctor, data.appointment_date)
    if not is_available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message or UNAVAILABLE_MESSAGE)

    schedule = get_schedule_for_day(db, doctor.id, data.appointment_date)
    if new_time not in models.generate_slots(schedule.start_time, schedule.end_time, schedule.duration_minutes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected time is not a valid slot. Please choose from the available slots.",
        )

    # Same anti-double-booking check, ignoring the appointment itself.
    taken = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.doctor_id == appointment.doctor_id,
            models.Appointment.appointment_date == data.appointment_date,
            models.Appointment.appointment_time == new_time,
            models.Appointment.id != appointment.id,
            models.Appointment.status != models.AppointmentStatus.CANCELLED,
        )
        .first()
    )
    if taken is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SLOT_BOOKED_MESSAGE)

    appointment.appointment_date = data.appointment_date
    appointment.appointment_time = new_time
    db.commit()
    db.refresh(appointment)

    notify(
        db,
        role="doctor",
        recipient_id=doctor.id,
        message=f"{patient.name} rescheduled an appointment to {appointment.appointment_date} at "
        f"{appointment.to_time_string()}.",
        notification_type="reschedule",
    )
    db.commit()

    appointment.doctor = appointment.doctor
    appointment.patient = appointment.patient
    return appointment


@router.delete("/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
def cancel_appointment(
    appointment_id: int,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Cancel one of the patient's appointments (status becomes Cancelled)."""
    appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id, models.Appointment.patient_id == patient.id)
        .first()
    )
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    if appointment.status == models.AppointmentStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This appointment is already cancelled.")

    if appointment.status == models.AppointmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A completed appointment cannot be cancelled.",
        )

    doctor = appointment.doctor
    appointment.status = models.AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)

    notify(
        db,
        role="doctor",
        recipient_id=doctor.id,
        message=f"{patient.name} cancelled the appointment on {appointment.appointment_date} at "
        f"{appointment.to_time_string()}.",
        notification_type="cancel",
    )
    db.commit()

    appointment.doctor = appointment.doctor
    appointment.patient = appointment.patient
    return appointment

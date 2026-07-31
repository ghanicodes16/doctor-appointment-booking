"""
routers/appointments.py - Booking endpoints (core business logic).

Endpoints in this file:

    GET  /api/slots                   -> free time slots for a doctor+date (public)
    POST /api/appointments            -> book a new appointment (patient only)
    GET  /api/appointments            -> the patient's own appointments (patient only)
    PATCH /api/appointments/{id}      -> reschedule an appointment (patient only)
    DELETE /api/appointments/{id}     -> cancel an appointment (patient only)

The MOST IMPORTANT logic in the whole project is inside book_appointment
(and reschedule_appointment): the double-booking check. See the comments
below for a full explanation.
"""

from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_patient

router = APIRouter(prefix="/api", tags=["Appointments"])

# Message shown to the patient when the chosen slot is already taken.
SLOT_BOOKED_MESSAGE = "This appointment slot is already booked. Please choose another date or time."


def parse_time(value: str) -> time:
    """Turn a 'HH:MM' string into a datetime.time object.

    Raises a clear 422 error if the string is not a valid time.
    """
    try:
        hour, minute = value.split(":")
        return time(int(hour), int(minute))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid time format. Please use HH:MM (e.g. 09:30).",
        )


def slot_is_taken(db: Session, doctor_id: int, appointment_date: date, appointment_time: time) -> bool:
    """Check whether a slot is already booked for a doctor.

    This is the core anti-double-booking check. It looks for ANY
    existing appointment row that has the same doctor, the same date and
    the same time. If such a row exists the slot is taken.

    NOTE: the database also has a UNIQUE constraint on
    (doctor_id, appointment_date, appointment_time), so even if two
    booking requests arrived at the exact same moment, the database
    would reject the second one. Our query here makes the check faster
    and lets us return a friendly error message to the patient.
    """
    existing = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.appointment_date == appointment_date,
            models.Appointment.appointment_time == appointment_time,
        )
        .first()
    )
    return existing is not None


@router.get("/slots", response_model=schemas.AvailableSlotsOut)
def get_available_slots(
    doctor_id: int,
    appointment_date: date,
    db: Session = Depends(get_db),
):
    """Return all free time slots for a doctor on a given date.

    This is called by the booking page so the patient can see which
    times are still available before choosing one.
    """
    # Make sure the doctor exists (otherwise there is nothing to book).
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")

    # Refuse past dates - you cannot book an appointment in the past.
    if appointment_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot book an appointment for a past date.",
        )

    # Fetch every time that is already taken for this doctor on this date.
    booked_times = {
        a.appointment_time
        for a in db.query(models.Appointment).filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.appointment_date == appointment_date,
        )
    }

    # The free slots are all standard slots minus the booked ones.
    free_slots = [s.strftime("%H:%M") for s in models.available_slots() if s not in booked_times]

    return schemas.AvailableSlotsOut(
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        available_slots=free_slots,
    )


@router.post("/appointments", response_model=schemas.AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(
    data: schemas.AppointmentCreate,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Book a new appointment for the logged-in patient.

    Steps:
      1. Validate the doctor and the time format.
      2. Reject past dates.
      3. Check the slot is not already taken (double-booking check).
      4. Save the appointment in the database.
    """
    doctor = db.query(models.Doctor).filter(models.Doctor.id == data.doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")

    appointment_time = parse_time(data.appointment_time)

    if data.appointment_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot book an appointment for a past date.",
        )

    # >>> DOUBLE-BOOKING CHECK <<<
    # If a booking already exists for this doctor/date/time we refuse the
    # request with a clear, patient-friendly message.
    if slot_is_taken(db, doctor.id, data.appointment_date, appointment_time):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SLOT_BOOKED_MESSAGE)

    appointment = models.Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        appointment_date=data.appointment_date,
        appointment_time=appointment_time,
        status=models.AppointmentStatus.BOOKED,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/appointments", response_model=list[schemas.AppointmentOut])
def get_my_appointments(
    upcoming: bool | None = Query(default=None, description="If true, only future appointments"),
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Return all appointments of the logged-in patient.

    Use ?upcoming=true to see only future/upcoming appointments, or
    ?upcoming=false to see only past ones. Without the parameter, both
    are returned. The patient's appointments page uses this endpoint.
    """
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
    """Reschedule (change the date/time of) one of the patient's appointments.

    The same double-booking rules apply: the new slot must be free.
    """
    appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id, models.Appointment.patient_id == patient.id)
        .first()
    )
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    # Only Booked appointments can be rescheduled.
    if appointment.status != models.AppointmentStatus.BOOKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only booked appointments can be rescheduled.",
        )

    new_time = parse_time(data.appointment_time)

    if data.appointment_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot book an appointment for a past date.",
        )

    # The same anti-double-booking check, but we must ignore the current
    # appointment itself (otherwise changing anything would always fail).
    taken = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.doctor_id == appointment.doctor_id,
            models.Appointment.appointment_date == data.appointment_date,
            models.Appointment.appointment_time == new_time,
            models.Appointment.id != appointment.id,
        )
        .first()
    )
    if taken is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SLOT_BOOKED_MESSAGE)

    appointment.appointment_date = data.appointment_date
    appointment.appointment_time = new_time
    db.commit()
    db.refresh(appointment)
    return appointment


@router.delete("/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
def cancel_appointment(
    appointment_id: int,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Cancel one of the patient's appointments.

    We keep the row in the database but change its status to
    "Cancelled". This keeps a full history for the doctor's dashboard.
    """
    appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id, models.Appointment.patient_id == patient.id)
        .first()
    )
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    if appointment.status == models.AppointmentStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This appointment is already cancelled.",
        )

    if appointment.status == models.AppointmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A completed appointment cannot be cancelled.",
        )

    appointment.status = models.AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)
    return appointment

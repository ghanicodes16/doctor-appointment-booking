"""
utils.py - small shared helpers used by several routers.

Kept here so we do not repeat the same logic in every router:
    - parse_time: convert "HH:MM" -> datetime.time with a friendly error
    - slot_time_from_string
    - attach_rating: compute a doctor's average rating / review count
    - attach_is_favorite: mark which doctors the current patient favours
    - notify: create an in-app notification for a doctor or patient
"""

from datetime import time

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models


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


def attach_rating(db: Session, doctor) -> None:
    """Attach rating_avg and rating_count to a doctor object.

    Reviews are future-ready: if there are no reviews yet both values are
    simply 0. The values are attached as temporary attributes so Pydantic
    can include them in the response.
    """
    avg, count = (
        db.query(func.coalesce(func.avg(models.Review.rating), 0), func.count(models.Review.id))
        .filter(models.Review.doctor_id == doctor.id)
        .first()
    )
    doctor.rating_avg = round(float(avg or 0), 1)
    doctor.rating_count = int(count or 0)


def attach_is_favorite(db: Session, doctors, patient_id: int | None) -> None:
    """Mark which doctors are favourites of the given patient.

    If the patient is not logged in, none are favourites.
    """
    if not patient_id or not doctors:
        for doctor in doctors:
            doctor.is_favorite = False
        return

    ids = [d.id for d in doctors]
    fav_ids = set(
        row[0]
        for row in db.query(models.PatientFavorite.doctor_id)
        .filter(
            models.PatientFavorite.patient_id == patient_id,
            models.PatientFavorite.doctor_id.in_(ids),
        )
    )
    for doctor in doctors:
        doctor.is_favorite = doctor.id in fav_ids


def notify(db: Session, role: str, recipient_id: int, message: str, notification_type: str = "info") -> None:
    """Create an in-app notification for a doctor or a patient."""
    db.add(
        models.Notification(
            recipient_role=role,
            recipient_id=recipient_id,
            message=message,
            notification_type=notification_type,
        )
    )

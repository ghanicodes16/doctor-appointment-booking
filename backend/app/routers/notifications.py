"""
routers/notifications.py - In-app notifications.

    GET    /api/notifications            the logged-in user's notifications
    PATCH  /api/notifications/{id}/read  mark one notification as read
    PATCH  /api/notifications/read-all   mark all as read
    GET    /api/notifications/unread-count   number of unread notifications

Notifications are created automatically by the app (new bookings, status
changes, cancellations, reschedules).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_doctor, get_current_patient

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


def _role_id(db: Session, patient=None, doctor=None):
    """Return (role, id) of the current user depending on which is set."""
    if doctor is not None:
        return "doctor", doctor.id
    return "patient", patient.id


@router.get("", response_model=list[schemas.NotificationOut])
def get_my_notifications(
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """List the patient's notifications (newest first)."""
    return _list_notifications(db, "patient", patient.id)


@router.get("/doctor", response_model=list[schemas.NotificationOut])
def get_doctor_notifications(
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """List the doctor's notifications (newest first)."""
    return _list_notifications(db, "doctor", doctor.id)


def _list_notifications(db: Session, role: str, recipient_id: int):
    return (
        db.query(models.Notification)
        .filter(
            models.Notification.recipient_role == role,
            models.Notification.recipient_id == recipient_id,
        )
        .order_by(models.Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.get("/unread-count")
def unread_count(
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Number of unread notifications for the patient."""
    return {"count": _count_unread(db, "patient", patient.id)}


@router.get("/doctor/unread-count")
def doctor_unread_count(
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Number of unread notifications for the doctor."""
    return {"count": _count_unread(db, "doctor", doctor.id)}


def _count_unread(db: Session, role: str, recipient_id: int) -> int:
    return (
        db.query(models.Notification)
        .filter(
            models.Notification.recipient_role == role,
            models.Notification.recipient_id == recipient_id,
            models.Notification.is_read.is_(False),
        )
        .count()
    )


@router.patch("/{notification_id}/read")
def mark_read(
    notification_id: int,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Mark one of the patient's notifications as read."""
    return _mark_read(db, "patient", patient.id, notification_id)


@router.patch("/doctor/{notification_id}/read")
def doctor_mark_read(
    notification_id: int,
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Mark one of the doctor's notifications as read."""
    return _mark_read(db, "doctor", doctor.id, notification_id)


def _mark_read(db: Session, role: str, recipient_id: int, notification_id: int):
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.recipient_role == role,
            models.Notification.recipient_id == recipient_id,
        )
        .first()
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    notification.is_read = True
    db.commit()
    return {"message": "Notification marked as read."}


@router.patch("/read-all")
def mark_all_read(
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Mark all of the patient's notifications as read."""
    return _mark_all_read(db, "patient", patient.id)


@router.patch("/doctor/read-all")
def doctor_mark_all_read(
    doctor: models.Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Mark all of the doctor's notifications as read."""
    return _mark_all_read(db, "doctor", doctor.id)


def _mark_all_read(db: Session, role: str, recipient_id: int):
    db.query(models.Notification).filter(
        models.Notification.recipient_role == role,
        models.Notification.recipient_id == recipient_id,
        models.Notification.is_read.is_(False),
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read."}

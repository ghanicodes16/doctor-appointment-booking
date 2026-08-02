"""
routers/patients.py - Patient profile, favourites and stats.

    GET    /api/patients/me                     the patient's profile
    GET    /api/patients/me/favorites           favourite doctors
    POST   /api/patients/me/favorites/{doctor_id}   add a favourite
    DELETE /api/patients/me/favorites/{doctor_id}   remove a favourite
    GET    /api/patients/me/stats               dashboard numbers
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_patient
from ..utils import attach_rating

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.get("/me", response_model=schemas.PatientOut)
def get_my_profile(patient: models.Patient = Depends(get_current_patient)):
    """Return the current patient's profile."""
    return patient


@router.get("/me/favorites", response_model=list[schemas.DoctorOut])
def get_my_favorites(
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Return the doctors the patient has favourited."""
    rows = (
        db.query(models.PatientFavorite)
        .filter(models.PatientFavorite.patient_id == patient.id)
        .order_by(models.PatientFavorite.created_at.desc())
        .all()
    )
    doctors = [row.doctor for row in rows]
    for doctor in doctors:
        attach_rating(db, doctor)
        doctor.is_favorite = True
    return doctors


@router.post("/me/favorites/{doctor_id}", status_code=status.HTTP_201_CREATED)
def add_favorite(
    doctor_id: int,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Add a doctor to the patient's favourites."""
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")

    exists = (
        db.query(models.PatientFavorite)
        .filter(
            models.PatientFavorite.patient_id == patient.id,
            models.PatientFavorite.doctor_id == doctor_id,
        )
        .first()
    )
    if exists is None:
        db.add(models.PatientFavorite(patient_id=patient.id, doctor_id=doctor_id))
        db.commit()
    return {"message": "Doctor added to favourites."}


@router.delete("/me/favorites/{doctor_id}")
def remove_favorite(
    doctor_id: int,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Remove a doctor from the patient's favourites."""
    row = (
        db.query(models.PatientFavorite)
        .filter(
            models.PatientFavorite.patient_id == patient.id,
            models.PatientFavorite.doctor_id == doctor_id,
        )
        .first()
    )
    if row:
        db.delete(row)
        db.commit()
    return {"message": "Doctor removed from favourites."}


@router.get("/me/stats", response_model=schemas.PatientStatsOut)
def get_my_stats(
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Compute the numbers shown on the patient dashboard."""
    today = date.today()
    appointments = (
        db.query(models.Appointment)
        .filter(models.Appointment.patient_id == patient.id)
        .all()
    )
    favorite_count = (
        db.query(models.PatientFavorite)
        .filter(models.PatientFavorite.patient_id == patient.id)
        .count()
    )
    return schemas.PatientStatsOut(
        total=len(appointments),
        upcoming=sum(1 for a in appointments if a.appointment_date >= today and a.status == models.AppointmentStatus.BOOKED),
        completed=sum(1 for a in appointments if a.status == models.AppointmentStatus.COMPLETED),
        cancelled=sum(1 for a in appointments if a.status == models.AppointmentStatus.CANCELLED),
        favorite_count=favorite_count,
    )

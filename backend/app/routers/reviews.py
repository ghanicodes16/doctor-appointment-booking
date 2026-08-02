"""
routers/reviews.py - Doctor reviews (future-ready, but fully working).

    GET  /api/reviews?doctor_id=       list reviews for a doctor (public)
    POST /api/reviews                  create a review (patient only)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_patient

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


@router.get("", response_model=list[schemas.ReviewOut])
def list_reviews(
    doctor_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Return all reviews for a doctor."""
    reviews = (
        db.query(models.Review)
        .filter(models.Review.doctor_id == doctor_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )
    for review in reviews:
        review.patient_name = review.patient.name if review.patient else None
    return reviews


@router.post("", response_model=schemas.ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    doctor_id: int = Query(...),
    data: schemas.ReviewCreate | None = None,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Leave a rating/review for a doctor."""
    if data is None:
        data = schemas.ReviewCreate(rating=5)
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")

    review = models.Review(
        doctor_id=doctor_id,
        patient_id=patient.id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    review.patient_name = patient.name
    return review

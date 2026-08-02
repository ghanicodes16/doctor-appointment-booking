"""
routers/search.py - Advanced doctor search + symptom mapping.

    GET /api/search/doctors?q=&specialization=&city=&gender=&fee_min=&fee_max=&experience=&available=&online=&clinic=
    GET /api/search/specializations         list of specializations (for filters/UI)
    GET /api/search/symptoms?q=             symptom autocomplete/suggestions
    GET /api/search/recommendations         popular specializations (homepage + dashboard)

Smart symptom mapping: when a patient types something like "Tooth Pain",
the system looks it up in the symptoms table and maps it to the correct
specialization ("Dentist"), then returns matching doctors.

Example mappings (seeded):
    Tooth Pain      -> Dentist
    Stomach Pain    -> Gastroenterologist
    Chest Pain      -> Cardiologist
    Skin Rash       -> Dermatologist
    Ear Pain        -> ENT Specialist
    Eye Infection   -> Ophthalmologist
    Child Specialist/Paediatric -> Pediatrician
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_optional_patient
from ..utils import attach_is_favorite, attach_rating

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("/doctors", response_model=list[schemas.DoctorOut])
def search_doctors(
    q: str | None = Query(default=None, description="Free text: symptom, specialization, name, hospital or city"),
    specialization: str | None = Query(default=None),
    city: str | None = Query(default=None),
    gender: str | None = Query(default=None),
    fee_min: int | None = Query(default=None),
    fee_max: int | None = Query(default=None),
    experience: int | None = Query(default=None, description="Minimum years of experience"),
    available: bool | None = Query(default=None, description="Only doctors accepting bookings"),
    online: bool | None = Query(default=None, description="Only doctors offering online consultation"),
    clinic: bool | None = Query(default=None, description="Only doctors with clinic details"),
    sort: str | None = Query(default="relevance", description="relevance | rating | fee_low | fee_high"),
    patient: models.Patient | None = Depends(get_optional_patient),
    db: Session = Depends(get_db),
):
    """Search doctors using structured filters + smart symptom mapping."""
    query = db.query(models.Doctor)

    # --- Structured filters --------------------------------------------
    if specialization:
        query = query.filter(models.Doctor.specialization.ilike(f"%{specialization}%"))
    if city:
        query = query.filter(models.Doctor.city.ilike(f"%{city}%"))
    if gender:
        query = query.filter(models.Doctor.gender == gender)
    if fee_min is not None:
        query = query.filter(models.Doctor.first_visit_fee >= fee_min)
    if fee_max is not None:
        query = query.filter(models.Doctor.first_visit_fee <= fee_max)
    if experience is not None:
        query = query.filter(models.Doctor.years_of_experience >= experience)
    if available:
        query = query.filter(models.Doctor.booking_enabled.is_(True))
    if online:
        query = query.filter(models.Doctor.online_fee > 0)
    if clinic:
        query = query.filter(
            or_(models.Doctor.hospital_name.isnot(None), models.Doctor.clinic_address.isnot(None))
        )

    # --- Free-text / symptom search ------------------------------------
    if q and q.strip():
        term = q.strip()

        # 1. Symptom mapping: "Tooth Pain" -> ["Dentist"]
        mapped_specializations = set()
        matching_symptoms = (
            db.query(models.Symptom)
            .filter(or_(models.Symptom.name.ilike(f"%{term}%"), models.Symptom.name.ilike(f"%{term}%")))
            .all()
        )
        for symptom in matching_symptoms:
            for mapping in symptom.mappings:
                mapped_specializations.add(mapping.specialization.name)

        conditions = []
        # 2. Any specializations discovered from symptoms.
        for spec in mapped_specializations:
            conditions.append(models.Doctor.specialization.ilike(f"%{spec}%"))
        # 3. General text search across useful fields.
        conditions.extend(
            [
                models.Doctor.name.ilike(f"%{term}%"),
                models.Doctor.specialization.ilike(f"%{term}%"),
                models.Doctor.hospital_name.ilike(f"%{term}%"),
                models.Doctor.city.ilike(f"%{term}%"),
                models.Doctor.qualifications.ilike(f"%{term}%"),
            ]
        )
        query = query.filter(or_(*conditions))

    # Most relevant / active doctors first (overridden by an explicit sort).
    query = query.order_by(models.Doctor.is_verified.desc(), models.Doctor.patients_treated.desc())

    doctors = query.all()
    for doctor in doctors:
        attach_rating(db, doctor)
    attach_is_favorite(db, doctors, patient.id if patient else None)

    # In-memory sorting so we can sort by the computed rating.
    sort = (sort or "relevance").lower()
    if sort == "rating":
        doctors.sort(key=lambda d: d.rating_avg, reverse=True)
    elif sort == "fee_low":
        doctors.sort(key=lambda d: d.first_visit_fee or 0)
    elif sort == "fee_high":
        doctors.sort(key=lambda d: d.first_visit_fee or 0, reverse=True)

    return doctors


@router.get("/specializations", response_model=list[schemas.SpecializationOut])
def list_specializations(db: Session = Depends(get_db)):
    """Return the canonical list of medical specializations."""
    specs = db.query(models.Specialization).order_by(models.Specialization.name).all()
    for spec in specs:
        spec.doctor_count = (
            db.query(func.count(models.Doctor.id))
            .filter(models.Doctor.specialization.ilike(f"%{spec.name}%"))
            .scalar()
        )
    return specs


@router.get("/symptoms", response_model=list[schemas.SymptomOut])
def list_symptoms(
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Return symptoms, optionally filtered by a search term (autocomplete)."""
    query = db.query(models.Symptom)
    if q:
        query = query.filter(models.Symptom.name.ilike(f"%{q}%"))
    return query.order_by(models.Symptom.name).all()


@router.get("/recommendations", response_model=list[schemas.SpecializationOut])
def recommendations(db: Session = Depends(get_db)):
    """Return popular specializations (by number of doctors in them).

    Used for the homepage and the patient dashboard "Recommended
    Specialists" section.
    """
    popular = (
        db.query(models.Specialization)
        .join(models.Doctor, models.Doctor.specialization.ilike(models.Specialization.name))
        .group_by(models.Specialization.id)
        .order_by(func.count(models.Doctor.id).desc())
        .limit(8)
        .all()
    )
    # Fallback: if no doctors match a canonical name, return the first 8.
    if not popular:
        popular = db.query(models.Specialization).order_by(models.Specialization.name).limit(8).all()
    for spec in popular:
        spec.doctor_count = (
            db.query(func.count(models.Doctor.id))
            .filter(models.Doctor.specialization.ilike(f"%{spec.name}%"))
            .scalar()
        )
    return popular

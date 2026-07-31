"""
routers/patients.py - Patient profile endpoints.

Endpoints in this file:

    GET  /api/patients/me   -> current patient's profile (patient only)
"""

from fastapi import APIRouter, Depends

from .. import models, schemas
from ..deps import get_current_patient

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.get("/me", response_model=schemas.PatientOut)
def get_my_profile(patient: models.Patient = Depends(get_current_patient)):
    """Return the profile of the currently logged-in patient."""
    return patient

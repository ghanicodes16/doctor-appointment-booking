"""
routers/ai.py - ShifaBook AI Health Assistant (real Groq API, patient only).

    POST   /api/ai/reports                       upload a medical document
    GET    /api/ai/reports                       list the patient's documents
    GET    /api/ai/reports/{report_id}           one document + its analysis
    DELETE /api/ai/reports/{report_id}           delete a document
    POST   /api/ai/reports/{report_id}/analyze   run the Groq analysis
    POST   /api/ai/reports/{report_id}/chat      ask a follow-up question
    GET    /api/ai/reports/{report_id}/messages  chat history for a document

Every endpoint requires a patient login (see get_current_patient) and a
patient can only ever see THEIR OWN documents and chats.

The Groq API key never leaves this backend - the React app only talks to
these endpoints.
"""

import json
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import BASE_DIR
from ..database import get_db
from ..deps import get_current_patient
from services.ai import health_analyzer

router = APIRouter(prefix="/api/ai", tags=["AI Health Assistant"])

# Uploaded medical files live here - a private folder that is NEVER served
# by the web server, so patient data is not publicly accessible.
UPLOAD_ROOT = BASE_DIR / "uploads" / "ai"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
# Extension -> MIME type. Images are read by a Groq vision model at analyze
# time; PDFs have their text extracted on upload.
ALLOWED_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "pdf": "application/pdf",
}


def _get_own_report(report_id: int, patient: models.Patient, db: Session) -> models.AIReport:
    """Fetch a report but only if it belongs to the logged-in patient."""
    report = (
        db.query(models.AIReport)
        .filter(models.AIReport.id == report_id, models.AIReport.patient_id == patient.id)
        .first()
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return report


def _to_detail(report: models.AIReport) -> schemas.AIReportDetailOut:
    """Build the detail response, parsing the stored analysis JSON if present."""
    detail = schemas.AIReportDetailOut.model_validate(report)
    if report.analysis_result:
        try:
            detail.analysis = schemas.AIAnalysisResult.model_validate(json.loads(report.analysis_result))
        except Exception:
            detail.analysis = None
    return detail


@router.post("/reports", response_model=schemas.AIReportOut, status_code=status.HTTP_201_CREATED)
def upload_report(
    file: UploadFile = File(...),
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Upload a medical document (JPG/JPEG/PNG/WEBP/PDF, max 10 MB)."""
    original = file.filename or "report"
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, JPEG, PNG, WEBP or PDF files are allowed.",
        )

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty.")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is too large. Maximum size is 10 MB.")

    # Save privately - under backend/uploads/ai/<patient_id>/ - never served.
    # stored_path is stored RELATIVE to UPLOAD_ROOT so it stays portable
    # across machines (Windows locally, Linux on Railway).
    patient_dir = UPLOAD_ROOT / str(patient.id)
    patient_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    stored_path = patient_dir / stored_name
    stored_path.write_bytes(content)
    relative_path = f"{patient.id}/{stored_name}"

    extracted_text = None
    if ext == "pdf":
        extracted_text = health_analyzer.extract_text_from_pdf(content)

    report = models.AIReport(
        patient_id=patient.id,
        original_filename=original,
        stored_path=relative_path,
        file_type=ext,
        file_size=len(content),
        extracted_text=extracted_text,
        analysis_status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports", response_model=list[schemas.AIReportOut])
def list_reports(
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """List the patient's documents, newest first."""
    return (
        db.query(models.AIReport)
        .filter(models.AIReport.patient_id == patient.id)
        .order_by(models.AIReport.created_at.desc())
        .all()
    )


@router.get("/reports/{report_id}", response_model=schemas.AIReportDetailOut)
def get_report(
    report_id: int,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Get one document plus its parsed analysis."""
    report = _get_own_report(report_id, patient, db)
    return _to_detail(report)


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Delete a document, its stored file and its chat."""
    report = _get_own_report(report_id, patient, db)
    if report.stored_path:
        try:
            (UPLOAD_ROOT / report.stored_path).unlink(missing_ok=True)
        except Exception:
            pass
    db.delete(report)  # cascades to conversations + messages
    db.commit()


@router.post("/reports/{report_id}/analyze", response_model=schemas.AIReportDetailOut)
def analyze_report(
    report_id: int,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Run the REAL Groq analysis on a document and store the result."""
    report = _get_own_report(report_id, patient, db)
    report.analysis_status = "analyzing"
    report.error_message = None
    db.commit()

    image_bytes = None
    mime = "image/jpeg"
    if report.file_type in ("jpg", "jpeg", "png", "webp"):
        path = UPLOAD_ROOT / report.stored_path if report.stored_path else None
        if path and path.exists():
            image_bytes = path.read_bytes()
            mime = ALLOWED_TYPES.get(report.file_type, mime)

    try:
        raw = health_analyzer.analyze_report(
            extracted_text=report.extracted_text,
            file_name=report.original_filename,
            image_bytes=image_bytes,
            image_mime=mime,
        )
        # Validate the AI's reply BEFORE saving, so bad replies are rejected.
        validated = schemas.AIAnalysisResult.model_validate(raw)
        report.analysis_result = json.dumps(validated.model_dump())
        report.report_type = validated.report_type
        report.urgency_level = validated.urgency
        report.recommended_specialty = validated.recommended_specialty
        report.analysis_status = "analyzed"
        report.error_message = None
    except ValidationError:
        report.analysis_status = "failed"
        report.error_message = "The AI returned an incomplete response. Please try again."
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=report.error_message)
    except Exception as exc:
        report.analysis_status = "failed"
        report.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    db.commit()
    db.refresh(report)
    return _to_detail(report)


@router.post("/reports/{report_id}/chat", response_model=schemas.AIChatResponse)
def chat_with_report(
    report_id: int,
    payload: schemas.AIChatRequest,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Ask the AI a follow-up question about a document (real Groq call)."""
    report = _get_own_report(report_id, patient, db)

    conversation = (
        db.query(models.AIConversation)
        .filter(models.AIConversation.report_id == report.id)
        .first()
    )
    if conversation is None:
        conversation = models.AIConversation(patient_id=patient.id, report_id=report.id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    db.add(models.AIMessage(conversation_id=conversation.id, role="user", message=payload.message))
    db.commit()

    try:
        reply = health_analyzer.answer_question(
            report.extracted_text, report.analysis_result, payload.message
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI could not answer right now. Please try again.",
        )

    db.add(models.AIMessage(conversation_id=conversation.id, role="assistant", message=reply))
    db.commit()

    messages = (
        db.query(models.AIMessage)
        .filter(models.AIMessage.conversation_id == conversation.id)
        .order_by(models.AIMessage.created_at.asc())
        .all()
    )
    return {"messages": messages}


@router.get("/reports/{report_id}/messages", response_model=schemas.AIChatResponse)
def get_chat_messages(
    report_id: int,
    patient: models.Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Return the full chat history for a document."""
    report = _get_own_report(report_id, patient, db)
    conversation = (
        db.query(models.AIConversation)
        .filter(models.AIConversation.report_id == report.id)
        .first()
    )
    messages = []
    if conversation:
        messages = (
            db.query(models.AIMessage)
            .filter(models.AIMessage.conversation_id == conversation.id)
            .order_by(models.AIMessage.created_at.asc())
            .all()
        )
    return {"messages": messages}
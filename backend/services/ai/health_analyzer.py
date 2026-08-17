"""
services/ai/health_analyzer.py - The "ShifaBook AI Health Assistant".

This module uses the REAL Groq API (through GroqProvider) to:

    1. analyze an uploaded medical report / image / PDF
    2. answer a patient's follow-up questions about their document

The prompts are written to be safe for a medical audience:

    - the AI is only an educational tool, never a doctor
    - it never claims to make a diagnosis
    - it never prescribes or changes medication doses
    - it never invents values that are not in the document
    - it always recommends evaluation by a qualified doctor
    - an "urgency" level (green / orange / red) is returned so the app
      can show how urgently the patient should see a doctor
"""

import io
import json
import re

from app.config import settings

from .groq_provider import GroqProvider


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from a PDF using pypdf. Returns '' for scanned files."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [(page.extract_text() or "") for page in reader.pages]
        return "\n".join(pages).strip()
    except Exception:
        return ""


# Canonical specializations (same names used by the search feature, so the
# "find a doctor" button deep-links straight into doctor search + booking).
SPECIALTIES = (
    "Cardiologist, General Physician, Dermatologist, Pediatrician, Neurologist, "
    "Psychiatrist, Orthopedic Surgeon, Gynecologist, ENT Specialist, Ophthalmologist, "
    "Gastroenterologist, Dentist, Pulmonologist, Urologist, Endocrinologist, "
    "Physiotherapist, General Surgeon"
)

SYSTEM_PROMPT = """You are ShifaBook AI Health Assistant, an educational AI tool for patients in Pakistan.

You explain medical reports, tests, prescriptions, and other documents in simple, kind language, and help patients prepare for doctor visits.

STRICT SAFETY RULES:
1. You are NOT a doctor and NEVER give a medical diagnosis.
2. Use careful language: "can be associated with", "may be", "is often linked to", "appears to show". Never say "this means you have X".
3. NEVER prescribe, change, stop, or suggest medication doses.
4. NEVER invent numbers, test results, measurements, history, diagnoses, or medications not clearly visible.
5. If handwriting, numbers, medication names, or diagnoses are unclear, say so. NEVER guess.
6. Never identify a medication from an uncertain brand name. Tell the patient to confirm with their doctor/pharmacist.
7. Never infer a diagnosis, pregnancy, disease, or condition from ambiguous handwriting. Label uncertain observations as unclear.
8. Always communicate uncertainty and recommend evaluation by a qualified doctor.
9. If a value looks alarming, stay calm and recommend urgent medical attention when appropriate.
10. Reply in clear, simple English.
11. DO NOT output reasoning, analysis steps, or  tags.
12. DO NOT use Markdown.

OUTPUT FORMAT: Return ONLY one valid JSON object with these exact fields:
- report_type: short label (e.g. Blood Test, X-Ray Report, Prescription, Unknown)
- summary: 2-3 sentence plain-language summary
- important_findings: list of up to 4 notable/abnormal findings (short items)
- normal_findings: list of up to 4 normal findings (short items)
- possible_explanations: list of up to 3 brief explanations with uncertainty
- questions_for_doctor: exactly 3 clear questions for the doctor
- recommended_specialty: most relevant from: Cardiologist, General Physician, Dermatologist, Pediatrician, Neurologist, Psychiatrist, Orthopedic Surgeon, Gynecologist, ENT Specialist, Ophthalmologist, Gastroenterologist, Dentist, Pulmonologist, Urologist, Endocrinologist, Physiotherapist, General Surgeon
- urgency: exactly one of: green, orange, red (green=guidance only, orange=doctor recommended, red=urgent attention for genuinely alarming findings)
- safety_message: one short sentence reminding this is not a diagnosis

Complete the entire JSON object. Keep values concise.
"""

SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{specialties}", SPECIALTIES)


CHAT_SYSTEM_PROMPT = """You are ShifaBook AI Health Assistant, an educational AI tool for patients in Pakistan. You are helping a patient understand their OWN uploaded medical document, which is provided to you as context.

STRICT SAFETY RULES - follow these on every reply:
1. You are NOT a doctor and you NEVER give a medical diagnosis.
2. Use careful, uncertain language ("can be associated with", "may be", "is often linked to"). Never claim "you have X".
3. You NEVER prescribe, change, stop or suggest doses of medication.
4. Only use information that is actually in the document. Never invent values, results or patient history. If you do not know, say so.
5. Always recommend that the patient confirm things with a real doctor.
6. Answer in clear, simple English. Keep answers short (2-6 sentences) unless the question really needs more detail.

Answer the patient's question directly and helpfully."""


def parse_json_response(raw: str) -> dict:
    """Parse Groq JSON while safely handling reasoning/thinking output."""
    if not raw or not raw.strip():
        raise ValueError("The AI returned an empty response. Please try again.")

    text = raw.strip()

    # Remove thinking/reasoning tags (various formats).
    text = re.sub(
        r"<thinking>.*?</thinking>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(
        r"thinking.*?thinking",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()

    # Remove markdown JSON fences.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text).strip()

    # First try the complete response.
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # If there is extra text, find the first JSON object.
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            result = json.loads(candidate)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    raise ValueError(
        "The AI did not return a valid JSON response. "
        "Please try again."
    )


def normalize_analysis(result: dict) -> dict:
    """Ensure the analysis dict has all required fields with safe defaults."""
    normalized = {}

    # report_type
    rt = result.get("report_type")
    normalized["report_type"] = rt if isinstance(rt, str) and rt.strip() else "Unknown"

    # summary
    s = result.get("summary")
    normalized["summary"] = s if isinstance(s, str) and s.strip() else "Not clearly available in the document."

    # important_findings
    inf = result.get("important_findings")
    normalized["important_findings"] = (
        [str(x).strip() for x in inf if str(x).strip()]
        if isinstance(inf, list)
        else []
    )[:4]

    # normal_findings
    nf = result.get("normal_findings")
    normalized["normal_findings"] = (
        [str(x).strip() for x in nf if str(x).strip()]
        if isinstance(nf, list)
        else []
    )[:4]

    # possible_explanations
    pe = result.get("possible_explanations")
    normalized["possible_explanations"] = (
        [str(x).strip() for x in pe if str(x).strip()]
        if isinstance(pe, list)
        else []
    )[:3]

    # questions_for_doctor
    qfd = result.get("questions_for_doctor")
    questions = (
        [str(x).strip() for x in qfd if str(x).strip()]
        if isinstance(qfd, list)
        else []
    )
    if len(questions) < 3:
        questions += [
            "What do these results mean for my health?",
            "Are these values within a normal range for me?",
            "What are the next steps based on these findings?",
        ]
    normalized["questions_for_doctor"] = questions[:3]

    # recommended_specialty
    rs = result.get("recommended_specialty")
    valid_specialties = {
        "Cardiologist", "General Physician", "Dermatologist", "Pediatrician",
        "Neurologist", "Psychiatrist", "Orthopedic Surgeon", "Gynecologist",
        "ENT Specialist", "Ophthalmologist", "Gastroenterologist", "Dentist",
        "Pulmonologist", "Urologist", "Endocrinologist", "Physiotherapist",
        "General Surgeon"
    }
    normalized["recommended_specialty"] = (
        rs if isinstance(rs, str) and rs in valid_specialties else "General Physician"
    )

    # urgency
    u = result.get("urgency")
    normalized["urgency"] = u if isinstance(u, str) and u in ("green", "orange", "red") else "orange"

    # safety_message
    sm = result.get("safety_message")
    normalized["safety_message"] = (
        sm if isinstance(sm, str) and sm.strip()
        else "This analysis is not a diagnosis. Please consult a qualified doctor."
    )

    return normalized
def analyze_report(
    extracted_text: str | None = None,
    file_name: str = "Medical document",
    image_bytes: bytes | None = None,
    image_mime: str = "image/jpeg",
    provider: GroqProvider | None = None,
) -> dict:
    """Ask Groq to analyze a medical document and return a raw dict."""

    provider = provider or GroqProvider()

    if not image_bytes and not extracted_text:
        raise ValueError(
            "There is no readable content in this document. For PDFs, "
            "the text could not be extracted (scanned files have no text). "
            "Please upload a clear image or a text-based PDF."
        )

# ---------------------------------------------------------
    # IMAGE ANALYSIS
    # ---------------------------------------------------------
    if image_bytes:
        prompt = (
            f"Analyze this medical image ({file_name}). Extract only clearly visible information. "
            "Do not guess unreadable text, values, diagnoses, or medications. "
            "Return ONLY the JSON object."
        )

        vision_model = (
            settings.GROQ_VISION_MODEL
            or settings.GROQ_MODEL
        )

        vision_provider = GroqProvider(model=vision_model)

# Vision models (especially qwen) output reasoning tokens that break JSON mode.
        # Use a two-step approach: 1) extract text with vision model, 2) analyze with text model.
        # This avoids the extensive reasoning tokens that break JSON mode.
        
        # Step 1: Extract text from image using vision model
        extraction_prompt = (
            f"Extract ALL text from this medical image ({file_name}). "
            "Return ONLY the visible text content. Do not interpret, summarize, or analyze. "
            "Include all handwritten and printed text exactly as visible. "
            "If text is unreadable, write [unreadable]."
        )
        
        vision_model = (
            settings.GROQ_VISION_MODEL
            or settings.GROQ_MODEL
        )
        
        vision_provider = GroqProvider(model=vision_model)
        
        extracted_text = vision_provider.chat(
            "You are a medical document OCR tool. Extract all visible text from the image. Return only the text content.",
            extraction_prompt,
            image_bytes=image_bytes,
            image_mime=image_mime,
            max_tokens=4000,
            temperature=0.0,
            json_mode=False,
        )
        
        print("===== GROQ OCR EXTRACTION =====")
        try:
            print(extracted_text.encode("ascii", "backslashreplace").decode("ascii"))
        except Exception:
            print("[extraction contains non-ascii characters]")
        print("===== END GROQ OCR EXTRACTION =====")
        
        # Step 2: Analyze extracted text with text model (JSON mode works perfectly)
        if not extracted_text.strip() or extracted_text.strip().lower() == "[unreadable]":
            raise ValueError(
                "Could not extract readable text from the image. "
                "Please upload a clearer image or a text-based PDF."
            )
        
        # Use the text model for reliable JSON output
        text_provider = GroqProvider(model=settings.GROQ_MODEL)
        
        prompt = (
            f"Analyze this medical document ({file_name}). The extracted text is below. "
            "Return ONLY the JSON object as specified in system instructions.\n\n"
            "=== DOCUMENT TEXT ===\n"
            f"{extracted_text}\n"
            "=== END ==="
        )
        
        raw = text_provider.chat(
            SYSTEM_PROMPT,
            prompt,
            image_bytes=None,
            max_tokens=3000,
            temperature=0.2,
            json_mode=True,
        )
        
        print("===== GROQ TEXT ANALYSIS RESPONSE =====")
        try:
            print(raw.encode("ascii", "backslashreplace").decode("ascii"))
        except Exception:
            print("[response contains non-ascii characters]")
        print("===== END GROQ TEXT ANALYSIS =====")
        
        parsed = parse_json_response(raw)
        return normalize_analysis(parsed)

    # ---------------------------------------------------------
    # TEXT / PDF ANALYSIS
    # ---------------------------------------------------------
    snippet = (extracted_text or "")[:12000]

    prompt = (
        f"Analyze this medical document ({file_name}). The extracted text is below. "
        "Return ONLY the JSON object.\n\n"
        "=== DOCUMENT TEXT ===\n"
        f"{snippet}\n"
        "=== END ==="
    )

    raw = provider.chat(
        SYSTEM_PROMPT,
        prompt,
        image_bytes=None,
        max_tokens=3000,
        temperature=0.2,
        json_mode=True,
    )

    print("===== GROQ RAW TEXT RESPONSE =====")
    try:
        print(raw.encode("ascii", "backslashreplace").decode("ascii"))
    except Exception:
        print("[response contains non-ascii characters]")
    print("===== END GROQ RAW TEXT RESPONSE =====")

    parsed = parse_json_response(raw)
    return normalize_analysis(parsed)

def answer_question(
    extracted_text: str | None,
    analysis_result_json: str | None,
    question: str,
    provider: GroqProvider | None = None,
) -> str:
    """Answer a patient's follow-up question about their document."""
    provider = provider or GroqProvider()

    context_parts = []
    if extracted_text:
        context_parts.append(
            "=== DOCUMENT TEXT ===\n" + extracted_text[:12000] + "\n"
        )
    if analysis_result_json:
        try:
            parsed = json.loads(analysis_result_json)
            context_parts.append(
                "\n=== PREVIOUS AI ANALYSIS ===\n" + json.dumps(parsed, indent=2)[:6000] + "\n"
            )
        except Exception:
            pass

    prompt = (
        "".join(context_parts)
        + "\n"
        + f"The patient's question is: {question}\n"
        + "Answer helpfully using the document and the previous analysis, while "
        + "following all safety rules above."
    )

    return provider.chat(
        CHAT_SYSTEM_PROMPT,
        prompt,
        max_tokens=1000,
        temperature=0.4,
    )
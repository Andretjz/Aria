"""Text Practice module router (Module 4) — upload + analyze text.

Full implementation by Alice_Analysis in Phase 5.
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post(
    "/upload",
    summary="Upload a text document for practice",
    description=(
        "Upload PDF/TXT/DOCX in any language. Select a target practice language. "
        "Returns: Helsinki-NLP translation, CEFR-ranked vocabulary, comprehension quiz, "
        "grammar patterns, and adds vocabulary to the user's flashcard deck."
    ),
    responses={
        200: {"description": "Text processed, analysis returned"},
        413: {"description": "File exceeds 10MB limit"},
        422: {"description": "Unsupported file format"},
    },
)
async def upload_text(
    document: UploadFile = File(..., description="PDF, TXT, or DOCX file (max 10MB)"),
    target_lang: str = Form("de", description="Target language to practice (de/en/es/fr/it)"),
) -> JSONResponse:
    """Upload and analyse a text document.

    Returns:
        JSON with translation, vocabulary, quiz, and grammar patterns.
    """
    return JSONResponse(
        {"detail": "Not implemented — Phase 5 (Alice_Analysis)"},
        status_code=501,
    )

"""Text Practice module router (Module 4) — upload + analyze text.

POST /api/v1/text-practice/upload — Alice_Analysis (Phase 5).

Pipeline:
  1. Extract text from uploaded document (TXT / PDF / DOCX)
  2. Ask LLM to detect language, rank CEFR vocabulary, generate quiz + grammar
  3. Translate to target_lang via TranslationService
  4. Return structured result
"""
from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from aria.backend.core.config import settings
from aria.backend.core.llm_utils import parse_json_from_llm
from aria.backend.core.logging import get_logger
from aria.backend.modules.auth.models import User
from aria.backend.modules.auth.users import current_active_user
from aria.backend.modules.text_practice.schemas import (
    CEFRVocabItem,
    TextGrammarSpotlight,
    TextPracticeRead,
    TextQuizQuestion,
)
from aria.backend.services.factory import get_llm_service, get_translation_service
from aria.backend.services.interfaces import LLMService, TranslationService

log = get_logger(__name__)
router = APIRouter()

_SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}
_MAX_TEXT_CHARS = 8_000  # truncation limit sent to LLM

_TEXT_ANALYSIS_SYSTEM = (
    "You are a language learning assistant. Given text in any language, return a JSON object with:\n"
    '  "detected_language": "en",  // BCP-47 code of the source text\n'
    '  "vocabulary": [{"word": "...", "cefr_level": "B1", "definition": "..."}],  // up to 10 key words\n'
    '  "quiz": [{"question": "...", "options": ["A", "B", "C", "D"], "correct": 0, "explanation": "..."}],  // 3 questions\n'
    '  "grammar_spotlights": [{"rule": "...", "example": "...", "correction": "...", "frequency": 1}]  // up to 3 patterns\n'
    "Return only valid JSON — no markdown, no explanation."
)


def get_text_llm() -> LLMService:
    """FastAPI dependency — overridable in tests."""
    return get_llm_service()


def get_text_translation() -> TranslationService:
    """FastAPI dependency — overridable in tests."""
    return get_translation_service()


def _extract_text(content: bytes, ext: str) -> str:
    """Extract plain text from a document given its file extension."""
    if ext == ".txt":
        return content.decode("utf-8", errors="replace")
    if ext == ".pdf":
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == ".docx":
        import docx
        doc = docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    raise HTTPException(status_code=422, detail=f"Unsupported format: {ext}")


async def _analyse_text(
    text: str,
    llm: LLMService,
) -> dict:
    """Ask the LLM to analyse text and return structured JSON."""
    snippet = text[:_MAX_TEXT_CHARS]
    messages = [{"role": "user", "content": f"Text to analyse:\n\n{snippet}"}]
    try:
        raw = await llm.generate_complete(messages, system=_TEXT_ANALYSIS_SYSTEM, max_tokens=2048)
        try:
            clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            parsed = json.loads(clean)
        except (json.JSONDecodeError, AttributeError):
            parsed = parse_json_from_llm(raw)
        if isinstance(parsed, dict):
            return parsed
    except Exception as exc:
        log.warning("text_practice_llm_failed", error=str(exc))
    return {}


@router.post(
    "/upload",
    response_model=TextPracticeRead,
    summary="Upload a text document for practice",
    description=(
        "Upload PDF/TXT/DOCX in any language. Select a target practice language. "
        "Returns: Helsinki-NLP translation, CEFR-ranked vocabulary, comprehension quiz, "
        "and grammar patterns."
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
    llm: LLMService = Depends(get_text_llm),
    translation: TranslationService = Depends(get_text_translation),
    current_user: User = Depends(current_active_user),
) -> TextPracticeRead:
    """Upload and analyse a text document.

    Args:
        document: Uploaded text document.
        target_lang: Language to translate the document into for practice.
        llm: Injected LLM service (overridable in tests).
        translation: Injected translation service (overridable in tests).

    Returns:
        TextPracticeRead with translation, vocabulary, quiz, and grammar patterns.
    """
    max_bytes = 10 * 1024 * 1024
    content = await document.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit.")

    filename = document.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in _SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported format '{ext}'. Supported: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}",
        )

    text = _extract_text(content, ext)
    if not text.strip():
        raise HTTPException(status_code=422, detail="Document contains no extractable text.")

    analysis = await _analyse_text(text, llm)

    detected_language = str(analysis.get("detected_language", "en"))

    if detected_language == target_lang:
        translated_text = text[:_MAX_TEXT_CHARS]
    else:
        try:
            translated_text = await translation.translate(
                text[:_MAX_TEXT_CHARS], detected_language, target_lang
            )
        except Exception as exc:
            log.warning("text_practice_translation_failed", error=str(exc))
            translated_text = ""

    raw_vocab = analysis.get("vocabulary", [])
    vocabulary = []
    for item in raw_vocab if isinstance(raw_vocab, list) else []:
        if isinstance(item, dict) and item.get("word"):
            vocabulary.append(CEFRVocabItem(
                word=str(item["word"]),
                cefr_level=str(item.get("cefr_level", "B1")),
                definition=str(item.get("definition", "")),
            ))

    raw_quiz = analysis.get("quiz", [])
    quiz = []
    for item in raw_quiz if isinstance(raw_quiz, list) else []:
        if isinstance(item, dict) and item.get("question"):
            options = item.get("options", [])
            if isinstance(options, list) and len(options) == 4:
                quiz.append(TextQuizQuestion(
                    question=str(item["question"]),
                    options=[str(o) for o in options],
                    correct=int(item.get("correct", 0)),
                    explanation=str(item.get("explanation", "")),
                ))

    raw_grammar = analysis.get("grammar_spotlights", [])
    grammar_spotlights = []
    for item in raw_grammar if isinstance(raw_grammar, list) else []:
        if isinstance(item, dict) and item.get("rule"):
            grammar_spotlights.append(TextGrammarSpotlight(
                rule=str(item["rule"]),
                example=str(item.get("example", "")),
                correction=str(item.get("correction", "")),
                frequency=int(item.get("frequency", 1)),
            ))

    return TextPracticeRead(
        detected_language=detected_language,
        translated_text=translated_text,
        vocabulary=vocabulary,
        quiz=quiz,
        grammar_spotlights=grammar_spotlights,
    )

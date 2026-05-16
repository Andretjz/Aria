"""Analysis module router — 6-pass audio pipeline endpoint.

POST /api/v1/sessions/analyze — upload audio → full analysis JSON.
Pete_Pipeline implements Passes 1–4 (STT, diarization, speaker assignment,
LLM fluency/vocab). Alice_Analysis (Phase 5) adds Passes 5–6
(comprehension quiz, grammar spotlight, voice blueprints).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from aria.backend.core.config import settings
from aria.backend.core.exceptions import AudioFormatError, STTError
from aria.backend.core.logging import get_logger
from aria.backend.database import get_db
from aria.backend.modules.analysis.models import AnalysisSession
from aria.backend.modules.analysis.pipeline import AnalysisPipeline
from aria.backend.modules.analysis.schemas import (
    AnalysisSessionRead,
    GrammarSpotlight,
    QuizQuestion,
    SpeakerSegmentRead,
    VoiceBlueprint,
)
from aria.backend.modules.auth.models import User
from aria.backend.modules.auth.users import current_active_user
from aria.backend.modules.billing.dependencies import check_daily_analysis
from aria.backend.services.factory import (
    get_diarization_service,
    get_llm_service,
    get_stt_service,
)

log = get_logger(__name__)
router = APIRouter()

SUPPORTED_EXTENSIONS = {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".webm"}


def get_pipeline() -> AnalysisPipeline:
    """FastAPI dependency — returns an AnalysisPipeline backed by current .env providers.

    Overridden in tests via app.dependency_overrides[get_pipeline].
    """
    return AnalysisPipeline(
        stt=get_stt_service(),
        diarization=get_diarization_service(),
        llm=get_llm_service(),
    )


@router.post(
    "/analyze",
    response_model=AnalysisSessionRead,
    status_code=200,
    summary="Analyse an uploaded audio file",
    description=(
        "Runs the Aria 6-pass analysis pipeline on an uploaded audio file. "
        "Returns speaker-labelled transcript, fluency score, vocabulary list, "
        "comprehension quiz, grammar spotlight, and per-speaker voice blueprints. "
        "Supports de/en/es/fr/it as target languages; input language auto-detected."
    ),
    responses={
        200: {"description": "Analysis complete, full JSON result returned"},
        413: {"description": "File exceeds 50 MB limit"},
        422: {"description": "Unsupported audio format or validation error"},
        500: {"description": "STT or pipeline failure"},
    },
)
async def analyze_session(
    audio: UploadFile = File(..., description="Audio file (mp3/m4a/wav/ogg/flac/webm, max 50 MB)"),
    language: str = Form("auto", description="Target language code (de/en/es/fr/it) or 'auto'"),
    pipeline: AnalysisPipeline = Depends(get_pipeline),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
    _quota: None = Depends(check_daily_analysis),
) -> AnalysisSessionRead:
    """Run the 6-pass analysis pipeline on an uploaded audio file.

    Args:
        audio: Uploaded audio file (multipart/form-data).
        language: Target language or "auto" for auto-detection.
        pipeline: Injected pipeline instance (overridable in tests).
        db: Injected database session.

    Returns:
        AnalysisSessionRead with all analysis passes included.

    Raises:
        413: File exceeds MAX_UPLOAD_SIZE_MB.
        422: Unsupported audio format.
        500: STT or pipeline failure.
    """
    content = await audio.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
        )

    filename = audio.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported audio format '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = await pipeline.run(tmp_path, language)
    except (STTError, AudioFormatError) as exc:
        log.error("pipeline_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    session = AnalysisSession(
        user_id=current_user.id,
        audio_filename=filename,
        language=result.language,
        duration_seconds=result.duration_seconds,
        num_speakers=result.num_speakers,
        transcript_json=json.dumps([s.to_dict() for s in result.segments]),
        fluency_score=result.fluency_score,
        vocabulary_json=json.dumps(result.vocabulary),
        quiz_json=json.dumps(result.quiz) if result.quiz else None,
        grammar_json=json.dumps(result.grammar_spotlights) if result.grammar_spotlights else None,
        voice_blueprints_json=json.dumps(result.voice_blueprints) if result.voice_blueprints else None,
        status="complete",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return AnalysisSessionRead(
        id=session.id,
        created_at=session.created_at,
        audio_filename=session.audio_filename,
        language=session.language,
        duration_seconds=session.duration_seconds,
        num_speakers=session.num_speakers,
        segments=[SpeakerSegmentRead(**s) for s in json.loads(session.transcript_json)],
        fluency_score=session.fluency_score,
        vocabulary=json.loads(session.vocabulary_json),
        status=session.status,
        quiz=[QuizQuestion(**q) for q in json.loads(session.quiz_json or "[]")],
        grammar_spotlights=[GrammarSpotlight(**g) for g in json.loads(session.grammar_json or "[]")],
        voice_blueprints=[VoiceBlueprint(**v) for v in json.loads(session.voice_blueprints_json or "[]")],
    )

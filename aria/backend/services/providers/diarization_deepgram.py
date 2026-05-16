"""Deepgram diarization provider — production (Nova-3 batch with diarization).

Used when DIAR_BACKEND=deepgram. Deepgram Nova-3 returns diarization data
alongside its transcription, eliminating the need for a separate diarization
service. See ADR-001.
"""
from __future__ import annotations

from pathlib import Path

from aria.backend.core.exceptions import DiarizationError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import DiarizationService, DiarizationResult, DiarizationSegment

log = get_logger(__name__)


class DeepgramDiarizationService(DiarizationService):
    """Deepgram Nova-3 diarization — production uploaded-file processing.

    Args:
        api_key: Deepgram API key from DEEPGRAM_API_KEY env var.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def diarise(
        self,
        path: Path,
        num_speakers: int = 0,
    ) -> DiarizationResult:
        """Run Deepgram Nova-3 diarization on an audio file.

        Args:
            path: Absolute path to the audio file.
            num_speakers: Expected number of speakers; 0 = auto-detect.

        Returns:
            DiarizationResult parsed from Deepgram's diarize response.

        Raises:
            DiarizationError: If the API call fails.

        Note:
            Pete_Pipeline (Phase 3) implements the full API call here.
            Sam_Architect provides the stub so the interface is importable.
        """
        raise NotImplementedError(
            "DeepgramDiarizationService.diarise implemented by Pete_Pipeline in Phase 3"
        )


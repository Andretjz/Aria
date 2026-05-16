"""Pyannote diarization provider — dev only (GPU required).

Used when DIAR_BACKEND=local. In production, Gladia handles diarization
as part of its STT response (no separate service call needed).
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from aria.backend.core.exceptions import DiarizationError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import DiarizationService, DiarizationResult, DiarizationSegment

log = get_logger(__name__)


class PyannoteService(DiarizationService):
    """Pyannote.audio speaker diarization — local GPU development.

    Args:
        hf_token: HuggingFace token for downloading the pyannote model.
    """

    def __init__(self, hf_token: str) -> None:
        self._hf_token = hf_token
        self._pipeline = None

    def _load_pipeline(self):
        if self._pipeline is None:
            try:
                from pyannote.audio import Pipeline
                log.info("loading_pyannote_pipeline")
                self._pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self._hf_token,
                )
                try:
                    import torch
                    if torch.cuda.is_available():
                        self._pipeline.to(torch.device("cuda"))
                except ImportError:
                    pass
                log.info("pyannote_pipeline_ready")
            except Exception as exc:
                raise DiarizationError(f"Failed to load pyannote pipeline: {exc}") from exc
        return self._pipeline

    async def diarise(
        self,
        path: Path,
        num_speakers: int = 0,
    ) -> DiarizationResult:
        """Run pyannote speaker diarization on an audio file.

        Args:
            path: Absolute path to the audio file.
            num_speakers: Expected number of speakers; 0 = auto-detect.

        Returns:
            DiarizationResult with speaker-labelled time spans.

        Raises:
            DiarizationError: If the pipeline fails.

        Note:
            VRAM freed after each call via flush_gpu(). See core/gpu.py.
        """
        pipeline = self._load_pipeline()
        kwargs = {}
        if num_speakers > 0:
            kwargs["num_speakers"] = num_speakers

        try:
            def _run():
                return pipeline(str(path), **kwargs)

            diarization = await asyncio.to_thread(_run)
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append(DiarizationSegment(
                    speaker=speaker,
                    start=turn.start,
                    end=turn.end,
                ))

            speakers = list({s.speaker for s in segments})
            log.info(
                "diarization_complete",
                path=str(path),
                segments=len(segments),
                speakers=len(speakers),
            )
            return DiarizationResult(segments=segments, num_speakers=len(speakers))
        except Exception as exc:
            raise DiarizationError(f"Pyannote diarization failed: {exc}") from exc
        finally:
            from aria.backend.core.gpu import flush_gpu
            flush_gpu()


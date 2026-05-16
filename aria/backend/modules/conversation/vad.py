"""Voice Activity Detection — energy-based turn-end detection.

EnergyVAD accumulates 16-bit PCM chunks and triggers when RMS energy drops
below a configurable threshold for a configurable silence window.

Decision: simple RMS threshold is accurate enough at session scale and avoids
the GPU dependency that WebRTC-VAD or Silero-VAD would require in dev. A more
sophisticated VAD can be swapped in by sub-classing EnergyVAD and overriding
`process_chunk`.
"""
from __future__ import annotations

import struct


class EnergyVAD:
    """Energy-based, sample-accurate voice activity detector.

    Args:
        sample_rate: Input audio sample rate in Hz (must match PCM stream).
        silence_threshold_rms: RMS energy below which a frame is silent.
            For 16-bit PCM the scale is 0–32767; 300 is a comfortable low
            threshold that captures near-silence without false triggers.
        silence_duration_ms: Consecutive silence required (ms) before a
            turn-end is signalled. 500 ms gives the speaker time to pause
            mid-sentence without prematurely cutting them off.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        silence_threshold_rms: float = 300.0,
        silence_duration_ms: int = 500,
    ) -> None:
        self._sample_rate = sample_rate
        self._threshold = silence_threshold_rms
        self._silence_samples_needed = int(sample_rate * silence_duration_ms / 1000)
        self._silent_sample_count: int = 0
        self._speech_started: bool = False

    # ── public API ────────────────────────────────────────────────────────────

    def process_chunk(self, pcm_bytes: bytes) -> bool:
        """Process one PCM chunk; return True when a turn-end is detected.

        A turn-end fires once per speech segment: only after the VAD has seen
        speech (RMS > threshold) followed by enough silence.

        Args:
            pcm_bytes: Raw 16-bit little-endian mono PCM bytes.

        Returns:
            True exactly once per detected utterance end; False otherwise.
        """
        rms = self._compute_rms(pcm_bytes)
        samples_in_chunk = len(pcm_bytes) // 2  # 2 bytes per 16-bit sample

        if rms > self._threshold:
            self._speech_started = True
            self._silent_sample_count = 0
            return False

        if self._speech_started:
            self._silent_sample_count += samples_in_chunk
            if self._silent_sample_count >= self._silence_samples_needed:
                self._speech_started = False
                self._silent_sample_count = 0
                return True

        return False

    def reset(self) -> None:
        """Reset internal state; call after processing each complete turn."""
        self._silent_sample_count = 0
        self._speech_started = False

    # ── internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_rms(pcm_bytes: bytes) -> float:
        """Compute root-mean-square energy of 16-bit LE mono PCM bytes.

        Args:
            pcm_bytes: Raw PCM bytes (must be an even number of bytes).

        Returns:
            RMS energy on the 0–32767 scale; 0.0 for empty input.
        """
        n = len(pcm_bytes) // 2
        if n == 0:
            return 0.0
        samples = struct.unpack(f"<{n}h", pcm_bytes[: n * 2])
        mean_sq = sum(s * s for s in samples) / n
        return mean_sq ** 0.5

"""Helsinki-NLP offline translation provider — dev + production.

Used when TRANSLATION_BACKEND=helsinki (default). CPU-only, no API cost.
Helsinki-NLP/opus-mt models are downloaded from HuggingFace on first use
and cached locally. See ADR-009 for language architecture rationale.
"""
from __future__ import annotations

import asyncio
from functools import lru_cache

from aria.backend.core.exceptions import TranslationError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import TranslationService

log = get_logger(__name__)


@lru_cache(maxsize=20)
def _get_pipeline(src: str, tgt: str):
    """Load (and cache) a Helsinki-NLP translation pipeline for a language pair.

    Args:
        src: Source language BCP-47 code.
        tgt: Target language BCP-47 code.

    Returns:
        A transformers pipeline for translation.

    Raises:
        TranslationError: If the model is not available for this language pair.
    """
    try:
        from transformers import pipeline as hf_pipeline
        model_name = f"Helsinki-NLP/opus-mt-{src}-{tgt}"
        log.info("loading_translation_model", model=model_name)
        return hf_pipeline("translation", model=model_name)
    except Exception as exc:
        raise TranslationError(
            f"Helsinki-NLP model not available for {src}→{tgt}: {exc}"
        ) from exc


class HelsinkiTranslationService(TranslationService):
    """Helsinki-NLP opus-mt offline translation — zero API cost."""

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate text using the appropriate Helsinki-NLP opus-mt model.

        Args:
            text: Input text to translate.
            source_lang: BCP-47 source language code (e.g. "de").
            target_lang: BCP-47 target language code (e.g. "en").

        Returns:
            Translated text string.

        Raises:
            TranslationError: If the language pair is unsupported or translation fails.

        Note:
            Models are lazy-loaded and cached. First call for a new language pair
            downloads ~300MB from HuggingFace. Subsequent calls are instant.
        """
        if source_lang == target_lang:
            return text

        try:
            pipe = _get_pipeline(source_lang, target_lang)
            result = await asyncio.to_thread(pipe, text, max_length=512)
            return result[0]["translation_text"]
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(
                f"Helsinki-NLP translation failed ({source_lang}→{target_lang}): {exc}"
            ) from exc


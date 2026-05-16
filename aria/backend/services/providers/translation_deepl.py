"""DeepL translation provider — optional production upgrade.

Used when TRANSLATION_BACKEND=deepl. Higher quality than Helsinki-NLP
but incurs API cost. Switch via .env — no code change required.
"""
from __future__ import annotations

from aria.backend.core.exceptions import TranslationError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import TranslationService

log = get_logger(__name__)


class DeepLTranslationService(TranslationService):
    """DeepL API translation — optional higher-quality alternative.

    Pete_Pipeline (Phase 3) or Alice_Analysis (Phase 5) implement the
    full API call. Sam_Architect provides the stub for import correctness.
    """

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate text using the DeepL API.

        Args:
            text: Input text to translate.
            source_lang: BCP-47 source language code.
            target_lang: BCP-47 target language code.

        Returns:
            Translated text string.

        Raises:
            TranslationError: If the API call fails.
        """
        raise NotImplementedError(
            "DeepLTranslationService implemented in Phase 5 (Alice_Analysis)"
        )


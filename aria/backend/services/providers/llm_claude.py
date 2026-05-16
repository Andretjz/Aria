"""Claude API LLM provider — production.

Used when LLM_BACKEND=claude. Routes to Haiku (speed) or Sonnet (quality)
depending on the caller. See ADR-002 for model routing rationale.
"""
from __future__ import annotations

from typing import AsyncIterator

from aria.backend.core.exceptions import LLMError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import LLMService

log = get_logger(__name__)


class ClaudeLLMService(LLMService):
    """Anthropic Claude API backed LLM service for production.

    Args:
        api_key: Anthropic API key from ANTHROPIC_API_KEY env var.
        model: Claude model ID (default: Haiku for speed + cost).
    """

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001") -> None:
        self._api_key = api_key
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
            except ImportError as exc:
                raise LLMError("anthropic package not installed. Run: pip install anthropic") from exc
        return self._client

    async def generate(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Generate a streaming response via the Claude Messages API.

        Args:
            messages: List of {"role": str, "content": str} dicts.
            system: Optional system prompt string.
            max_tokens: Maximum tokens to generate.

        Yields:
            Text chunks from the Claude streaming response.

        Raises:
            LLMError: If the Claude API call fails.

        Note:
            Uses prompt caching (cache_control) for system prompts longer than
            1024 tokens to reduce latency and cost on repeated analysis calls.
            See Anthropic prompt caching docs.
        """
        client = self._get_client()
        kwargs: dict = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ]

        try:
            async with client.messages.stream(**kwargs) as stream:
                async for chunk in stream.text_stream:
                    yield chunk
        except Exception as exc:
            raise LLMError(f"Claude API call failed: {exc}", detail=str(exc)) from exc


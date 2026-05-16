"""Ollama LLM provider — dev only (local GPU, llama3.1:8b).

Used when LLM_BACKEND=ollama. In production, swap to ClaudeLLMService
via the .env file. See ADR-002 for model routing rationale.
"""
from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from aria.backend.core.exceptions import LLMError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import LLMService

log = get_logger(__name__)


class OllamaLLMService(LLMService):
    """Ollama-backed LLM service for local development.

    Args:
        base_url: Ollama server URL (default: http://127.0.0.1:11434).
        model: Model name to use (e.g. "llama3.1:8b").
    """

    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "llama3.1:8b") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def generate(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Generate a streaming response via Ollama /api/chat.

        Args:
            messages: List of {"role": str, "content": str} dicts.
            system: Optional system prompt string.
            max_tokens: Maximum tokens to generate (mapped to num_predict).

        Yields:
            Text chunks from the Ollama streaming response.

        Raises:
            LLMError: If Ollama is unreachable or returns an error.
        """
        payload: dict = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": 0.15,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/api/chat",
                    json=payload,
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if chunk := data.get("message", {}).get("content", ""):
                                yield chunk
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError as exc:
            raise LLMError(
                f"Ollama unreachable at {self._base_url}. Is `ollama serve` running?",
                detail=str(exc),
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise LLMError(f"Ollama returned HTTP {exc.response.status_code}", detail=str(exc)) from exc
        except Exception as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc

    async def is_available(self) -> bool:
        """Check if Ollama is running and the configured model is loaded.

        Returns:
            True if Ollama is reachable and the model is present.
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                resp.raise_for_status()
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                return any(self._model in m for m in models)
        except Exception:
            return False


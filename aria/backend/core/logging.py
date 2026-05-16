"""Structured JSON logger used by every Aria module.

Usage:
    from aria.backend.core.logging import get_logger
    log = get_logger(__name__)
    log.info("session started", session_id=session_id, lang=lang)
"""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from aria.backend.core.config import settings


def _configure_structlog() -> None:
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.DEBUG:
        # Human-readable output in development
        renderer: Any = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # JSON output in production — parseable by Fly.io / Datadog / Loki
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.LOG_LEVEL.upper())


_configure_structlog()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger for the given module name.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A structlog BoundLogger that emits JSON in production and
        coloured console output in debug mode.
    """
    return structlog.get_logger(name)


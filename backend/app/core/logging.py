"""
Structured logging configuration for Operator IQ.

Uses structlog for consistent, machine-parseable logs.
- Production (DEBUG=False): JSON output → ready for Datadog / ELK ingestion
- Development (DEBUG=True) : colorful human-readable console output

Usage:
    from app.core.logging import get_logger, audit_log

    logger = get_logger(__name__)
    logger.info("my_event", key="value")

    audit_log(user="OP-0042", action="UPDATE_SKILL", resource="skill/12")
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Any

import structlog

from app.core.config import settings


def _configure_structlog() -> None:
    """Set up structlog processors and renderer based on environment."""
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.DEBUG:
        # Human-readable for local development
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # JSON for production log aggregators
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.LOG_LEVEL.upper())

    # Quiet noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# Run configuration once at import time
_configure_structlog()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Return a structlog logger bound to *name*.

    Prefer this over ``logging.getLogger`` throughout the application.
    """
    return structlog.get_logger(name)


def audit_log(
    *,
    user: str,
    action: str,
    resource: str,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    Emit a structured audit event.

    Every mutation in the system should call this so that a complete
    trail exists for compliance (ISO 9001 / GDPR traceability).

    Args:
        user:     The actor's identifier (matricule or system).
        action:   Verb describing what happened (e.g. ``CREATE_OPERATOR``).
        resource: What was affected (e.g. ``operator/42``).
        extra:    Optional additional key/value pairs for context.
    """
    if not settings.AUDIT_LOG_ENABLED:
        return

    _audit_logger = get_logger("audit")
    _audit_logger.info(
        "audit_event",
        user=user,
        action=action,
        resource=resource,
        timestamp=datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    )

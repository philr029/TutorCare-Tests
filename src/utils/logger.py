"""Shared logger utility for the security-diagnostic toolkit.

Wraps the toolkit's RedactingFormatter so API keys, tokens, and passwords are
never written to log files or stdout.

Usage
-----
    from src.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Checking target: %s", target)
"""
from __future__ import annotations

import logging
from typing import Optional

# Re-use the production-grade redacting formatter from the core toolkit.
from security_toolkit.utils.logging_utils import RedactingFormatter


def get_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = "INFO",
) -> logging.Logger:
    """Return a named logger with sensitive-data redaction.

    Args:
        name:     Logger name – typically pass ``__name__``.
        log_file: Optional path to a log file; logs to stderr if omitted.
        level:    Logging level string (``"DEBUG"``, ``"INFO"``, etc.).

    Returns:
        A :class:`logging.Logger` instance.

    Example output::

        2024-01-15 10:30:00 [INFO] src.ip_reputation.check_rbl: Checking 8.8.8.8
    """
    # TODO: Extend to support structured / JSON logging for SIEM integration.
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        _fmt = RedactingFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(_fmt)
        logger.addHandler(stream_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(_fmt)
            logger.addHandler(file_handler)

    return logger

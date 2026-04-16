"""Logging utilities with sensitive data redaction."""
import logging
import re
from typing import Optional


_API_KEY_PATTERN = re.compile(
    r'(api[_-]?key|token|secret|password|Authorization)["\s:=]+([A-Za-z0-9\-_\.]{8,})',
    re.IGNORECASE,
)


class RedactingFormatter(logging.Formatter):
    """Log formatter that redacts sensitive data such as API keys."""

    REDACT_PLACEHOLDER = "[REDACTED]"

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        return _API_KEY_PATTERN.sub(r'\1 ' + self.REDACT_PLACEHOLDER, msg)


def get_logger(name: str, log_file: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    """Create and return a logger with sensitive-data redaction."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            RedactingFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                RedactingFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            )
            logger.addHandler(file_handler)

    return logger

"""Health and metrics routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from api.config import get_settings

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        generate_latest,
        Counter,
        Histogram,
        Info,
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])

if _PROMETHEUS_AVAILABLE:
    REQUEST_COUNT = Counter(
        "api_requests_total",
        "Total API requests",
        ["method", "endpoint", "status"],
    )
    REQUEST_LATENCY = Histogram(
        "api_request_duration_seconds",
        "API request latency",
        ["endpoint"],
    )
    APP_INFO = Info("api_info", "API service information")
    APP_INFO.info({"version": "1.0.0", "service": "security-toolkit-api"})


@router.get(
    "/health",
    summary="Health check",
    response_description="Service liveness status and optional API key availability.",
)
async def health_check() -> dict:
    """Return liveness status and which optional API keys are configured."""
    try:
        settings = get_settings()
        return {
            "status": "ok",
            "service": "security-toolkit-api",
            "abuseipdb_loaded": bool(settings.abuseipdb_key),
            "virustotal_loaded": bool(settings.virustotal_key),
            "numverify_loaded": bool(settings.numverify_key),
            "twilio_loaded": bool(settings.twilio_sid and settings.twilio_token),
        }
    except Exception as exc:  # pragma: no cover – belt-and-suspenders for unexpected errors
        logger.warning("health_check: unexpected error – %s", exc)
        return {"status": "ok", "service": "security-toolkit-api"}


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    response_class=PlainTextResponse,
    response_description="Prometheus-format metrics.",
    include_in_schema=False,
)
async def metrics() -> PlainTextResponse:
    """Expose Prometheus-format metrics."""
    if not _PROMETHEUS_AVAILABLE:
        return PlainTextResponse("# prometheus_client not installed\n", status_code=200)
    content = generate_latest()
    return PlainTextResponse(content, media_type=CONTENT_TYPE_LATEST)

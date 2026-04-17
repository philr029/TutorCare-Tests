"""Health and metrics routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

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
    response_description="Service liveness status.",
)
async def health_check() -> dict:
    """Return a simple liveness response."""
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

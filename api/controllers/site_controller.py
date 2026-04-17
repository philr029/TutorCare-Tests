"""Controller for site-health endpoint."""
from __future__ import annotations

import logging

from fastapi import HTTPException, status

from api.schemas.site_schemas import SiteHealthRequest, SiteHealthResponse
from api.services.site_service import site_health

logger = logging.getLogger(__name__)


async def handle_site_health(body: SiteHealthRequest) -> SiteHealthResponse:
    """Business logic for POST /site-health."""
    try:
        result = site_health(url=body.url, timeout=body.timeout)
        return SiteHealthResponse(**result)
    except Exception as exc:
        logger.exception("site-health failed for %s", body.url)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during site-health check: {exc}",
        ) from exc

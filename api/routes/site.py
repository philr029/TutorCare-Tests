"""Site-health routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.middleware.auth import verify_api_key
from api.middleware.rate_limit import limiter
from api.schemas.site_schemas import SiteHealthRequest, SiteHealthResponse
from api.controllers.site_controller import handle_site_health
from api.config import get_settings

router = APIRouter(tags=["Site Health"])


@router.post(
    "/site-health",
    response_model=SiteHealthResponse,
    summary="Run site-health diagnostics",
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit(get_settings().rate_limit_default)
async def site_health_endpoint(
    request: Request,
    body: SiteHealthRequest,
) -> SiteHealthResponse:
    """Run HTTP, SSL/TLS, and DNS diagnostics for a URL or hostname.

    - **url**: Full URL (e.g. `https://example.com`) or bare hostname.
    - **timeout**: Network timeout in seconds (1–60, default 10).
    """
    return await handle_site_health(body)

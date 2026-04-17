"""Domain reputation routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.middleware.auth import verify_api_key
from api.middleware.rate_limit import limiter
from api.schemas.domain_schemas import CheckDomainRequest, CheckDomainResponse
from api.controllers.domain_controller import handle_check_domain
from api.config import get_settings

router = APIRouter(tags=["Domain Reputation"])


@router.post(
    "/check-domain",
    response_model=CheckDomainResponse,
    summary="Check domain reputation",
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit(lambda: get_settings().rate_limit_default)
async def check_domain_endpoint(
    request: Request,
    body: CheckDomainRequest,
) -> CheckDomainResponse:
    """Check a domain name against IP-based DNSBLs and Spamhaus DBL.

    - **domain**: Domain to check (e.g. `example.com`).
    - **dnsbl_hosts**: Optional override for the DNSBL host list.
    """
    return await handle_check_domain(body)

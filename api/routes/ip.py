"""IP reputation routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from api.middleware.auth import verify_api_key
from api.middleware.rate_limit import limiter
from api.schemas.ip_schemas import CheckIPRequest, CheckIPResponse
from api.controllers.ip_controller import handle_check_ip
from api.config import get_settings
from fastapi import Request

router = APIRouter(tags=["IP Reputation"])


@router.post(
    "/check-ip",
    response_model=CheckIPResponse,
    summary="Check IP reputation",
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit(lambda: get_settings().rate_limit_default)
async def check_ip_endpoint(
    request: Request,  # required by SlowAPI
    body: CheckIPRequest,
) -> CheckIPResponse:
    """Check an IPv4 address against DNSBL blocklists and (optionally) AbuseIPDB.

    - **ip**: IPv4 address to check (required).
    - **dnsbl_zones**: Optional list of DNSBL zone hostnames; uses built-in list when omitted.
    """
    return await handle_check_ip(body)

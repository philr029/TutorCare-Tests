"""Controller for IP reputation endpoint."""
from __future__ import annotations

import logging

from fastapi import HTTPException, status

from api.config import get_settings
from api.schemas.ip_schemas import CheckIPRequest, CheckIPResponse
from api.services.ip_service import check_ip

logger = logging.getLogger(__name__)


async def handle_check_ip(body: CheckIPRequest) -> CheckIPResponse:
    """Business logic for POST /check-ip."""
    settings = get_settings()
    module_config = settings.build_module_config()

    try:
        result = check_ip(
            ip=body.ip,
            dnsbl_zones=body.dnsbl_zones,
            module_config=module_config,
        )
        return CheckIPResponse(**result)
    except Exception as exc:
        logger.exception("check-ip failed for %s", body.ip)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during IP check: {exc}",
        ) from exc

"""Controller for domain reputation endpoint."""
from __future__ import annotations

import logging

from fastapi import HTTPException, status

from api.config import get_settings
from api.schemas.domain_schemas import CheckDomainRequest, CheckDomainResponse
from api.services.domain_service import check_domain

logger = logging.getLogger(__name__)


async def handle_check_domain(body: CheckDomainRequest) -> CheckDomainResponse:
    """Business logic for POST /check-domain."""
    settings = get_settings()
    module_config = settings.build_module_config()

    try:
        result = check_domain(
            domain=body.domain,
            dnsbl_hosts=body.dnsbl_hosts,
            module_config=module_config,
        )
        return CheckDomainResponse(**result)
    except Exception as exc:
        logger.exception("check-domain failed for %s", body.domain)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during domain check: {exc}",
        ) from exc

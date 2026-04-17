"""Controller for phone validation endpoint."""
from __future__ import annotations

import logging

from fastapi import HTTPException, status

from api.config import get_settings
from api.schemas.phone_schemas import ValidatePhoneRequest, ValidatePhoneResponse
from api.services.phone_service import validate_phone

logger = logging.getLogger(__name__)


async def handle_validate_phone(body: ValidatePhoneRequest) -> ValidatePhoneResponse:
    """Business logic for POST /validate-phone."""
    settings = get_settings()
    module_config = settings.build_module_config()

    try:
        result = validate_phone(
            phone=body.phone,
            region=body.region,
            module_config=module_config,
        )
        return ValidatePhoneResponse(**result)
    except Exception as exc:
        logger.exception("validate-phone failed for %s", body.phone)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during phone validation: {exc}",
        ) from exc

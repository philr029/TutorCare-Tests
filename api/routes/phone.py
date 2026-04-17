"""Phone validation routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.middleware.auth import verify_api_key
from api.middleware.rate_limit import limiter
from api.schemas.phone_schemas import ValidatePhoneRequest, ValidatePhoneResponse
from api.controllers.phone_controller import handle_validate_phone
from api.config import get_settings

router = APIRouter(tags=["Phone Validation"])


@router.post(
    "/validate-phone",
    response_model=ValidatePhoneResponse,
    summary="Validate a phone number",
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit(lambda: get_settings().rate_limit_default)
async def validate_phone_endpoint(
    request: Request,
    body: ValidatePhoneRequest,
) -> ValidatePhoneResponse:
    """Parse and validate a phone number using Google's libphonenumber.

    - **phone**: Phone number string (e.g. `+14155552671`).
    - **region**: Optional ISO 3166-1 alpha-2 region hint (e.g. `US`, `GB`).

    No network calls are made unless Numverify or Twilio API keys are configured.
    """
    return await handle_validate_phone(body)

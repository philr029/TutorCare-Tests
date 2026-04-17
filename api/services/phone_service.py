"""Service wrapper for phone number validation."""
from __future__ import annotations

from typing import Any, Dict, Optional

from src.phone_validation.validate_number import validate_number


def validate_phone(
    phone: str,
    region: Optional[str] = None,
    module_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate a phone number and return enriched result.

    Args:
        phone:         Phone number string.
        region:        ISO 3166-1 alpha-2 region hint.
        module_config: Config dict forwarded to validate_number.

    Returns:
        Full validation result dict from ``validate_number``.
    """
    return validate_number(phone, region=region, config=module_config or {})

"""API key authentication middleware.

Validates the ``X-API-Key`` header against the configured key list.
Authentication is skipped when ``AUTH_DISABLED=true`` or no keys are configured.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from api.config import get_settings

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(_API_KEY_HEADER)) -> None:
    """FastAPI dependency that enforces API key authentication.

    Raises:
        HTTPException 401: when authentication is required but no key provided.
        HTTPException 403: when the provided key is invalid.
    """
    settings = get_settings()

    if settings.auth_disabled:
        return

    valid_keys = settings.get_api_key_list()
    if not valid_keys:
        return

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

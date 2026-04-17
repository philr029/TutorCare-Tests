"""Pydantic schemas for site-health endpoints."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

_URL_RE = re.compile(r"^https?://[^\s]+$|^[a-zA-Z0-9][a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$")


class SiteHealthRequest(BaseModel):
    """Request body for POST /site-health."""

    url: str = Field(
        ...,
        description="Full URL (e.g. 'https://example.com') or bare hostname.",
    )
    timeout: int = Field(
        default=10,
        ge=1,
        le=60,
        description="HTTP/SSL/DNS timeout in seconds (1–60).",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not _URL_RE.match(v):
            raise ValueError(
                f"Invalid URL or hostname: '{v}'. "
                "Provide a full URL (https://example.com) or a bare hostname."
            )
        return v


class SiteHealthResponse(BaseModel):
    """Response body for POST /site-health."""

    hostname: str
    http: Dict[str, Any]
    ssl: Dict[str, Any]
    dns: Dict[str, Any]
    checked_at: str
    error: Optional[str] = None

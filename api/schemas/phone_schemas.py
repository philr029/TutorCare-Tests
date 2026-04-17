"""Pydantic schemas for phone validation endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ValidatePhoneRequest(BaseModel):
    """Request body for POST /validate-phone."""

    phone: str = Field(..., description="Phone number string (e.g. '+14155552671').")
    region: Optional[str] = Field(
        default=None,
        description="ISO 3166-1 alpha-2 region hint (e.g. 'US', 'GB'). "
        "Required for numbers without a leading country code.",
    )

    @field_validator("phone")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("phone must not be empty.")
        return v

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if len(v) != 2 or not v.isalpha():
            raise ValueError("region must be a 2-letter ISO 3166-1 alpha-2 code.")
        return v


class ValidatePhoneResponse(BaseModel):
    """Response body for POST /validate-phone."""

    input: str
    valid: bool
    possible: bool
    format: Optional[Dict[str, str]]
    country: Optional[str]
    region: Optional[str]
    carrier: Optional[str]
    line_type: Optional[str]
    timezones: Optional[List[str]]
    sources: List[Dict[str, Any]]
    error: Optional[str]

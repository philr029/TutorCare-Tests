"""Pydantic schemas for domain reputation endpoints."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

_DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)


class CheckDomainRequest(BaseModel):
    """Request body for POST /check-domain."""

    domain: str = Field(..., description="Domain name to check (e.g. 'example.com').")
    dnsbl_hosts: Optional[List[str]] = Field(
        default=None,
        description="Optional IP-based DNSBL hostnames. Uses built-in list when omitted.",
    )

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if not _DOMAIN_RE.match(v):
            raise ValueError(f"Invalid domain name: '{v}'")
        return v


class CheckDomainResponse(BaseModel):
    """Response body for POST /check-domain."""

    domain: str
    resolved_ips: List[str]
    listed: bool
    sources: List[Dict[str, Any]]
    error: Optional[str] = None

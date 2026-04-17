"""Pydantic schemas for IP reputation endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator
import ipaddress


class CheckIPRequest(BaseModel):
    """Request body for POST /check-ip."""

    ip: str = Field(..., description="IPv4 address to check against DNSBLs.")
    dnsbl_zones: Optional[List[str]] = Field(
        default=None,
        description="Optional list of DNSBL zone hostnames. Uses built-in list when omitted.",
    )

    @field_validator("ip")
    @classmethod
    def validate_ipv4(cls, v: str) -> str:
        v = v.strip()
        try:
            addr = ipaddress.ip_address(v)
            if addr.version != 4:
                raise ValueError("Only IPv4 addresses are supported.")
        except ValueError as exc:
            raise ValueError(f"Invalid IPv4 address '{v}': {exc}") from exc
        return v


class DNSBLResult(BaseModel):
    """Single DNSBL zone result."""

    ip: str
    dnsbl: str
    listed: bool
    details: str


class CheckIPResponse(BaseModel):
    """Response body for POST /check-ip."""

    ip: str
    dnsbl_results: List[Dict[str, Any]]
    abuseipdb: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

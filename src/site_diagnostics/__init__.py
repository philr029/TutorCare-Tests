"""Site diagnostics sub-package."""
from __future__ import annotations

from typing import Any, Dict
from urllib.parse import urlparse

from .http_status import check_http_status
from .ssl_check import check_ssl
from .dns_records import query_dns_records


def get_http_status(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Fetch a URL and return HTTP status, headers, redirect chain, and timing.

    Convenience wrapper around :func:`check_http_status`.

    Args:
        url:     Target URL or bare hostname.
        timeout: Request timeout in seconds.

    Returns:
        Structured dict with keys ``url``, ``final_url``, ``status_code``,
        ``redirect_chain``, ``headers``, ``page_load_ms``, and ``error``.
    """
    return check_http_status(url, timeout)


def get_ssl_info(url: str, port: int = 443, timeout: int = 10) -> Dict[str, Any]:
    """Inspect the SSL/TLS certificate for the hostname in *url*.

    Extracts the hostname from *url* (or treats the argument as a bare
    hostname when no scheme is present) and delegates to :func:`check_ssl`.

    Args:
        url:     Full URL (``https://example.com``) or bare hostname.
        port:    TLS port override (default ``443``).
        timeout: Socket connection timeout in seconds.

    Returns:
        Structured dict with keys ``hostname``, ``port``, ``valid``,
        ``subject``, ``issuer``, ``not_before``, ``not_after``,
        ``days_until_expiry``, and ``error``.
    """
    if url.startswith(("http://", "https://")):
        parsed = urlparse(url)
        hostname = parsed.hostname or url
        port = parsed.port or port
    else:
        hostname = url
    return check_ssl(hostname, port, timeout)


def get_dns_records(domain: str) -> Dict[str, Any]:
    """Query A, MX, TXT, SPF, and DMARC records for a domain.

    Convenience wrapper around :func:`query_dns_records`.

    Args:
        domain: Domain name to query (e.g. ``"example.com"``).

    Returns:
        Structured dict with keys ``domain``, ``A``, ``MX``, ``TXT``,
        ``SPF``, ``DMARC``, and ``DKIM_hint``.
    """
    return query_dns_records(domain)

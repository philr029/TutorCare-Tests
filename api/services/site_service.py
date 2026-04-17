"""Service wrapper for site-health diagnostics."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import urlparse

from src.site_diagnostics.http_status import check_http_status
from src.site_diagnostics.ssl_check import check_ssl
from src.site_diagnostics.dns_records import query_dns_records


def _extract_hostname(url: str) -> str:
    """Extract hostname from a URL or return the input if it is already a hostname."""
    if url.startswith(("http://", "https://")):
        parsed = urlparse(url)
        return parsed.hostname or url
    return url


def site_health(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Run HTTP, SSL, and DNS diagnostics for a URL or hostname.

    Args:
        url:     Full URL or bare hostname.
        timeout: Timeout in seconds for all network operations.

    Returns:
        Dict with ``hostname``, ``http``, ``ssl``, ``dns``, and ``checked_at`` keys.
    """
    hostname = _extract_hostname(url)

    http_result = check_http_status(url, timeout=timeout)
    ssl_result = check_ssl(hostname, port=443, timeout=timeout)
    dns_result = query_dns_records(hostname)

    return {
        "hostname": hostname,
        "http": http_result,
        "ssl": ssl_result,
        "dns": dns_result,
        "checked_at": datetime.now(tz=timezone.utc).isoformat(),
    }

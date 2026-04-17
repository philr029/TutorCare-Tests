"""Domain reputation sub-package."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .check_dnsbl import check_domain_dnsbl


def check_dnsbl(domain: str, dnsbl_hosts: Optional[List[str]] = None) -> Dict[str, Any]:
    """Check a domain name against IP-based DNSBLs and Spamhaus DBL.

    Convenience wrapper around :func:`check_domain_dnsbl`.

    Args:
        domain:      Domain to check (e.g. ``"example.com"``).
        dnsbl_hosts: Optional list of IP-based DNSBL hostnames to query.
                     Defaults to ``["zen.spamhaus.org", "multi.surbl.org"]``.

    Returns:
        Dictionary with keys ``domain``, ``resolved_ips``, ``listed``,
        and ``sources``.  See :func:`check_domain_dnsbl` for the full schema.

    Example::

        from src.domain_reputation import check_dnsbl

        result = check_dnsbl("example.com")
        print(result["listed"])   # False
    """
    return check_domain_dnsbl(domain, dnsbl_hosts)

"""Service wrapper for domain reputation checks."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.domain_reputation.check_dnsbl import check_domain_dnsbl


def check_domain(
    domain: str,
    dnsbl_hosts: Optional[List[str]] = None,
    module_config: Optional[Dict[str, Any]] = None,  # noqa: ARG001
) -> Dict[str, Any]:
    """Run DNSBL checks for a domain name.

    Args:
        domain:       Domain to check.
        dnsbl_hosts:  Override DNSBL host list.
        module_config: Reserved for future use.

    Returns:
        Dict with ``domain``, ``resolved_ips``, ``listed``, and ``sources`` keys.
    """
    return check_domain_dnsbl(domain, dnsbl_hosts)

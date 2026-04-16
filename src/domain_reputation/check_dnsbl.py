"""DNS-based block list (DNSBL) check for domain names.

Resolves a domain to its A records and then queries each configured DNSBL
for every resolved IP.  Also checks Spamhaus DBL (Domain Block List) directly
against the domain name without IP resolution.

Usage
-----
    from src.domain_reputation.check_dnsbl import check_domain_dnsbl

    result = check_domain_dnsbl(
        domain="example.com",
        dnsbl_hosts=["zen.spamhaus.org", "multi.surbl.org"],
    )
    print(result)
    # {
    #   "domain": "example.com",
    #   "resolved_ips": ["93.184.216.34"],
    #   "listed": false,
    #   "sources": [...]
    # }
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import dns.exception
import dns.resolver

from src.utils.logger import get_logger

logger = get_logger(__name__)

_SPAMHAUS_DBL = "dbl.spamhaus.org"


def _resolve_domain(domain: str) -> List[str]:
    """Resolve a domain name to its A record IPs.

    Returns an empty list if the domain cannot be resolved.
    """
    # TODO: Add AAAA (IPv6) record resolution.
    try:
        answers = dns.resolver.resolve(domain, "A")
        ips = [str(r) for r in answers]
        logger.debug("Resolved %s -> %s", domain, ips)
        return ips
    except Exception as exc:
        logger.warning("Could not resolve domain %s: %s", domain, exc)
        return []


def _check_ip_in_dnsbl(ip: str, dnsbl_host: str) -> Dict[str, Any]:
    """Check a single IP against a single DNSBL (reversed-IP method)."""
    reversed_ip = ".".join(reversed(ip.split(".")))
    query = f"{reversed_ip}.{dnsbl_host}"
    try:
        dns.resolver.resolve(query, "A")
        return {"listed": True, "details": f"IP {ip} listed in {dnsbl_host}"}
    except dns.resolver.NXDOMAIN:
        return {"listed": False, "details": "Not listed"}
    except dns.resolver.NoNameservers:
        return {"listed": None, "details": "DNS lookup failed (no nameservers)"}
    except dns.exception.Timeout:
        return {"listed": None, "details": "DNS lookup timed out"}
    except Exception as exc:  # pragma: no cover
        logger.error("DNSBL error %s / %s: %s", ip, dnsbl_host, exc)
        return {"listed": None, "details": f"Error: {exc}"}


def _check_domain_in_dbl(domain: str) -> Dict[str, Any]:
    """Check a domain directly against Spamhaus DBL."""
    # TODO: Support additional domain-based blocklists (e.g. URIBL, SURBL).
    query = f"{domain}.{_SPAMHAUS_DBL}"
    logger.debug("DBL query: %s", query)
    try:
        dns.resolver.resolve(query, "A")
        return {
            "name": "Spamhaus DBL",
            "status": "listed",
            "details": f"Domain listed in {_SPAMHAUS_DBL}",
        }
    except dns.resolver.NXDOMAIN:
        return {"name": "Spamhaus DBL", "status": "clean", "details": "Not listed"}
    except dns.exception.Timeout:
        return {"name": "Spamhaus DBL", "status": "unknown", "details": "Timeout"}
    except Exception as exc:  # pragma: no cover
        return {"name": "Spamhaus DBL", "status": "unknown", "details": f"Error: {exc}"}


def check_domain_dnsbl(
    domain: str,
    dnsbl_hosts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Check a domain name against IP-based DNSBLs and Spamhaus DBL.

    Args:
        domain:      Domain to check (e.g. ``"example.com"``).
        dnsbl_hosts: IP-based DNSBL hostnames to query.  Defaults to
                     ``["zen.spamhaus.org", "multi.surbl.org"]``.

    Returns:
        Dictionary with keys:

        - ``domain`` (*str*) – the input domain.
        - ``resolved_ips`` (*list[str]*) – IPs the domain resolved to.
        - ``listed`` (*bool*) – ``True`` if listed in any source.
        - ``sources`` (*list[dict]*) – per-source result dicts.

    Example output::

        {
          "domain": "example.com",
          "resolved_ips": ["93.184.216.34"],
          "listed": false,
          "sources": [
            {"name": "Spamhaus DBL", "status": "clean", "details": "Not listed"},
            {"name": "zen.spamhaus.org (93.184.216.34)", "status": "clean", "details": "Not listed"}
          ]
        }
    """
    if dnsbl_hosts is None:
        dnsbl_hosts = ["zen.spamhaus.org", "multi.surbl.org"]

    logger.info("Checking domain DNSBL reputation for %s", domain)

    sources: List[Dict[str, Any]] = []
    overall_listed = False

    # 1. Spamhaus DBL – direct domain check.
    dbl_result = _check_domain_in_dbl(domain)
    sources.append(dbl_result)
    if dbl_result.get("status") == "listed":
        overall_listed = True

    # 2. Resolve domain and check each IP against IP-based DNSBLs.
    resolved_ips = _resolve_domain(domain)
    for ip in resolved_ips:
        for host in dnsbl_hosts:
            check = _check_ip_in_dnsbl(ip, host)
            status = (
                "listed" if check["listed"] else
                "unknown" if check["listed"] is None else
                "clean"
            )
            sources.append({
                "name": f"{host} ({ip})",
                "status": status,
                "details": check["details"],
            })
            if check["listed"]:
                overall_listed = True

    return {
        "domain": domain,
        "resolved_ips": resolved_ips,
        "listed": overall_listed,
        "sources": sources,
    }

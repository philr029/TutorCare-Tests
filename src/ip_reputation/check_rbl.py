"""Real-time Block List (RBL / DNSBL) check for IPv4 addresses.

Queries one or more DNS-based block lists by reversing the IP octets and
appending the DNSBL host (e.g. ``4.3.2.1.zen.spamhaus.org``).  An ``A``
record in the response means the IP is listed.

Usage
-----
    from src.ip_reputation.check_rbl import check_rbl, check_rbl_multi

    # Single DNSBL
    result = check_rbl("1.2.3.4", "zen.spamhaus.org")
    print(result)
    # {"ip": "1.2.3.4", "dnsbl": "zen.spamhaus.org", "listed": True, "details": "Listed in zen.spamhaus.org"}

    # Multiple DNSBLs
    results = check_rbl_multi("8.8.8.8", ["zen.spamhaus.org", "multi.surbl.org"])
"""
from __future__ import annotations

from typing import Any, Dict, List

import dns.exception
import dns.resolver

from src.utils.logger import get_logger

logger = get_logger(__name__)


def _reverse_ip(ip: str) -> str:
    """Reverse the octets of an IPv4 address for DNSBL lookup.

    Example::

        _reverse_ip("1.2.3.4")  # "4.3.2.1"
    """
    # TODO: Add IPv6 nibble-reversal support.
    return ".".join(reversed(ip.split(".")))


def check_rbl(ip: str, dnsbl_host: str) -> Dict[str, Any]:
    """Query a single DNSBL for an IPv4 address.

    Args:
        ip:         IPv4 address to check (e.g. ``"1.2.3.4"``).
        dnsbl_host: DNSBL hostname (e.g. ``"zen.spamhaus.org"``).

    Returns:
        Dictionary with keys:

        - ``ip`` (*str*) – the queried IP.
        - ``dnsbl`` (*str*) – the DNSBL that was queried.
        - ``listed`` (*bool | None*) – ``True`` if listed, ``False`` if clean,
          ``None`` if the check could not be completed.
        - ``details`` (*str*) – human-readable description.

    Example output (listed)::

        {
          "ip": "1.2.3.4",
          "dnsbl": "zen.spamhaus.org",
          "listed": true,
          "details": "Listed in zen.spamhaus.org"
        }

    Example output (clean)::

        {
          "ip": "8.8.8.8",
          "dnsbl": "zen.spamhaus.org",
          "listed": false,
          "details": "Not listed"
        }
    """
    # TODO: Validate that ``ip`` is a well-formed IPv4 address before querying.
    reversed_ip = _reverse_ip(ip)
    query = f"{reversed_ip}.{dnsbl_host}"
    logger.debug("DNSBL query: %s", query)

    try:
        dns.resolver.resolve(query, "A")
        logger.info("IP %s is LISTED in %s", ip, dnsbl_host)
        return {
            "ip": ip,
            "dnsbl": dnsbl_host,
            "listed": True,
            "details": f"Listed in {dnsbl_host}",
        }
    except dns.resolver.NXDOMAIN:
        return {
            "ip": ip,
            "dnsbl": dnsbl_host,
            "listed": False,
            "details": "Not listed",
        }
    except dns.resolver.NoNameservers:
        logger.warning("No nameservers available for DNSBL %s", dnsbl_host)
        return {
            "ip": ip,
            "dnsbl": dnsbl_host,
            "listed": None,
            "details": "DNS lookup failed (no nameservers)",
        }
    except dns.exception.Timeout:
        logger.warning("DNSBL query timed out for %s at %s", ip, dnsbl_host)
        return {
            "ip": ip,
            "dnsbl": dnsbl_host,
            "listed": None,
            "details": "DNS lookup timed out",
        }
    except Exception as exc:  # pragma: no cover
        logger.error("Unexpected DNSBL error for %s at %s: %s", ip, dnsbl_host, exc)
        return {
            "ip": ip,
            "dnsbl": dnsbl_host,
            "listed": None,
            "details": f"Error: {exc}",
        }


def check_rbl_multi(ip: str, dnsbl_hosts: List[str]) -> List[Dict[str, Any]]:
    """Query multiple DNSBLs for a single IPv4 address.

    Args:
        ip:          IPv4 address to check.
        dnsbl_hosts: List of DNSBL hostnames to query.

    Returns:
        List of result dicts (one per DNSBL), same schema as :func:`check_rbl`.

    Example::

        results = check_rbl_multi("1.2.3.4", ["zen.spamhaus.org", "bl.spamcop.net"])
        listed_in = [r["dnsbl"] for r in results if r["listed"]]
    """
    # TODO: Add async/concurrent DNS resolution to reduce total latency.
    return [check_rbl(ip, host) for host in dnsbl_hosts]

"""IP reputation sub-package."""
from __future__ import annotations

from typing import Any, Dict, List

from .check_rbl import check_rbl_multi, COMMON_DNSBL_ZONES


def check_rbl(ip: str) -> List[Dict[str, Any]]:
    """Query all built-in DNSBL zones for an IPv4 address.

    Convenience wrapper around :func:`check_rbl_multi` that uses the
    :data:`COMMON_DNSBL_ZONES` list so callers don't need to manage zone lists.

    Args:
        ip: IPv4 address to check (e.g. ``"1.2.3.4"``).

    Returns:
        List of result dicts – one per zone – with keys ``ip``, ``dnsbl``,
        ``listed``, and ``details``.

    Example::

        from src.ip_reputation import check_rbl

        results = check_rbl("8.8.8.8")
        listed_in = [r["dnsbl"] for r in results if r["listed"]]
    """
    return check_rbl_multi(ip, COMMON_DNSBL_ZONES)

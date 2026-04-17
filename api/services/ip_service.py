"""Service wrapper for IP reputation checks."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.ip_reputation.check_rbl import check_rbl_multi, COMMON_DNSBL_ZONES
from src.ip_reputation.check_abuseipdb import check_abuseipdb


def check_ip(
    ip: str,
    dnsbl_zones: Optional[List[str]] = None,
    module_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run DNSBL checks (and optionally AbuseIPDB) for an IPv4 address.

    Args:
        ip:           IPv4 address.
        dnsbl_zones:  Override DNSBL zone list.  ``None`` uses the built-in list.
        module_config: Config dict forwarded to AbuseIPDB helper.

    Returns:
        Dict with ``ip``, ``dnsbl_results``, and ``abuseipdb`` keys.
    """
    zones = dnsbl_zones or COMMON_DNSBL_ZONES
    dnsbl_results = check_rbl_multi(ip, zones)

    abuseipdb_result: Optional[Dict[str, Any]] = None
    api_key = (module_config or {}).get("api_keys", {}).get("abuseipdb", "")
    if api_key:
        timeout = (module_config or {}).get("settings", {}).get("timeout", 10)
        abuseipdb_result = check_abuseipdb(ip, api_key, timeout)

    return {
        "ip": ip,
        "dnsbl_results": dnsbl_results,
        "abuseipdb": abuseipdb_result,
    }

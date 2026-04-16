"""AbuseIPDB reputation check for IPv4/IPv6 addresses.

Queries the AbuseIPDB v2 API (https://www.abuseipdb.com/) for the abuse
confidence score and recent report history of an IP address.

Requires a free or paid AbuseIPDB API key configured in ``config.json``.

Usage
-----
    from src.ip_reputation.check_abuseipdb import check_abuseipdb

    result = check_abuseipdb(
        ip="1.2.3.4",
        api_key="YOUR_ABUSEIPDB_KEY",
        timeout=10,
    )
    print(result)
    # {
    #   "ip": "1.2.3.4",
    #   "source": "AbuseIPDB",
    #   "listed": true,
    #   "abuse_confidence_score": 87,
    #   "country": "CN",
    #   "isp": "Some ISP",
    #   "total_reports": 42,
    #   "error": null
    # }
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from src.utils.logger import get_logger

logger = get_logger(__name__)

_ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"
_MAX_AGE_DAYS = 90


def check_abuseipdb(
    ip: str,
    api_key: str,
    timeout: int = 10,
    max_age_days: int = _MAX_AGE_DAYS,
) -> Dict[str, Any]:
    """Query AbuseIPDB for the reputation of an IP address.

    Args:
        ip:           IPv4 or IPv6 address to look up.
        api_key:      AbuseIPDB API key (obtain at https://www.abuseipdb.com/).
        timeout:      HTTP request timeout in seconds.
        max_age_days: Only consider reports younger than this many days
                      (AbuseIPDB default is 90).

    Returns:
        Dictionary with keys:

        - ``ip`` (*str*) – the queried IP.
        - ``source`` (*str*) – always ``"AbuseIPDB"``.
        - ``listed`` (*bool | None*) – ``True`` if ``abuse_confidence_score > 0``.
        - ``abuse_confidence_score`` (*int | None*) – 0–100 confidence score.
        - ``country`` (*str | None*) – two-letter country code.
        - ``isp`` (*str | None*) – ISP or organisation name.
        - ``total_reports`` (*int*) – number of abuse reports in the window.
        - ``error`` (*str | None*) – error message, or ``None`` on success.

    Example output (malicious IP)::

        {
          "ip": "1.2.3.4",
          "source": "AbuseIPDB",
          "listed": true,
          "abuse_confidence_score": 87,
          "country": "CN",
          "isp": "Some Hosting Ltd",
          "total_reports": 42,
          "error": null
        }

    Example output (clean IP)::

        {
          "ip": "8.8.8.8",
          "source": "AbuseIPDB",
          "listed": false,
          "abuse_confidence_score": 0,
          "country": "US",
          "isp": "Google LLC",
          "total_reports": 0,
          "error": null
        }
    """
    # TODO: Accept a list of IPs and use the AbuseIPDB bulk-check endpoint.
    # TODO: Cache results to avoid re-querying the same IP within a session.
    if not api_key:
        logger.warning("AbuseIPDB API key not configured – skipping enrichment.")
        return _error_result(ip, "API key not configured")

    headers = {"Key": api_key, "Accept": "application/json"}
    params: Dict[str, Any] = {"ipAddress": ip, "maxAgeInDays": max_age_days}

    logger.debug("Querying AbuseIPDB for %s", ip)
    try:
        resp = requests.get(
            _ABUSEIPDB_URL,
            headers=headers,
            params=params,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        score: int = data.get("abuseConfidenceScore", 0)

        result: Dict[str, Any] = {
            "ip": ip,
            "source": "AbuseIPDB",
            "listed": score > 0,
            "abuse_confidence_score": score,
            "country": data.get("countryCode"),
            "isp": data.get("isp"),
            "total_reports": data.get("totalReports", 0),
            "error": None,
        }
        logger.info(
            "AbuseIPDB result for %s: score=%s listed=%s",
            ip,
            score,
            result["listed"],
        )
        return result

    except requests.HTTPError as exc:
        logger.warning("AbuseIPDB HTTP error for %s: %s", ip, exc)
        return _error_result(ip, f"HTTP error: {exc}")
    except requests.RequestException as exc:
        logger.warning("AbuseIPDB request failed for %s: %s", ip, exc)
        return _error_result(ip, f"Request error: {exc}")


def _error_result(ip: str, message: str) -> Dict[str, Any]:
    """Build a uniform error-result dict."""
    return {
        "ip": ip,
        "source": "AbuseIPDB",
        "listed": None,
        "abuse_confidence_score": None,
        "country": None,
        "isp": None,
        "total_reports": 0,
        "error": message,
    }

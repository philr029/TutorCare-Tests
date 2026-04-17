"""Helper to query multirbl.valli.org via HTML scraping.

Parses the multi-DNSBL results page at https://multirbl.valli.org/lookup/ for a
given IPv4 address using :mod:`requests` and :mod:`bs4` (BeautifulSoup).

Usage
-----
    from src.ip_reputation.multirbl import query_multirbl

    result = query_multirbl("1.2.3.4")
    print(result["listed"])   # True/False/None
    print(result["sources"])  # list of per-zone dicts
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from src.utils.logger import get_logger

logger = get_logger(__name__)

_MULTIRBL_URL = "https://multirbl.valli.org/lookup/{ip}.html"
_DEFAULT_TIMEOUT = 15
_USER_AGENT = (
    "SecurityToolkit/1.0 (health-check; +https://github.com/your-org/security-toolkit)"
)


def query_multirbl(ip: str, timeout: int = _DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Fetch and parse the multirbl.valli.org results page for an IP address.

    Makes a single HTTP GET to ``https://multirbl.valli.org/lookup/<ip>.html``
    and extracts the per-zone listed/clean status from the HTML table.

    Args:
        ip:      IPv4 address to check (e.g. ``"1.2.3.4"``).
        timeout: HTTP request timeout in seconds.

    Returns:
        Dictionary with keys:

        - ``ip`` (*str*) – the queried IP.
        - ``source`` (*str*) – always ``"multirbl.valli.org"``.
        - ``listed`` (*bool | None*) – ``True`` if listed in any zone,
          ``False`` if all zones returned clean, ``None`` on error.
        - ``listed_count`` (*int*) – number of zones where the IP is listed.
        - ``clean_count`` (*int*) – number of zones that returned clean.
        - ``sources`` (*list[dict]*) – per-zone result dicts with keys
          ``zone``, ``status`` (``"listed"`` | ``"clean"`` | ``"unknown"``).
        - ``error`` (*str | None*) – error message, or ``None`` on success.

    Example output::

        {
          "ip": "8.8.8.8",
          "source": "multirbl.valli.org",
          "listed": false,
          "listed_count": 0,
          "clean_count": 84,
          "sources": [
            {"zone": "zen.spamhaus.org", "status": "clean"},
            ...
          ],
          "error": null
        }
    """
    result: Dict[str, Any] = {
        "ip": ip,
        "source": "multirbl.valli.org",
        "listed": None,
        "listed_count": 0,
        "clean_count": 0,
        "sources": [],
        "error": None,
    }

    url = _MULTIRBL_URL.format(ip=ip)
    logger.info("Querying multirbl.valli.org for %s", ip)

    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": _USER_AGENT},
        )
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        result["error"] = "Request timed out"
        logger.warning("multirbl.valli.org timed out for %s", ip)
        return result
    except requests.exceptions.ConnectionError as exc:
        result["error"] = f"Connection error: {exc}"
        logger.warning("multirbl.valli.org connection error for %s: %s", ip, exc)
        return result
    except requests.RequestException as exc:
        result["error"] = f"Request error: {exc}"
        logger.warning("multirbl.valli.org request failed for %s: %s", ip, exc)
        return result

    sources = _parse_multirbl_html(resp.text)
    result["sources"] = sources

    listed_count = sum(1 for s in sources if s["status"] == "listed")
    clean_count = sum(1 for s in sources if s["status"] == "clean")
    result["listed_count"] = listed_count
    result["clean_count"] = clean_count
    result["listed"] = listed_count > 0 if sources else None

    logger.info(
        "multirbl.valli.org result for %s: listed=%s (%d/%d zones)",
        ip,
        result["listed"],
        listed_count,
        len(sources),
    )
    return result


def _parse_multirbl_html(html: str) -> List[Dict[str, Any]]:
    """Parse the multirbl.valli.org results table and return per-zone dicts.

    Args:
        html: Raw HTML content from a multirbl.valli.org lookup page.

    Returns:
        List of ``{"zone": ..., "status": "listed"|"clean"|"unknown"}`` dicts.
    """
    soup = BeautifulSoup(html, "html.parser")
    sources: List[Dict[str, Any]] = []

    # The results table has rows with a CSS class indicating the listing status.
    # Typical class names are "positive" (listed) and "negative" (clean).
    table = soup.find("table", id="dnsbl_results")
    if table is None:
        # Fall back to the first table if the specific ID is absent.
        table = soup.find("table")

    if table is None:
        logger.debug("multirbl: no results table found in HTML")
        return sources

    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue

        zone_cell = cells[0]
        status_cell = cells[-1]

        zone = zone_cell.get_text(strip=True)
        if not zone or zone.lower() in ("zone", "dnsbl", "rbl", "list"):
            continue  # skip header rows

        raw_status = status_cell.get_text(strip=True).lower()
        row_class = " ".join(row.get("class", []))

        if "positive" in row_class or (
            "listed" in raw_status and "not listed" not in raw_status
        ):
            status = "listed"
        elif "negative" in row_class or "not listed" in raw_status or raw_status == "ok":
            status = "clean"
        else:
            status = "unknown"

        sources.append({"zone": zone, "status": status})

    return sources

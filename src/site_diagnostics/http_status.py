"""HTTP status and response-header diagnostics for a target URL.

Performs a single HTTP GET request with a clearly identified ``User-Agent``
and reports the status code, response headers, redirect chain, and page-load
time.  Designed to be non-intrusive: only standard GET requests, no crawling.

Usage
-----
    from src.site_diagnostics.http_status import check_http_status

    result = check_http_status("https://example.com")
    print(result["status_code"])   # 200
    print(result["page_load_ms"])  # 342.5
"""
from __future__ import annotations

import time
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
from requests.exceptions import ConnectionError, SSLError, Timeout

from src.utils.logger import get_logger

logger = get_logger(__name__)

_USER_AGENT = "SecurityToolkit/1.0 (health-check; +https://github.com/your-org/security-toolkit)"


def _ensure_scheme(url: str) -> str:
    """Prepend ``https://`` if no scheme is present."""
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def check_http_status(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Fetch a URL and report its HTTP status, headers, redirects, and timing.

    Args:
        url:     Target URL or bare hostname (scheme is added if missing).
        timeout: Request timeout in seconds.

    Returns:
        Dictionary with keys:

        - ``url`` – the normalised request URL.
        - ``final_url`` – URL after following any redirects.
        - ``status_code`` (*int | None*) – HTTP response status.
        - ``redirect_chain`` – list of ``{"url": …, "status_code": …}`` dicts.
        - ``headers`` – response headers dict.
        - ``page_load_ms`` (*float | None*) – total request time in milliseconds.
        - ``error`` (*str | None*) – error message, or ``null`` on success.

    Example output (success)::

        {
          "url": "https://example.com",
          "final_url": "https://example.com/",
          "status_code": 200,
          "redirect_chain": [],
          "headers": {"Content-Type": "text/html; charset=UTF-8", ...},
          "page_load_ms": 342.5,
          "error": null
        }

    Example output (redirect)::

        {
          "url": "http://example.com",
          "final_url": "https://example.com/",
          "status_code": 200,
          "redirect_chain": [{"url": "http://example.com", "status_code": 301}],
          "page_load_ms": 410.2,
          "error": null
        }
    """
    # TODO: Add HEAD-request mode for faster checks when full content isn't needed.
    # TODO: Detect and report HSTS header presence.
    url = _ensure_scheme(url)
    parsed = urlparse(url)

    result: Dict[str, Any] = {
        "url": url,
        "final_url": None,
        "status_code": None,
        "redirect_chain": [],
        "headers": {},
        "page_load_ms": None,
        "error": None,
    }

    # Guard against SSRF: reject private/loopback targets.
    hostname = parsed.hostname or ""
    if not hostname:
        result["error"] = "URL contains no hostname"
        return result

    logger.info("Checking HTTP status for %s", url)

    try:
        start = time.time()
        resp = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        )
        elapsed_ms = round((time.time() - start) * 1000, 2)

        result["status_code"] = resp.status_code
        result["final_url"] = resp.url
        result["page_load_ms"] = elapsed_ms
        result["headers"] = dict(resp.headers)

        redirect_chain: List[Dict[str, Any]] = [
            {"url": r.url, "status_code": r.status_code}
            for r in resp.history
        ]
        result["redirect_chain"] = redirect_chain

        logger.info(
            "HTTP %s for %s in %.1f ms (redirects=%d)",
            resp.status_code,
            url,
            elapsed_ms,
            len(redirect_chain),
        )

    except SSLError as exc:
        result["error"] = f"SSL error: {exc}"
        logger.warning("SSL error for %s: %s", url, exc)
    except ConnectionError as exc:
        result["error"] = f"Connection error: {exc}"
        logger.warning("Connection error for %s: %s", url, exc)
    except Timeout:
        result["error"] = "Request timed out"
        logger.warning("Request timed out for %s", url)
    except Exception as exc:  # pragma: no cover
        result["error"] = f"Unexpected error: {exc}"
        logger.error("Unexpected error for %s: %s", url, exc)

    return result

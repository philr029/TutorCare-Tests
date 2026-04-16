"""Shared HTTP client utility for the security-diagnostic toolkit.

Provides a thin :class:`HttpClient` wrapper around :mod:`requests` with:
- Configurable timeouts
- A clearly identified ``User-Agent`` header
- Automatic retry handling with exponential back-off
- Centralised error logging

Usage
-----
    from src.utils.http_client import HttpClient

    client = HttpClient(timeout=10)
    response = client.get("https://api.abuseipdb.com/api/v2/check",
                          headers={"Key": "YOUR_KEY"},
                          params={"ipAddress": "8.8.8.8"})
    data = response.json()
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logger import get_logger

logger = get_logger(__name__)

_DEFAULT_USER_AGENT = "SecurityToolkit/1.0 (+https://github.com/your-org/security-toolkit)"
_DEFAULT_TIMEOUT = 10
_DEFAULT_RETRIES = 3
_DEFAULT_BACKOFF = 0.5
# Retry on these transient HTTP status codes.
_RETRY_STATUS_CODES = frozenset([429, 500, 502, 503, 504])
# HTTP methods eligible for retry.
_RETRY_METHODS = frozenset(["GET", "POST"])


class HttpClient:
    """Lightweight HTTP client with retry, logging, and consistent headers.

    Args:
        timeout:        Request timeout in seconds.
        user_agent:     Override the default ``User-Agent`` string.
        retries:        Total number of retry attempts on transient failures.
        backoff_factor: Back-off multiplier between retries
                        (sleep = ``backoff_factor * 2 ** (retry - 1)`` seconds).

    Example::

        client = HttpClient(timeout=15, retries=3)
        resp = client.get("https://example.com/api", params={"key": "val"})
        print(resp.status_code)  # 200
    """

    def __init__(
        self,
        timeout: int = _DEFAULT_TIMEOUT,
        user_agent: str = _DEFAULT_USER_AGENT,
        retries: int = _DEFAULT_RETRIES,
        backoff_factor: float = _DEFAULT_BACKOFF,
    ) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=_RETRY_STATUS_CODES,
            allowed_methods=_RETRY_METHODS,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        """Perform an HTTP GET request.

        Args:
            url:     Target URL.
            headers: Additional request headers (merged with defaults).
            params:  Query-string parameters.
            **kwargs: Passed directly to :func:`requests.Session.get`.

        Returns:
            :class:`requests.Response` object.

        Raises:
            requests.RequestException: on any network or HTTP error.

        Example::

            resp = client.get(
                "https://api.abuseipdb.com/api/v2/check",
                headers={"Key": api_key, "Accept": "application/json"},
                params={"ipAddress": "1.2.3.4", "maxAgeInDays": 90},
            )
            resp.raise_for_status()
            print(resp.json()["data"]["abuseConfidenceScore"])
        """
        logger.debug("GET %s params=%s", url, params)
        try:
            resp = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=self.timeout,
                **kwargs,
            )
            logger.debug("Response %s from %s", resp.status_code, url)
            return resp
        except requests.RequestException as exc:
            logger.error("HTTP GET failed for %s: %s", url, exc)
            raise

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        """Perform an HTTP POST request.

        Args:
            url:     Target URL.
            headers: Additional request headers.
            json:    Request body (serialised automatically).
            **kwargs: Passed to :func:`requests.Session.post`.

        Returns:
            :class:`requests.Response` object.

        Raises:
            requests.RequestException: on any network or HTTP error.
        """
        logger.debug("POST %s", url)
        try:
            resp = self.session.post(
                url,
                headers=headers,
                json=json,
                timeout=self.timeout,
                **kwargs,
            )
            logger.debug("Response %s from %s", resp.status_code, url)
            return resp
        except requests.RequestException as exc:
            logger.error("HTTP POST failed for %s: %s", url, exc)
            raise

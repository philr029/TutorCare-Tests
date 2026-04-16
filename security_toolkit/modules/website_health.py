"""Website health and diagnostics module."""
from __future__ import annotations

import ipaddress
import socket
import ssl
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import dns.resolver
import requests
from requests.exceptions import SSLError, ConnectionError, Timeout

from ..utils.config_loader import load_config
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


_PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_private_address(hostname: str) -> bool:
    """Return True if the hostname resolves to a private/loopback address."""
    try:
        addr = ipaddress.ip_address(hostname)
        return any(addr in net for net in _PRIVATE_RANGES)
    except ValueError:
        pass
    try:
        resolved = socket.getaddrinfo(hostname, None)
        for item in resolved:
            try:
                addr = ipaddress.ip_address(item[4][0])
                if any(addr in net for net in _PRIVATE_RANGES):
                    return True
            except ValueError:
                continue
    except OSError:
        pass
    return False


def _ensure_scheme(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def _validate_url(url: str) -> Optional[str]:
    """Validate URL scheme and ensure the target is not a private network address.

    Returns an error string if invalid, or None if the URL is acceptable.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return f"Unsupported scheme '{parsed.scheme}'; only http and https are allowed"
    hostname = parsed.hostname or ""
    if not hostname:
        return "URL contains no hostname"
    if _is_private_address(hostname):
        return f"Target hostname '{hostname}' resolves to a private or loopback address"
    return None


def _check_http(url: str, timeout: int) -> Dict[str, Any]:
    """Check HTTP status, redirect chain, response headers, and page load time."""
    result: Dict[str, Any] = {
        "final_url": None,
        "status_code": None,
        "redirect_chain": [],
        "headers": {},
        "page_load_ms": None,
        "error": None,
    }
    url_error = _validate_url(url)
    if url_error:
        result["error"] = url_error
        return result
    try:
        start = time.time()
        resp = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "SecurityToolkit/1.0 (health-check)"},
        )
        elapsed_ms = round((time.time() - start) * 1000, 2)
        result["status_code"] = resp.status_code
        result["final_url"] = resp.url
        result["page_load_ms"] = elapsed_ms
        result["headers"] = dict(resp.headers)

        for r in resp.history:
            result["redirect_chain"].append({"url": r.url, "status_code": r.status_code})

    except SSLError as exc:
        result["error"] = f"SSL error: {exc}"
    except ConnectionError as exc:
        result["error"] = f"Connection error: {exc}"
    except Timeout:
        result["error"] = "Request timed out"
    except Exception as exc:  # pragma: no cover
        result["error"] = f"Unexpected error: {exc}"
    return result


def _check_ssl(hostname: str, port: int = 443, timeout: int = 10) -> Dict[str, Any]:
    """Check SSL certificate validity and details."""
    result: Dict[str, Any] = {
        "valid": False,
        "subject": None,
        "issuer": None,
        "not_before": None,
        "not_after": None,
        "days_until_expiry": None,
        "error": None,
    }
    try:
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        with ctx.wrap_socket(
            socket.create_connection((hostname, port), timeout=timeout),
            server_hostname=hostname,
        ) as ssock:
            cert = ssock.getpeercert()
        result["valid"] = True
        result["subject"] = dict(x[0] for x in cert.get("subject", []))
        result["issuer"] = dict(x[0] for x in cert.get("issuer", []))
        result["not_before"] = cert.get("notBefore")
        result["not_after"] = cert.get("notAfter")

        if cert.get("notAfter"):
            expiry = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            expiry = expiry.replace(tzinfo=timezone.utc)
            now = datetime.now(tz=timezone.utc)
            result["days_until_expiry"] = (expiry - now).days

    except ssl.SSLCertVerificationError as exc:
        result["error"] = f"Certificate verification failed: {exc}"
    except ssl.SSLError as exc:
        result["error"] = f"SSL error: {exc}"
    except socket.timeout:
        result["error"] = "Connection timed out"
    except OSError as exc:
        result["error"] = f"Socket error: {exc}"
    except Exception as exc:  # pragma: no cover
        result["error"] = f"Unexpected error: {exc}"
    return result


def _query_dns(domain: str) -> Dict[str, Any]:
    """Query DNS records: A, MX, TXT (including SPF, DKIM, DMARC)."""
    records: Dict[str, Any] = {
        "A": [],
        "MX": [],
        "TXT": [],
        "SPF": [],
        "DMARC": [],
        "DKIM_hint": "Query _domainkey.<domain> with selector to verify DKIM",
    }

    for rtype in ("A", "MX", "TXT"):
        try:
            answers = dns.resolver.resolve(domain, rtype)
            if rtype == "A":
                records["A"] = [str(r) for r in answers]
            elif rtype == "MX":
                records["MX"] = [
                    {"priority": r.preference, "host": str(r.exchange).rstrip(".")}
                    for r in answers
                ]
            elif rtype == "TXT":
                txt_records = [b"".join(r.strings).decode("utf-8", errors="replace") for r in answers]
                records["TXT"] = txt_records
                records["SPF"] = [t for t in txt_records if t.lower().startswith("v=spf1")]
        except dns.resolver.NoAnswer:
            pass
        except dns.resolver.NXDOMAIN:
            records[rtype] = "NXDOMAIN"
        except Exception as exc:
            records[rtype] = f"Error: {exc}"

    # DMARC
    try:
        dmarc_answers = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
        records["DMARC"] = [
            b"".join(r.strings).decode("utf-8", errors="replace") for r in dmarc_answers
        ]
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        records["DMARC"] = "No DMARC record found"
    except Exception as exc:
        records["DMARC"] = f"Error: {exc}"

    return records


def check_website(url: str, config: Optional[dict] = None) -> Dict[str, Any]:
    """
    Run non-intrusive health and diagnostics checks on a website.

    Args:
        url: Target URL or domain (e.g. "https://example.com" or "example.com").
        config: Optional config dict.

    Returns:
        Structured JSON-serializable dict with health results.
    """
    if config is None:
        config = load_config()

    settings = config.get("settings", {})
    timeout = settings.get("timeout", 10)

    url = _ensure_scheme(url)
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    url_error = _validate_url(url)
    if url_error:
        return {
            "input": url,
            "hostname": hostname,
            "error": url_error,
            "http": None,
            "ssl": None,
            "dns": None,
            "checked_at": datetime.now(tz=timezone.utc).isoformat(),
        }

    logger.info("Running website health check for %s", hostname)

    http_result = _check_http(url, timeout)
    ssl_result = _check_ssl(hostname, port=parsed.port or 443, timeout=timeout)
    dns_result = _query_dns(hostname)

    return {
        "input": url,
        "hostname": hostname,
        "http": http_result,
        "ssl": ssl_result,
        "dns": dns_result,
        "checked_at": datetime.now(tz=timezone.utc).isoformat(),
    }

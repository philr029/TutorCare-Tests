"""SSL/TLS certificate inspection for a target hostname.

Performs a standard TLS handshake (no traffic interception) and extracts
certificate metadata: subject, issuer, validity window, and days until expiry.

Usage
-----
    from src.site_diagnostics.ssl_check import check_ssl

    result = check_ssl("example.com")
    print(result["valid"])            # True
    print(result["days_until_expiry"])  # 120
"""
from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone
from typing import Any, Dict

from src.utils.logger import get_logger

logger = get_logger(__name__)


def check_ssl(hostname: str, port: int = 443, timeout: int = 10) -> Dict[str, Any]:
    """Inspect the SSL/TLS certificate for a given hostname and port.

    Connects via a standard TLS handshake (minimum TLS 1.2) and reads the
    peer certificate.  No traffic is captured or modified.

    Args:
        hostname: Target hostname (e.g. ``"example.com"``).
        port:     TLS port (default ``443``).
        timeout:  Socket connection timeout in seconds.

    Returns:
        Dictionary with keys:

        - ``hostname`` (*str*) – the queried hostname.
        - ``port`` (*int*) – the queried port.
        - ``valid`` (*bool*) – ``True`` if the certificate passed verification.
        - ``subject`` (*dict | None*) – certificate subject fields.
        - ``issuer`` (*dict | None*) – certificate issuer fields.
        - ``not_before`` (*str | None*) – certificate start date.
        - ``not_after`` (*str | None*) – certificate expiry date.
        - ``days_until_expiry`` (*int | None*) – days remaining until expiry.
        - ``error`` (*str | None*) – error message, or ``null`` on success.

    Example output (valid certificate)::

        {
          "hostname": "example.com",
          "port": 443,
          "valid": true,
          "subject": {"commonName": "example.com"},
          "issuer": {"organizationName": "DigiCert Inc"},
          "not_before": "Jan  1 00:00:00 2024 GMT",
          "not_after": "Mar  1 23:59:59 2025 GMT",
          "days_until_expiry": 120,
          "error": null
        }

    Example output (expired certificate)::

        {
          "hostname": "expired.badssl.com",
          "port": 443,
          "valid": false,
          "subject": null,
          "issuer": null,
          "not_before": null,
          "not_after": null,
          "days_until_expiry": null,
          "error": "Certificate verification failed: [SSL: CERTIFICATE_VERIFY_FAILED]"
        }
    """
    # TODO: Also retrieve and report the full certificate chain.
    # TODO: Check for weak cipher suites and report their names.
    result: Dict[str, Any] = {
        "hostname": hostname,
        "port": port,
        "valid": False,
        "subject": None,
        "issuer": None,
        "not_before": None,
        "not_after": None,
        "days_until_expiry": None,
        "error": None,
    }

    logger.info("Checking SSL certificate for %s:%d", hostname, port)

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

        logger.info(
            "SSL cert for %s: valid=True expires=%s days_left=%s",
            hostname,
            result["not_after"],
            result["days_until_expiry"],
        )

    except ssl.SSLCertVerificationError as exc:
        result["error"] = f"Certificate verification failed: {exc}"
        logger.warning("SSL verification failed for %s: %s", hostname, exc)
    except ssl.SSLError as exc:
        result["error"] = f"SSL error: {exc}"
        logger.warning("SSL error for %s: %s", hostname, exc)
    except socket.timeout:
        result["error"] = "Connection timed out"
        logger.warning("SSL connection timed out for %s", hostname)
    except OSError as exc:
        result["error"] = f"Socket error: {exc}"
        logger.warning("Socket error for %s: %s", hostname, exc)
    except Exception as exc:  # pragma: no cover
        result["error"] = f"Unexpected error: {exc}"
        logger.error("Unexpected SSL error for %s: %s", hostname, exc)

    return result

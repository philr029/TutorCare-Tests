"""DNS record lookup for site diagnostics.

Queries A, MX, and TXT records for a domain and automatically extracts SPF
and DMARC policies from TXT records.

Usage
-----
    from src.site_diagnostics.dns_records import query_dns_records

    result = query_dns_records("example.com")
    print(result["A"])      # ["93.184.216.34"]
    print(result["SPF"])    # ["v=spf1 -all"]
    print(result["DMARC"])  # ["v=DMARC1; p=reject; ..."]
"""
from __future__ import annotations

from typing import Any, Dict, List, Union

import dns.exception
import dns.resolver

from src.utils.logger import get_logger

logger = get_logger(__name__)


def _resolve(domain: str, rtype: str) -> Union[List[Any], str]:
    """Resolve DNS records of *rtype* for *domain*.

    Returns a list of records on success, ``"NXDOMAIN"`` if the domain does
    not exist, or an error string for any other failure.
    """
    try:
        return list(dns.resolver.resolve(domain, rtype))
    except dns.resolver.NoAnswer:
        return []
    except dns.resolver.NXDOMAIN:
        return "NXDOMAIN"
    except dns.exception.Timeout:
        logger.warning("DNS query timed out for %s %s", domain, rtype)
        return f"Error: DNS timeout for {rtype}"
    except Exception as exc:  # pragma: no cover
        logger.error("DNS query error for %s %s: %s", domain, rtype, exc)
        return f"Error: {exc}"


def query_dns_records(domain: str) -> Dict[str, Any]:
    """Query A, MX, TXT, SPF, and DMARC records for a domain.

    Args:
        domain: Domain name to query (e.g. ``"example.com"``).

    Returns:
        Dictionary with keys:

        - ``domain`` (*str*) – the queried domain.
        - ``A`` (*list[str] | str*) – A records (IPv4 addresses), or
          ``"NXDOMAIN"`` / error string.
        - ``MX`` (*list[dict]*) – list of ``{"priority": …, "host": …}`` dicts.
        - ``TXT`` (*list[str]*) – all TXT records.
        - ``SPF`` (*list[str]*) – TXT records beginning with ``"v=spf1"``.
        - ``DMARC`` (*list[str] | str*) – ``_dmarc.<domain>`` TXT records, or
          ``"No DMARC record found"``.
        - ``DKIM_hint`` – reminder to query ``_domainkey.<domain>`` with a
          selector for DKIM verification.

    Example output::

        {
          "domain": "example.com",
          "A": ["93.184.216.34"],
          "MX": [{"priority": 10, "host": "mail.example.com"}],
          "TXT": ["v=spf1 include:_spf.example.com ~all"],
          "SPF": ["v=spf1 include:_spf.example.com ~all"],
          "DMARC": ["v=DMARC1; p=reject; rua=mailto:dmarc@example.com"],
          "DKIM_hint": "Query _domainkey.<domain> with selector to verify DKIM"
        }
    """
    # TODO: Add AAAA (IPv6) record resolution.
    # TODO: Add CAA record resolution to detect authorised certificate issuers.
    logger.info("Querying DNS records for %s", domain)

    records: Dict[str, Any] = {
        "domain": domain,
        "A": [],
        "MX": [],
        "TXT": [],
        "SPF": [],
        "DMARC": [],
        "DKIM_hint": "Query _domainkey.<domain> with selector to verify DKIM",
    }

    # A records
    a_raw = _resolve(domain, "A")
    if isinstance(a_raw, list):
        records["A"] = [str(r) for r in a_raw]
    else:
        records["A"] = a_raw  # "NXDOMAIN" or error string

    # MX records
    mx_raw = _resolve(domain, "MX")
    if isinstance(mx_raw, list):
        records["MX"] = [
            {"priority": r.preference, "host": str(r.exchange).rstrip(".")}
            for r in mx_raw
        ]
    else:
        records["MX"] = mx_raw

    # TXT records (includes SPF)
    txt_raw = _resolve(domain, "TXT")
    if isinstance(txt_raw, list):
        txt_strings = [
            b"".join(r.strings).decode("utf-8", errors="replace") for r in txt_raw
        ]
        records["TXT"] = txt_strings
        records["SPF"] = [t for t in txt_strings if t.lower().startswith("v=spf1")]
    else:
        records["TXT"] = txt_raw

    # DMARC records
    dmarc_raw = _resolve(f"_dmarc.{domain}", "TXT")
    if isinstance(dmarc_raw, list):
        if dmarc_raw:
            records["DMARC"] = [
                b"".join(r.strings).decode("utf-8", errors="replace")
                for r in dmarc_raw
            ]
        else:
            records["DMARC"] = "No DMARC record found"
    elif isinstance(dmarc_raw, str) and "NXDOMAIN" in dmarc_raw:
        records["DMARC"] = "No DMARC record found"
    else:
        records["DMARC"] = dmarc_raw  # error string

    return records

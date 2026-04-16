"""IP and Domain Reputation checker module."""
from __future__ import annotations

import ipaddress
import socket
from typing import Any, Dict, List, Optional

import dns.resolver
import requests

from ..utils.config_loader import load_config
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def _reverse_ip(ip: str) -> str:
    """Reverse an IPv4 address for DNSBL lookup."""
    return ".".join(reversed(ip.split(".")))


def _check_dnsbl(ip: str, dnsbl_host: str) -> Dict[str, Any]:
    """Check if an IP is listed in a DNSBL."""
    try:
        reversed_ip = _reverse_ip(ip)
        query = f"{reversed_ip}.{dnsbl_host}"
        dns.resolver.resolve(query, "A")
        return {"listed": True, "details": f"Listed in {dnsbl_host}"}
    except dns.resolver.NXDOMAIN:
        return {"listed": False, "details": "Not listed"}
    except dns.resolver.NoNameservers:
        return {"listed": None, "details": "DNS lookup failed (no nameservers)"}
    except dns.exception.Timeout:
        return {"listed": None, "details": "DNS lookup timed out"}
    except Exception as exc:  # pragma: no cover
        logger.warning("DNSBL check error for %s at %s: %s", ip, dnsbl_host, exc)
        return {"listed": None, "details": f"Error: {exc}"}


def _resolve_domain_to_ip(domain: str) -> Optional[str]:
    """Resolve a domain name to its first A record IP."""
    try:
        answers = dns.resolver.resolve(domain, "A")
        return str(answers[0])
    except Exception as exc:
        logger.warning("Could not resolve domain %s: %s", domain, exc)
        return None


def _is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _check_abuseipdb(ip: str, api_key: str, timeout: int) -> Dict[str, Any]:
    """Query AbuseIPDB for IP reputation."""
    url = "https://api.abuseipdb.com/api/v2/check"
    headers = {"Key": api_key, "Accept": "application/json"}
    params = {"ipAddress": ip, "maxAgeInDays": 90}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        score = data.get("abuseConfidenceScore", 0)
        return {
            "listed": score > 0,
            "details": {
                "abuse_confidence_score": score,
                "country": data.get("countryCode"),
                "isp": data.get("isp"),
                "total_reports": data.get("totalReports", 0),
            },
        }
    except requests.RequestException as exc:
        logger.warning("AbuseIPDB query failed: %s", exc)
        return {"listed": None, "details": f"Request error: {exc}"}


def _check_virustotal(target: str, api_key: str, timeout: int) -> Dict[str, Any]:
    """Query VirusTotal for IP/domain reputation."""
    if _is_ip(target):
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{target}"
    else:
        url = f"https://www.virustotal.com/api/v3/domains/{target}"
    headers = {"x-apikey": api_key}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        stats = (
            resp.json()
            .get("data", {})
            .get("attributes", {})
            .get("last_analysis_stats", {})
        )
        malicious = stats.get("malicious", 0)
        return {
            "listed": malicious > 0,
            "details": stats,
        }
    except requests.RequestException as exc:
        logger.warning("VirusTotal query failed: %s", exc)
        return {"listed": None, "details": f"Request error: {exc}"}


def check_reputation(target: str, config: Optional[dict] = None) -> Dict[str, Any]:
    """
    Check the reputation of an IP address or domain.

    Args:
        target: An IPv4 address or domain name.
        config: Optional config dict (loaded from config.yaml if not provided).

    Returns:
        Structured JSON-serialisable dict with reputation results.
    """
    if config is None:
        config = load_config()

    settings = config.get("settings", {})
    api_keys = config.get("api_keys", {})
    timeout = settings.get("timeout", 10)
    dnsbl_sources = config.get("dnsbl_sources", [])

    # Resolve domain to IP for DNSBL checks
    if _is_ip(target):
        ip = target
        resolved_domain = None
    else:
        resolved_domain = target
        ip = _resolve_domain_to_ip(target)

    sources: List[Dict[str, Any]] = []
    overall_listed = False

    # DNSBL checks (IP only)
    if ip:
        for source in dnsbl_sources:
            result = _check_dnsbl(ip, source["host"])
            entry = {
                "name": source["name"],
                "status": "listed" if result["listed"] else ("unknown" if result["listed"] is None else "clean"),
                "details": result["details"],
            }
            sources.append(entry)
            if result["listed"]:
                overall_listed = True

    # AbuseIPDB (IP only)
    abuseipdb_key = api_keys.get("abuseipdb", "")
    if abuseipdb_key and ip:
        result = _check_abuseipdb(ip, abuseipdb_key, timeout)
        sources.append({
            "name": "AbuseIPDB",
            "status": "listed" if result["listed"] else ("unknown" if result["listed"] is None else "clean"),
            "details": result["details"],
        })
        if result["listed"]:
            overall_listed = True

    # VirusTotal (IP or domain)
    vt_key = api_keys.get("virustotal", "")
    if vt_key:
        result = _check_virustotal(target, vt_key, timeout)
        sources.append({
            "name": "VirusTotal",
            "status": "listed" if result["listed"] else ("unknown" if result["listed"] is None else "clean"),
            "details": result["details"],
        })
        if result["listed"]:
            overall_listed = True

    return {
        "input": target,
        "resolved_ip": ip if not _is_ip(target) else None,
        "listed": overall_listed,
        "sources": sources,
    }


def check_reputation_bulk(targets: List[str], config: Optional[dict] = None) -> List[Dict[str, Any]]:
    """Check reputation for a list of IPs or domains."""
    if config is None:
        config = load_config()
    return [check_reputation(t, config) for t in targets]

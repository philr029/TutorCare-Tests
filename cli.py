"""CLI entry point for the security-diagnostic toolkit (src layout).

Commands
--------
  check-ip       Check the reputation of an IP address (DNSBL + AbuseIPDB).
  check-domain   Check the reputation of a domain name (DNSBL).
  validate-phone Validate and enrich a phone number.
  site-health    Run full HTTP/SSL/DNS diagnostics for a website.

Usage
-----
    python cli.py check-ip 8.8.8.8
    python cli.py check-domain example.com
    python cli.py validate-phone "+14155552671"
    python cli.py site-health https://example.com

    # Use a custom config file
    python cli.py --config /path/to/config.json check-ip 1.2.3.4

    # Write JSON output to a file
    python cli.py --output result.json site-health example.com
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click

from src.ip_reputation.check_rbl import check_rbl_multi
from src.ip_reputation.check_abuseipdb import check_abuseipdb
from src.domain_reputation.check_dnsbl import check_domain_dnsbl
from src.phone_validation.validate_number import validate_number
from src.site_diagnostics.http_status import check_http_status
from src.site_diagnostics.ssl_check import check_ssl
from src.site_diagnostics.dns_records import query_dns_records
from src.utils.config_loader import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.option(
    "--config", "-c",
    default=None,
    metavar="PATH",
    help="Path to a JSON config file (default: config/config.example.json).",
)
@click.option(
    "--output", "-o",
    default=None,
    metavar="FILE",
    help="Write JSON output to FILE instead of stdout.",
)
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], output: Optional[str]) -> None:
    """Security Diagnostic Toolkit – non-intrusive security checks."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config)
    ctx.obj["output"] = output


def _emit(data: object, output_path: Optional[str]) -> None:
    """Print JSON to stdout or write to a file."""
    text = json.dumps(data, indent=2, default=str)
    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
        click.echo(f"Output written to {output_path}")
    else:
        click.echo(text)


# ---------------------------------------------------------------------------
# check-ip
# ---------------------------------------------------------------------------

@cli.command("check-ip")
@click.argument("ip")
@click.option(
    "--dnsbl",
    multiple=True,
    default=["zen.spamhaus.org", "multi.surbl.org", "bl.spamcop.net"],
    show_default=True,
    help="DNSBL host(s) to query.  Repeat for multiple.",
)
@click.pass_context
def check_ip(ctx: click.Context, ip: str, dnsbl: tuple) -> None:
    """Check the reputation of an IP address against DNSBLs and AbuseIPDB.

    \b
    Examples:
      python cli.py check-ip 8.8.8.8
      python cli.py check-ip 1.2.3.4 --dnsbl zen.spamhaus.org
    """
    cfg = ctx.obj["config"]
    api_keys = cfg.get("api_keys", {})
    settings = cfg.get("settings", {})
    timeout: int = settings.get("timeout", 10)

    # DNSBL checks
    rbl_results = check_rbl_multi(ip, list(dnsbl))

    # AbuseIPDB enrichment (optional)
    abuseipdb_key = api_keys.get("abuseipdb", "")
    abuseipdb_result = check_abuseipdb(ip, abuseipdb_key, timeout) if abuseipdb_key else None

    output = {
        "ip": ip,
        "dnsbl_results": rbl_results,
        "abuseipdb": abuseipdb_result,
    }
    _emit(output, ctx.obj["output"])


# ---------------------------------------------------------------------------
# check-domain
# ---------------------------------------------------------------------------

@cli.command("check-domain")
@click.argument("domain")
@click.option(
    "--dnsbl",
    multiple=True,
    default=["zen.spamhaus.org", "multi.surbl.org"],
    show_default=True,
    help="IP-based DNSBL host(s) to query.  Repeat for multiple.",
)
@click.pass_context
def check_domain(ctx: click.Context, domain: str, dnsbl: tuple) -> None:
    """Check the reputation of a domain against DNSBL and Spamhaus DBL.

    \b
    Examples:
      python cli.py check-domain example.com
      python cli.py check-domain malicious.example --dnsbl multi.surbl.org
    """
    result = check_domain_dnsbl(domain, list(dnsbl))
    _emit(result, ctx.obj["output"])


# ---------------------------------------------------------------------------
# validate-phone
# ---------------------------------------------------------------------------

@cli.command("validate-phone")
@click.argument("number")
@click.option(
    "--region", "-r",
    default=None,
    metavar="CC",
    help="Default region hint (e.g. US, GB).  Required for numbers without +country-code.",
)
@click.pass_context
def validate_phone_cmd(ctx: click.Context, number: str, region: Optional[str]) -> None:
    """Validate and enrich a phone number (offline + optional API).

    No calls, pings, or probes are ever made to the phone number itself.

    \b
    Examples:
      python cli.py validate-phone "+14155552671"
      python cli.py validate-phone "02071234567" --region GB
    """
    result = validate_number(number, region, ctx.obj["config"])
    _emit(result, ctx.obj["output"])


# ---------------------------------------------------------------------------
# site-health
# ---------------------------------------------------------------------------

@cli.command("site-health")
@click.argument("url")
@click.pass_context
def site_health(ctx: click.Context, url: str) -> None:
    """Run HTTP status, SSL certificate, and DNS diagnostics for a website.

    \b
    Examples:
      python cli.py site-health https://example.com
      python cli.py site-health example.com
    """
    from urllib.parse import urlparse

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    cfg = ctx.obj["config"]
    settings = cfg.get("settings", {})
    timeout: int = settings.get("timeout", 10)

    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    logger.info("Running site-health check for %s", hostname)

    http_result = check_http_status(url, timeout)
    ssl_result = check_ssl(hostname, port=parsed.port or 443, timeout=timeout)
    dns_result = query_dns_records(hostname)

    from datetime import datetime, timezone as _tz
    output = {
        "input": url,
        "hostname": hostname,
        "http": http_result,
        "ssl": ssl_result,
        "dns": dns_result,
        "checked_at": datetime.now(tz=_tz.utc).isoformat(),
    }
    _emit(output, ctx.obj["output"])


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()

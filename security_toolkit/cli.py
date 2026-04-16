"""CLI entry point for the security toolkit."""
import json
import sys
from typing import Optional

import click

from .modules.ip_reputation import check_reputation, check_reputation_bulk
from .modules.phone_validation import validate_phone
from .modules.website_health import check_website
from .utils.config_loader import load_config
from .utils.logging_utils import get_logger

logger = get_logger(__name__)


@click.group()
@click.option("--config", "-c", default=None, help="Path to config.yaml file.")
@click.option("--output", "-o", default=None, help="Write JSON output to file.")
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], output: Optional[str]) -> None:
    """Security Diagnostic Toolkit – IP, phone, and website checks."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config)
    ctx.obj["output"] = output


def _print_or_save(data: dict, output_path: Optional[str]) -> None:
    text = json.dumps(data, indent=2)
    if output_path:
        with open(output_path, "w") as f:
            f.write(text)
        click.echo(f"Output written to {output_path}")
    else:
        click.echo(text)


@cli.command("ip")
@click.argument("target")
@click.pass_context
def ip_check(ctx: click.Context, target: str) -> None:
    """Check reputation of an IP address or domain."""
    result = check_reputation(target, ctx.obj["config"])
    _print_or_save(result, ctx.obj["output"])


@cli.command("ip-bulk")
@click.argument("targets", nargs=-1, required=True)
@click.pass_context
def ip_bulk_check(ctx: click.Context, targets: tuple) -> None:
    """Check reputation of multiple IPs or domains."""
    results = check_reputation_bulk(list(targets), ctx.obj["config"])
    _print_or_save(results, ctx.obj["output"])


@cli.command("phone")
@click.argument("number")
@click.option("--region", "-r", default=None, help="Default region hint (e.g. US, GB).")
@click.pass_context
def phone_check(ctx: click.Context, number: str, region: Optional[str]) -> None:
    """Validate a phone number (format, country, carrier, line type)."""
    result = validate_phone(number, region, ctx.obj["config"])
    _print_or_save(result, ctx.obj["output"])


@cli.command("website")
@click.argument("url")
@click.pass_context
def website_check(ctx: click.Context, url: str) -> None:
    """Run health and diagnostics checks on a website."""
    result = check_website(url, ctx.obj["config"])
    _print_or_save(result, ctx.obj["output"])


@cli.command("serve")
@click.option("--host", default="127.0.0.1", help="Host to bind.")
@click.option("--port", "-p", default=5000, help="Port to listen on.")
@click.option("--debug", is_flag=True, default=False, help="Enable Flask debug mode.")
@click.pass_context
def serve(ctx: click.Context, host: str, port: int, debug: bool) -> None:
    """Start the lightweight web dashboard."""
    from .web.dashboard import create_app
    app = create_app(ctx.obj["config"])
    click.echo(f"Dashboard running at http://{host}:{port}/")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    cli()

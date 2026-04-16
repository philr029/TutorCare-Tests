"""Configuration loader for security toolkit."""
import os
import yaml
from pathlib import Path


DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.yaml"


def load_config(config_path: str = None) -> dict:
    """Load configuration from YAML file."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        return _default_config()
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    return config or _default_config()


def _default_config() -> dict:
    return {
        "api_keys": {
            "abuseipdb": "",
            "virustotal": "",
            "numverify": "",
            "twilio_sid": "",
            "twilio_token": "",
        },
        "settings": {
            "timeout": 10,
            "log_level": "INFO",
            "log_file": "security_toolkit.log",
            "redact_keys": True,
        },
        "dnsbl_sources": [
            {"name": "Spamhaus ZEN", "host": "zen.spamhaus.org"},
            {"name": "SURBL", "host": "multi.surbl.org"},
            {"name": "Barracuda", "host": "b.barracudacentral.org"},
            {"name": "SpamCop", "host": "bl.spamcop.net"},
            {"name": "SORBS", "host": "dnsbl.sorbs.net"},
        ],
    }

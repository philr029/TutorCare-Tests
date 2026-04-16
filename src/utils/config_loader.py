"""JSON configuration loader for the security-diagnostic toolkit.

Loads ``config/config.example.json`` (or a user-supplied path) and merges it
with safe defaults so the toolkit always has a usable configuration dict.

Usage
-----
    from src.utils.config_loader import load_config

    cfg = load_config()                      # uses default path
    cfg = load_config("/custom/config.json") # explicit path
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = (
    Path(__file__).parent.parent.parent / "config" / "config.example.json"
)


def _default_config() -> Dict[str, Any]:
    """Return a safe, key-free default configuration."""
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
            "log_file": None,
        },
        "dnsbl_sources": [
            {"name": "Spamhaus ZEN", "host": "zen.spamhaus.org"},
            {"name": "SURBL", "host": "multi.surbl.org"},
            {"name": "Barracuda", "host": "b.barracudacentral.org"},
        ],
    }


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a JSON file, falling back to safe defaults.

    Args:
        config_path: Absolute or relative path to a JSON config file.
                     Defaults to ``config/config.example.json``.

    Returns:
        Merged configuration dictionary.

    Example input file (config/config.example.json)::

        {
          "api_keys": { "abuseipdb": "YOUR_KEY" },
          "settings": { "timeout": 15, "log_level": "DEBUG" }
        }

    Raises:
        json.JSONDecodeError: if the file contains invalid JSON.
    """
    # TODO: Add schema validation (e.g. jsonschema) to catch typos early.
    # TODO: Support environment-variable overrides (e.g. ABUSEIPDB_KEY).
    defaults = _default_config()
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH

    if not path.exists():
        logger.warning(
            "Config file not found at '%s'; using defaults. "
            "Copy config/config.example.json and fill in your API keys.",
            path,
        )
        return defaults

    try:
        with open(path, "r", encoding="utf-8") as fh:
            user_cfg: Dict[str, Any] = json.load(fh)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in config '%s': %s", path, exc)
        raise

    # Deep-merge: user values override defaults, missing keys fall back.
    merged = _deep_merge(defaults, user_cfg)
    return merged


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *override* into a copy of *base*."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

"""JSON configuration loader for the security-diagnostic toolkit.

Loads ``config/config.example.json`` (or a user-supplied path) and merges it
with safe defaults so the toolkit always has a usable configuration dict.
Environment variables override file values so that secrets can be injected
via the shell without modifying the config file.

Environment variable overrides
-------------------------------
The following environment variables are recognised:

+--------------------+---------------------------------+
| Variable           | Config path                     |
+====================+=================================+
| ``ABUSEIPDB_KEY``  | ``api_keys.abuseipdb``          |
| ``VIRUSTOTAL_KEY`` | ``api_keys.virustotal``         |
| ``NUMVERIFY_KEY``  | ``api_keys.numverify``          |
| ``TWILIO_SID``     | ``api_keys.twilio_sid``         |
| ``TWILIO_TOKEN``   | ``api_keys.twilio_token``       |
| ``TOOLKIT_TIMEOUT``| ``settings.timeout`` (int)      |
| ``TOOLKIT_LOG``    | ``settings.log_level``          |
+--------------------+---------------------------------+

Usage
-----
    from src.utils.config_loader import load_config

    cfg = load_config()                      # uses default path
    cfg = load_config("/custom/config.json") # explicit path
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = (
    Path(__file__).parent.parent.parent / "config" / "config.example.json"
)

# Mapping from environment variable name to (config_section, config_key).
_ENV_MAP: Dict[str, Tuple[str, str]] = {
    "ABUSEIPDB_KEY":  ("api_keys", "abuseipdb"),
    "VIRUSTOTAL_KEY": ("api_keys", "virustotal"),
    "NUMVERIFY_KEY":  ("api_keys", "numverify"),
    "TWILIO_SID":     ("api_keys", "twilio_sid"),
    "TWILIO_TOKEN":   ("api_keys", "twilio_token"),
    "TOOLKIT_TIMEOUT": ("settings", "timeout"),
    "TOOLKIT_LOG":    ("settings", "log_level"),
}


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


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment-variable overrides to *config* (in-place).

    Values from the environment always take precedence over file values.
    The ``TOOLKIT_TIMEOUT`` variable is coerced to ``int``; other values
    are stored as-is.
    """
    for env_var, (section, key) in _ENV_MAP.items():
        value: Optional[str] = os.environ.get(env_var)
        if value is None:
            continue
        if section not in config:
            config[section] = {}
        if env_var == "TOOLKIT_TIMEOUT":
            try:
                config[section][key] = int(value)
            except ValueError:
                logger.warning(
                    "Invalid value for %s – expected an integer, got %r",
                    env_var,
                    value,
                )
        else:
            config[section][key] = value
        logger.debug("Config override from env: %s -> %s.%s", env_var, section, key)
    return config


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a JSON file, falling back to safe defaults.

    Environment variables are applied after file loading so they always
    take precedence.

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
    defaults = _default_config()
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH

    if not path.exists():
        logger.warning(
            "Config file not found at '%s'; using defaults. "
            "Copy config/config.example.json and fill in your API keys.",
            path,
        )
        return _apply_env_overrides(defaults)

    try:
        with open(path, "r", encoding="utf-8") as fh:
            user_cfg: Dict[str, Any] = json.load(fh)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in config '%s': %s", path, exc)
        raise

    # Deep-merge: user values override defaults, missing keys fall back.
    merged = _deep_merge(defaults, user_cfg)
    # Environment variables have the highest precedence.
    return _apply_env_overrides(merged)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *override* into a copy of *base*."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

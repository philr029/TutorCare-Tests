"""API configuration – reads from environment variables / .env file.

All settings have safe defaults so the server starts without any configuration.
Secrets (API_KEY, REDIS_URL, etc.) must be provided at runtime via environment
variables or a ``.env`` file in the project root.
"""
from __future__ import annotations

import os
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Server ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    debug: bool = False

    # --- Auth ---
    api_keys: str = ""          # Comma-separated list of valid API keys
    auth_disabled: bool = False  # Disable auth for local dev

    # --- Rate limiting ---
    rate_limit_enabled: bool = True
    rate_limit_default: str = "60/minute"
    redis_url: Optional[str] = None  # e.g. redis://localhost:6379

    # --- CORS ---
    cors_origins: str = "*"     # Comma-separated allowed origins

    # --- Logging ---
    log_level: str = "INFO"
    log_json: bool = True       # Structured JSON logs

    # --- External API keys (forwarded to src/ modules) ---
    abuseipdb_key: str = ""
    virustotal_key: str = ""
    numverify_key: str = ""
    twilio_sid: str = ""
    twilio_token: str = ""

    # --- Timeout ---
    request_timeout: int = 10

    @field_validator("api_keys", mode="before")
    @classmethod
    def _strip_api_keys(cls, v: str) -> str:
        return v.strip()

    def get_api_key_list(self) -> List[str]:
        """Return the list of valid API keys (may be empty)."""
        if not self.api_keys:
            return []
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    def get_cors_origins(self) -> List[str]:
        """Return the list of allowed CORS origins."""
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def build_module_config(self) -> dict:
        """Build the config dict expected by src/ modules."""
        return {
            "api_keys": {
                "abuseipdb": self.abuseipdb_key,
                "virustotal": self.virustotal_key,
                "numverify": self.numverify_key,
                "twilio_sid": self.twilio_sid,
                "twilio_token": self.twilio_token,
            },
            "settings": {
                "timeout": self.request_timeout,
                "log_level": self.log_level,
                "log_file": None,
            },
        }


_settings: Optional[Settings] = None

# Safe fallback values used when environment validation fails.
_SAFE_DEFAULTS: dict = {
    "api_host": "0.0.0.0",
    "api_port": 8000,
    "api_workers": 1,
    "debug": False,
    "api_keys": "",
    "auth_disabled": False,
    "rate_limit_enabled": True,
    "rate_limit_default": "60/minute",
    "redis_url": None,
    "cors_origins": "*",
    "log_level": "INFO",
    "log_json": True,
    "abuseipdb_key": "",
    "virustotal_key": "",
    "numverify_key": "",
    "twilio_sid": "",
    "twilio_token": "",
    "request_timeout": 10,
}


def get_settings() -> Settings:
    """Return the cached application settings (singleton).

    Falls back to hard-coded safe defaults when environment variables contain
    invalid values (e.g. a non-integer ``API_PORT``), so the server can always
    start and serve ``/health``.
    """
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except Exception:  # noqa: BLE001 – catch pydantic ValidationError + any other parse error
            import logging as _logging
            _logging.getLogger(__name__).warning(
                "Failed to load Settings from environment; using safe defaults."
            )
            _settings = Settings.model_construct(**_SAFE_DEFAULTS)
    return _settings

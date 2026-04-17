"""Rate limiting configuration using SlowAPI (built on limits/Redis)."""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from api.config import get_settings


def _build_limiter() -> Limiter:
    settings = get_settings()
    storage_uri = settings.redis_url or "memory://"
    return Limiter(key_func=get_remote_address, storage_uri=storage_uri)


limiter = _build_limiter()

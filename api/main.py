"""Security Diagnostic Toolkit – FastAPI application entry point.

Starts the API server with:
- Structured JSON logging
- CORS middleware
- Rate limiting (SlowAPI)
- Request/response logging middleware
- API key authentication (per-route dependency)
- Auto-generated Swagger UI at /docs and ReDoc at /redoc
- Prometheus metrics at /metrics
- Health check at /health

Start with:
    uvicorn api.main:app --host 0.0.0.0 --port 8000
Or via the helper script:
    python -m api.main
"""
from __future__ import annotations

import logging
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette import status

from api.config import get_settings
from api.middleware.logging import RequestLoggingMiddleware
from api.middleware.rate_limit import limiter
from api.routes import health, ip, domain, phone, site

# ---------------------------------------------------------------------------
# Logging setup – structured JSON when LOG_JSON=true
# ---------------------------------------------------------------------------

def _configure_logging(settings) -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    if settings.log_json:
        import json as _json

        class _JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_obj = {
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                if record.exc_info:
                    log_obj["exception"] = self.formatException(record.exc_info)
                return _json.dumps(log_obj)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
        logging.basicConfig(level=level, handlers=[handler], force=True)
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            stream=sys.stdout,
            force=True,
        )


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()
    _configure_logging(settings)

    app = FastAPI(
        title="Security Diagnostic Toolkit API",
        description=(
            "A production-ready REST API wrapping the Security Diagnostic Toolkit.\n\n"
            "Provides IP reputation checks, domain reputation checks, phone number "
            "validation, and site-health diagnostics.\n\n"
            "**Authentication**: pass your API key in the `X-API-Key` header.  "
            "Authentication is disabled when no keys are configured."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # --- Rate limiter state ---
    app.state.limiter = limiter

    # --- Rate limit exceeded handler ---
    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": f"Rate limit exceeded: {exc.detail}"},
        )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Request/response logging ---
    app.add_middleware(RequestLoggingMiddleware)

    # --- Routes ---
    app.include_router(health.router)
    app.include_router(ip.router)
    app.include_router(domain.router)
    app.include_router(phone.router)
    app.include_router(site.router)

    return app


app = create_app()


# ---------------------------------------------------------------------------
# Dev-server entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    cfg = get_settings()
    uvicorn.run(
        "api.main:app",
        host=cfg.api_host,
        port=cfg.api_port,
        workers=cfg.api_workers,
        reload=cfg.debug,
        log_config=None,  # use our logging config
    )

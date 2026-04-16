"""Web dashboard placeholder package.

This directory is reserved for an optional lightweight web dashboard that
exposes the toolkit's capabilities through a browser UI and REST API.

Current status: PLACEHOLDER – not yet implemented.

Planned features
----------------
- Single-page UI (HTML + vanilla JS or a lightweight framework).
- REST endpoints mirroring the CLI commands:
    GET /api/check-ip?ip=1.2.3.4
    GET /api/check-domain?domain=example.com
    GET /api/validate-phone?number=+14155552671&region=US
    GET /api/site-health?url=https://example.com
- JSON response format identical to CLI output.
- Optional authentication via API token header.

TODO
----
- [ ] Choose a framework (Flask already available, or FastAPI).
- [ ] Implement REST endpoints.
- [ ] Build a minimal HTML front-end with result cards.
- [ ] Add rate-limiting middleware.
- [ ] Write integration tests.

See also: security_toolkit/web/dashboard.py for the existing Flask dashboard.
"""

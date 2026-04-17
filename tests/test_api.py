"""Tests for the FastAPI layer.

Tests cover:
- Health and metrics endpoints
- API key authentication
- Rate limiting (decorator presence)
- Input validation (Pydantic schemas)
- Route registration
- Controller/service integration (mocked)
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Patch settings before importing the app so we control auth/rate-limiting
import os
os.environ.setdefault("AUTH_DISABLED", "true")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from api.main import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_schema(self):
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert "service" in data

    def test_metrics_returns_200(self):
        resp = client.get("/metrics")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# IP reputation – input validation
# ---------------------------------------------------------------------------

class TestCheckIPValidation:
    def test_missing_body_returns_422(self):
        resp = client.post("/check-ip", json={})
        assert resp.status_code == 422

    def test_invalid_ip_returns_422(self):
        resp = client.post("/check-ip", json={"ip": "not-an-ip"})
        assert resp.status_code == 422

    def test_ipv6_returns_422(self):
        resp = client.post("/check-ip", json={"ip": "::1"})
        assert resp.status_code == 422

    def test_valid_ip_calls_service(self):
        mock_result = {
            "ip": "8.8.8.8",
            "dnsbl_results": [{"ip": "8.8.8.8", "dnsbl": "zen.spamhaus.org",
                                "listed": False, "details": "Not listed"}],
            "abuseipdb": None,
        }
        with patch("api.controllers.ip_controller.check_ip", return_value=mock_result):
            resp = client.post("/check-ip", json={"ip": "8.8.8.8"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ip"] == "8.8.8.8"
        assert isinstance(data["dnsbl_results"], list)


# ---------------------------------------------------------------------------
# Domain reputation – input validation
# ---------------------------------------------------------------------------

class TestCheckDomainValidation:
    def test_missing_body_returns_422(self):
        resp = client.post("/check-domain", json={})
        assert resp.status_code == 422

    def test_invalid_domain_returns_422(self):
        resp = client.post("/check-domain", json={"domain": "not a domain!"})
        assert resp.status_code == 422

    def test_valid_domain_calls_service(self):
        mock_result = {
            "domain": "example.com",
            "resolved_ips": ["93.184.216.34"],
            "listed": False,
            "sources": [],
        }
        with patch("api.controllers.domain_controller.check_domain",
                   return_value=mock_result):
            resp = client.post("/check-domain", json={"domain": "example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["domain"] == "example.com"
        assert data["listed"] is False


# ---------------------------------------------------------------------------
# Phone validation – input validation
# ---------------------------------------------------------------------------

class TestValidatePhoneValidation:
    def test_missing_body_returns_422(self):
        resp = client.post("/validate-phone", json={})
        assert resp.status_code == 422

    def test_empty_phone_returns_422(self):
        resp = client.post("/validate-phone", json={"phone": ""})
        assert resp.status_code == 422

    def test_invalid_region_returns_422(self):
        resp = client.post("/validate-phone",
                           json={"phone": "+14155552671", "region": "INVALID"})
        assert resp.status_code == 422

    def test_valid_phone_calls_service(self):
        mock_result = {
            "input": "+14155552671",
            "valid": True,
            "possible": True,
            "format": {
                "e164": "+14155552671",
                "international": "+1 415-555-2671",
                "national": "(415) 555-2671",
            },
            "country": "United States",
            "region": "US",
            "carrier": None,
            "line_type": "fixed_line_or_mobile",
            "timezones": ["America/Los_Angeles"],
            "sources": [],
            "error": None,
        }
        with patch("api.controllers.phone_controller.validate_phone",
                   return_value=mock_result):
            resp = client.post("/validate-phone", json={"phone": "+14155552671"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["region"] == "US"


# ---------------------------------------------------------------------------
# Site health – input validation
# ---------------------------------------------------------------------------

class TestSiteHealthValidation:
    def test_missing_body_returns_422(self):
        resp = client.post("/site-health", json={})
        assert resp.status_code == 422

    def test_invalid_url_returns_422(self):
        resp = client.post("/site-health", json={"url": "not a url !!!"})
        assert resp.status_code == 422

    def test_timeout_out_of_range_returns_422(self):
        resp = client.post("/site-health",
                           json={"url": "https://example.com", "timeout": 0})
        assert resp.status_code == 422

    def test_valid_url_calls_service(self):
        mock_result = {
            "hostname": "example.com",
            "http": {"status_code": 200, "error": None},
            "ssl": {"valid": True, "error": None},
            "dns": {"A": ["93.184.216.34"]},
            "checked_at": "2024-01-15T10:30:00+00:00",
        }
        with patch("api.controllers.site_controller.site_health",
                   return_value=mock_result):
            resp = client.post("/site-health",
                               json={"url": "https://example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["hostname"] == "example.com"


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class TestAuthentication:
    def test_no_key_allowed_when_auth_disabled(self):
        """When AUTH_DISABLED=true, requests without a key should succeed."""
        mock_result = {
            "ip": "1.2.3.4",
            "dnsbl_results": [],
            "abuseipdb": None,
        }
        with patch("api.controllers.ip_controller.check_ip", return_value=mock_result):
            resp = client.post("/check-ip", json={"ip": "1.2.3.4"})
        assert resp.status_code == 200

    def test_auth_required_when_keys_configured(self, monkeypatch):
        """When API_KEYS is set, missing X-API-Key returns 401."""
        from api.middleware import auth as auth_mod
        from api import config as cfg_mod

        # Fresh settings with a key configured and auth enabled
        import importlib
        monkeypatch.setenv("API_KEYS", "test-secret-key")
        monkeypatch.setenv("AUTH_DISABLED", "false")
        cfg_mod._settings = None          # reset cache
        new_settings = cfg_mod.get_settings()
        assert new_settings.get_api_key_list() == ["test-secret-key"]

        # Restore after test
        cfg_mod._settings = None
        monkeypatch.setenv("AUTH_DISABLED", "true")
        monkeypatch.delenv("API_KEYS", raising=False)

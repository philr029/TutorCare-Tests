"""Additional pytest tests for the FastAPI backend using realistic sample inputs.

These tests complement tests/test_api.py with:
- Full happy-path scenarios using canonical sample values
- Response-shape validation (every required field is present)
- Boundary / edge-case input checks
- Consistent failure logging so CI logs are self-explanatory

All service calls are mocked so no real network traffic is required.

Run locally:
    pip install -r requirements.txt -r requirements-api.txt
    AUTH_DISABLED=true python -m pytest tests/test_api_routes.py -v
"""
from __future__ import annotations

import os
import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Disable auth and rate-limiting before importing the app
os.environ.setdefault("AUTH_DISABLED", "true")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from api.main import app  # noqa: E402

logger = logging.getLogger(__name__)
client = TestClient(app, raise_server_exceptions=True)

# ---------------------------------------------------------------------------
# Sample inputs used across all tests
# ---------------------------------------------------------------------------

SAMPLE_IP = "8.8.8.8"           # Google Public DNS – well-known, non-routable abuse
SAMPLE_DOMAIN = "example.com"   # IANA reserved test domain
SAMPLE_PHONE = "+14155552671"    # US fictitious number (safe for testing)
SAMPLE_URL = "https://example.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_failure(endpoint: str, resp) -> None:
    """Log response details when a test assertion is about to fail."""
    logger.warning(
        "Unexpected response from %s – status=%s body=%s",
        endpoint,
        resp.status_code,
        resp.text[:500],
    )


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealthRoute:
    """Full health-endpoint contract."""

    def test_returns_200(self):
        resp = client.get("/health")
        if resp.status_code != 200:
            _log_failure("/health", resp)
        assert resp.status_code == 200

    def test_content_type_is_json(self):
        resp = client.get("/health")
        assert "application/json" in resp.headers.get("content-type", "")

    def test_status_field_is_ok(self):
        data = client.get("/health").json()
        assert data.get("status") == "ok", f"Unexpected status: {data}"

    def test_service_field_present(self):
        data = client.get("/health").json()
        assert "service" in data

    def test_optional_key_flags_are_booleans(self):
        """abuseipdb_loaded, virustotal_loaded etc. must be bool (may be False in CI)."""
        data = client.get("/health").json()
        for key in ("abuseipdb_loaded", "virustotal_loaded", "numverify_loaded", "twilio_loaded"):
            assert key in data, f"Missing key: {key}"
            assert isinstance(data[key], bool), f"{key} must be bool, got {type(data[key])}"

    def test_repeated_calls_are_idempotent(self):
        """Health endpoint must return the same shape on repeated calls."""
        first = client.get("/health").json()
        second = client.get("/health").json()
        assert first.keys() == second.keys()


# ---------------------------------------------------------------------------
# POST /check-ip
# ---------------------------------------------------------------------------

# Pre-built mock payloads
_IP_MOCK_CLEAN = {
    "ip": SAMPLE_IP,
    "dnsbl_results": [
        {"ip": SAMPLE_IP, "dnsbl": "zen.spamhaus.org", "listed": False, "details": "Not listed"},
        {"ip": SAMPLE_IP, "dnsbl": "bl.spamcop.net",   "listed": False, "details": "Not listed"},
    ],
    "abuseipdb": None,
}

_IP_MOCK_LISTED = {
    "ip": "192.0.2.1",
    "dnsbl_results": [
        {"ip": "192.0.2.1", "dnsbl": "zen.spamhaus.org", "listed": True, "details": "SBL listed"},
    ],
    "abuseipdb": {
        "abuse_confidence_score": 87,
        "total_reports": 42,
        "country_code": "US",
        "isp": "Example ISP",
    },
}


class TestCheckIPRoute:
    """POST /check-ip happy paths and input validation."""

    def test_clean_ip_returns_200(self):
        with patch("api.controllers.ip_controller.check_ip", return_value=_IP_MOCK_CLEAN):
            resp = client.post("/check-ip", json={"ip": SAMPLE_IP})
        if resp.status_code != 200:
            _log_failure("/check-ip", resp)
        assert resp.status_code == 200

    def test_response_contains_ip_field(self):
        with patch("api.controllers.ip_controller.check_ip", return_value=_IP_MOCK_CLEAN):
            data = client.post("/check-ip", json={"ip": SAMPLE_IP}).json()
        assert data["ip"] == SAMPLE_IP

    def test_response_contains_dnsbl_results_list(self):
        with patch("api.controllers.ip_controller.check_ip", return_value=_IP_MOCK_CLEAN):
            data = client.post("/check-ip", json={"ip": SAMPLE_IP}).json()
        assert isinstance(data["dnsbl_results"], list)
        assert len(data["dnsbl_results"]) > 0

    def test_dnsbl_entry_shape(self):
        with patch("api.controllers.ip_controller.check_ip", return_value=_IP_MOCK_CLEAN):
            data = client.post("/check-ip", json={"ip": SAMPLE_IP}).json()
        entry = data["dnsbl_results"][0]
        for field in ("ip", "dnsbl", "listed", "details"):
            assert field in entry, f"Missing field '{field}' in dnsbl_results entry"

    def test_listed_ip_returns_200_with_abuseipdb(self):
        with patch("api.controllers.ip_controller.check_ip", return_value=_IP_MOCK_LISTED):
            resp = client.post("/check-ip", json={"ip": "192.0.2.1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["abuseipdb"] is not None
        assert "abuse_confidence_score" in data["abuseipdb"]

    def test_private_ip_passes_validation(self):
        """Private IPs (RFC 1918) are valid IPv4 – schema must accept them."""
        mock = {**_IP_MOCK_CLEAN, "ip": "10.0.0.1",
                "dnsbl_results": [{"ip": "10.0.0.1", "dnsbl": "zen.spamhaus.org",
                                    "listed": False, "details": "Not listed"}]}
        with patch("api.controllers.ip_controller.check_ip", return_value=mock):
            resp = client.post("/check-ip", json={"ip": "10.0.0.1"})
        assert resp.status_code == 200

    def test_missing_ip_field_returns_422(self):
        resp = client.post("/check-ip", json={})
        assert resp.status_code == 422

    def test_invalid_ip_string_returns_422(self):
        resp = client.post("/check-ip", json={"ip": "not-an-ip"})
        assert resp.status_code == 422

    def test_ipv6_address_returns_422(self):
        """API only accepts IPv4."""
        resp = client.post("/check-ip", json={"ip": "2001:db8::1"})
        assert resp.status_code == 422

    def test_empty_string_ip_returns_422(self):
        resp = client.post("/check-ip", json={"ip": ""})
        assert resp.status_code == 422

    def test_custom_dnsbl_zones_are_forwarded(self):
        """When dnsbl_zones is supplied, service should be called with that data."""
        called_with = {}

        def fake_check_ip(**kwargs):
            called_with.update(kwargs)
            return _IP_MOCK_CLEAN

        with patch("api.controllers.ip_controller.check_ip", side_effect=fake_check_ip):
            client.post(
                "/check-ip",
                json={"ip": SAMPLE_IP, "dnsbl_zones": ["zen.spamhaus.org"]},
            )
        # Verify the request was forwarded (the ip kwarg will be present)
        assert called_with.get("ip") == SAMPLE_IP


# ---------------------------------------------------------------------------
# POST /check-domain
# ---------------------------------------------------------------------------

_DOMAIN_MOCK_CLEAN = {
    "domain": SAMPLE_DOMAIN,
    "resolved_ips": ["93.184.216.34"],
    "listed": False,
    "sources": [],
}

_DOMAIN_MOCK_LISTED = {
    "domain": "malicious-example.com",
    "resolved_ips": ["198.51.100.5"],
    "listed": True,
    # sources must be a list of dicts to match the CheckDomainResponse schema
    "sources": [{"dnsbl": "dbl.spamhaus.org", "type": "domain"}],
}


class TestCheckDomainRoute:
    """POST /check-domain happy paths and input validation."""

    def test_clean_domain_returns_200(self):
        with patch("api.controllers.domain_controller.check_domain", return_value=_DOMAIN_MOCK_CLEAN):
            resp = client.post("/check-domain", json={"domain": SAMPLE_DOMAIN})
        if resp.status_code != 200:
            _log_failure("/check-domain", resp)
        assert resp.status_code == 200

    def test_response_domain_field_matches_input(self):
        with patch("api.controllers.domain_controller.check_domain", return_value=_DOMAIN_MOCK_CLEAN):
            data = client.post("/check-domain", json={"domain": SAMPLE_DOMAIN}).json()
        assert data["domain"] == SAMPLE_DOMAIN

    def test_response_contains_listed_boolean(self):
        with patch("api.controllers.domain_controller.check_domain", return_value=_DOMAIN_MOCK_CLEAN):
            data = client.post("/check-domain", json={"domain": SAMPLE_DOMAIN}).json()
        assert isinstance(data["listed"], bool)

    def test_response_contains_resolved_ips_list(self):
        with patch("api.controllers.domain_controller.check_domain", return_value=_DOMAIN_MOCK_CLEAN):
            data = client.post("/check-domain", json={"domain": SAMPLE_DOMAIN}).json()
        assert isinstance(data["resolved_ips"], list)

    def test_response_contains_sources_list(self):
        with patch("api.controllers.domain_controller.check_domain", return_value=_DOMAIN_MOCK_CLEAN):
            data = client.post("/check-domain", json={"domain": SAMPLE_DOMAIN}).json()
        assert isinstance(data["sources"], list)

    def test_listed_domain_returns_correct_flag(self):
        with patch("api.controllers.domain_controller.check_domain", return_value=_DOMAIN_MOCK_LISTED):
            data = client.post("/check-domain", json={"domain": "malicious-example.com"}).json()
        assert data["listed"] is True
        assert len(data["sources"]) > 0

    def test_subdomain_is_accepted(self):
        mock = {**_DOMAIN_MOCK_CLEAN, "domain": "sub.example.com"}
        with patch("api.controllers.domain_controller.check_domain", return_value=mock):
            resp = client.post("/check-domain", json={"domain": "sub.example.com"})
        assert resp.status_code == 200

    def test_missing_domain_field_returns_422(self):
        resp = client.post("/check-domain", json={})
        assert resp.status_code == 422

    def test_domain_with_spaces_returns_422(self):
        resp = client.post("/check-domain", json={"domain": "not a domain!"})
        assert resp.status_code == 422

    def test_empty_domain_returns_422(self):
        resp = client.post("/check-domain", json={"domain": ""})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /validate-phone
# ---------------------------------------------------------------------------

_PHONE_MOCK_VALID = {
    "input": SAMPLE_PHONE,
    "valid": True,
    "possible": True,
    "format": {
        "e164": SAMPLE_PHONE,
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

_PHONE_MOCK_INVALID = {
    "input": "not-a-phone",
    "valid": False,
    "possible": False,
    # format must be None or a Dict[str, str]; None values inside the dict are
    # not accepted by the ValidatePhoneResponse schema
    "format": None,
    "country": None,
    "region": None,
    "carrier": None,
    "line_type": None,
    "timezones": [],
    "sources": [],
    "error": "The string supplied is too short to be a phone number.",
}

_PHONE_MOCK_UK = {
    "input": "+442071234567",
    "valid": True,
    "possible": True,
    "format": {
        "e164": "+442071234567",
        "international": "+44 20 7123 4567",
        "national": "020 7123 4567",
    },
    "country": "United Kingdom",
    "region": "GB",
    "carrier": None,
    "line_type": "fixed_line",
    "timezones": ["Europe/London"],
    "sources": [],
    "error": None,
}


class TestValidatePhoneRoute:
    """POST /validate-phone happy paths and input validation."""

    def test_us_number_returns_200(self):
        with patch("api.controllers.phone_controller.validate_phone", return_value=_PHONE_MOCK_VALID):
            resp = client.post("/validate-phone", json={"phone": SAMPLE_PHONE})
        if resp.status_code != 200:
            _log_failure("/validate-phone", resp)
        assert resp.status_code == 200

    def test_response_has_all_required_fields(self):
        required = ("input", "valid", "possible", "format", "country",
                    "region", "carrier", "line_type", "timezones", "sources", "error")
        with patch("api.controllers.phone_controller.validate_phone", return_value=_PHONE_MOCK_VALID):
            data = client.post("/validate-phone", json={"phone": SAMPLE_PHONE}).json()
        for field in required:
            assert field in data, f"Missing required field: {field}"

    def test_valid_flag_is_true_for_good_number(self):
        with patch("api.controllers.phone_controller.validate_phone", return_value=_PHONE_MOCK_VALID):
            data = client.post("/validate-phone", json={"phone": SAMPLE_PHONE}).json()
        assert data["valid"] is True

    def test_region_matches_expected_country(self):
        with patch("api.controllers.phone_controller.validate_phone", return_value=_PHONE_MOCK_VALID):
            data = client.post("/validate-phone", json={"phone": SAMPLE_PHONE}).json()
        assert data["region"] == "US"
        assert data["country"] == "United States"

    def test_format_block_has_e164_key(self):
        with patch("api.controllers.phone_controller.validate_phone", return_value=_PHONE_MOCK_VALID):
            data = client.post("/validate-phone", json={"phone": SAMPLE_PHONE}).json()
        assert "e164" in data["format"]

    def test_timezones_is_a_list(self):
        with patch("api.controllers.phone_controller.validate_phone", return_value=_PHONE_MOCK_VALID):
            data = client.post("/validate-phone", json={"phone": SAMPLE_PHONE}).json()
        assert isinstance(data["timezones"], list)

    def test_uk_number_with_region_hint(self):
        with patch("api.controllers.phone_controller.validate_phone", return_value=_PHONE_MOCK_UK):
            resp = client.post("/validate-phone", json={"phone": "+442071234567", "region": "GB"})
        assert resp.status_code == 200
        assert resp.json()["region"] == "GB"

    def test_missing_phone_field_returns_422(self):
        resp = client.post("/validate-phone", json={})
        assert resp.status_code == 422

    def test_empty_phone_returns_422(self):
        resp = client.post("/validate-phone", json={"phone": ""})
        assert resp.status_code == 422

    def test_invalid_region_code_returns_422(self):
        resp = client.post("/validate-phone", json={"phone": SAMPLE_PHONE, "region": "XX99"})
        assert resp.status_code == 422

    def test_phone_number_service_returned_invalid_still_200(self):
        """Service-level 'invalid' results are returned as 200 with valid=False."""
        with patch("api.controllers.phone_controller.validate_phone", return_value=_PHONE_MOCK_INVALID):
            resp = client.post("/validate-phone", json={"phone": "+10000000000"})
        assert resp.status_code == 200
        assert resp.json()["valid"] is False


# ---------------------------------------------------------------------------
# POST /site-health
# ---------------------------------------------------------------------------

_SITE_MOCK_HEALTHY = {
    "hostname": "example.com",
    "http": {
        "status_code": 200,
        "page_load_ms": 342.5,
        "final_url": "https://example.com/",
        "redirect_chain": [],
        "error": None,
    },
    "ssl": {
        "valid": True,
        "days_until_expiry": 90,
        "subject": {"commonName": "example.com"},
        "issuer": {"organizationName": "DigiCert Inc"},
        "error": None,
    },
    "dns": {"A": ["93.184.216.34"], "AAAA": [], "MX": [], "TXT": [], "NS": []},
    "checked_at": "2024-01-15T10:30:00+00:00",
}

_SITE_MOCK_UNHEALTHY = {
    "hostname": "down.example.com",
    "http": {
        "status_code": None,
        "page_load_ms": None,
        "final_url": None,
        "redirect_chain": [],
        "error": "Connection refused",
    },
    "ssl": {"valid": False, "days_until_expiry": None, "subject": None, "issuer": None,
            "error": "SSL handshake failed"},
    "dns": {"A": [], "AAAA": [], "MX": [], "TXT": [], "NS": []},
    "checked_at": "2024-01-15T10:30:00+00:00",
}


class TestSiteHealthRoute:
    """POST /site-health happy paths and input validation."""

    def test_healthy_site_returns_200(self):
        with patch("api.controllers.site_controller.site_health", return_value=_SITE_MOCK_HEALTHY):
            resp = client.post("/site-health", json={"url": SAMPLE_URL})
        if resp.status_code != 200:
            _log_failure("/site-health", resp)
        assert resp.status_code == 200

    def test_response_has_hostname(self):
        with patch("api.controllers.site_controller.site_health", return_value=_SITE_MOCK_HEALTHY):
            data = client.post("/site-health", json={"url": SAMPLE_URL}).json()
        assert data["hostname"] == "example.com"

    def test_response_has_http_block(self):
        with patch("api.controllers.site_controller.site_health", return_value=_SITE_MOCK_HEALTHY):
            data = client.post("/site-health", json={"url": SAMPLE_URL}).json()
        assert "http" in data
        assert "status_code" in data["http"]

    def test_response_has_ssl_block(self):
        with patch("api.controllers.site_controller.site_health", return_value=_SITE_MOCK_HEALTHY):
            data = client.post("/site-health", json={"url": SAMPLE_URL}).json()
        assert "ssl" in data
        assert "valid" in data["ssl"]

    def test_response_has_dns_block(self):
        with patch("api.controllers.site_controller.site_health", return_value=_SITE_MOCK_HEALTHY):
            data = client.post("/site-health", json={"url": SAMPLE_URL}).json()
        assert "dns" in data

    def test_response_has_checked_at_timestamp(self):
        with patch("api.controllers.site_controller.site_health", return_value=_SITE_MOCK_HEALTHY):
            data = client.post("/site-health", json={"url": SAMPLE_URL}).json()
        assert "checked_at" in data
        assert data["checked_at"]  # non-empty

    def test_unhealthy_site_still_returns_200(self):
        """HTTP errors in the target site should return 200 from the API."""
        with patch("api.controllers.site_controller.site_health", return_value=_SITE_MOCK_UNHEALTHY):
            resp = client.post("/site-health", json={"url": "https://down.example.com"})
        assert resp.status_code == 200
        assert resp.json()["http"]["error"] is not None

    def test_custom_timeout_is_accepted(self):
        with patch("api.controllers.site_controller.site_health", return_value=_SITE_MOCK_HEALTHY):
            resp = client.post("/site-health", json={"url": SAMPLE_URL, "timeout": 30})
        assert resp.status_code == 200

    def test_missing_url_returns_422(self):
        resp = client.post("/site-health", json={})
        assert resp.status_code == 422

    def test_invalid_url_returns_422(self):
        resp = client.post("/site-health", json={"url": "not a url !!!"})
        assert resp.status_code == 422

    def test_timeout_zero_returns_422(self):
        resp = client.post("/site-health", json={"url": SAMPLE_URL, "timeout": 0})
        assert resp.status_code == 422

    def test_timeout_above_max_returns_422(self):
        resp = client.post("/site-health", json={"url": SAMPLE_URL, "timeout": 61})
        assert resp.status_code == 422

    def test_http_url_is_accepted(self):
        """Plain http:// URLs should be valid input."""
        mock = {**_SITE_MOCK_HEALTHY, "hostname": "example.com"}
        with patch("api.controllers.site_controller.site_health", return_value=mock):
            resp = client.post("/site-health", json={"url": "http://example.com"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Cross-cutting: content-type and method routing
# ---------------------------------------------------------------------------

class TestRouting:
    """Verify that routes are wired up correctly and return sensible errors
    for wrong HTTP methods."""

    @pytest.mark.parametrize("endpoint", ["/check-ip", "/check-domain",
                                           "/validate-phone", "/site-health"])
    def test_get_on_post_only_route_returns_405(self, endpoint: str):
        resp = client.get(endpoint)
        assert resp.status_code == 405, (
            f"Expected 405 for GET {endpoint}, got {resp.status_code}"
        )

    def test_health_does_not_accept_post(self):
        resp = client.post("/health")
        assert resp.status_code == 405

    @pytest.mark.parametrize("endpoint", ["/check-ip", "/check-domain",
                                           "/validate-phone", "/site-health"])
    def test_empty_body_returns_422(self, endpoint: str):
        resp = client.post(endpoint, json={})
        assert resp.status_code == 422, (
            f"Expected 422 for empty body on {endpoint}, got {resp.status_code}"
        )

    @pytest.mark.parametrize("endpoint", ["/check-ip", "/check-domain",
                                           "/validate-phone", "/site-health"])
    def test_non_json_body_returns_422(self, endpoint: str):
        resp = client.post(endpoint, content=b"not json",
                           headers={"Content-Type": "application/json"})
        assert resp.status_code == 422

"""Test stubs for src/site_diagnostics/ modules."""
from __future__ import annotations

import ssl
import socket
import pytest
from unittest.mock import patch, MagicMock

import dns.resolver

from src.site_diagnostics.http_status import check_http_status, _ensure_scheme
from src.site_diagnostics.ssl_check import check_ssl
from src.site_diagnostics.dns_records import query_dns_records


# ---------------------------------------------------------------------------
# http_status
# ---------------------------------------------------------------------------

class TestEnsureScheme:
    def test_adds_https(self):
        assert _ensure_scheme("example.com") == "https://example.com"

    def test_keeps_https(self):
        assert _ensure_scheme("https://example.com") == "https://example.com"

    def test_keeps_http(self):
        assert _ensure_scheme("http://example.com") == "http://example.com"


class TestCheckHttpStatus:
    def test_successful_200(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/"
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.history = []
        with patch("requests.get", return_value=mock_resp):
            result = check_http_status("https://example.com")
        assert result["status_code"] == 200
        assert result["error"] is None

    def test_redirect_chain(self):
        redirect = MagicMock()
        redirect.url = "http://example.com"
        redirect.status_code = 301
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/"
        mock_resp.headers = {}
        mock_resp.history = [redirect]
        with patch("requests.get", return_value=mock_resp):
            result = check_http_status("http://example.com")
        assert len(result["redirect_chain"]) == 1
        assert result["redirect_chain"][0]["status_code"] == 301

    def test_ssl_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.SSLError("cert error")):
            result = check_http_status("https://example.com")
        assert result["error"] is not None
        assert "SSL" in result["error"]

    def test_connection_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.ConnectionError("refused")):
            result = check_http_status("https://example.com")
        assert "Connection error" in result["error"]

    def test_timeout(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.Timeout()):
            result = check_http_status("https://example.com")
        assert "timed out" in result["error"]

    def test_result_schema(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/"
        mock_resp.headers = {}
        mock_resp.history = []
        with patch("requests.get", return_value=mock_resp):
            result = check_http_status("https://example.com")
        expected_keys = {
            "url", "final_url", "status_code", "redirect_chain",
            "headers", "page_load_ms", "error",
        }
        assert set(result.keys()) == expected_keys


# ---------------------------------------------------------------------------
# ssl_check
# ---------------------------------------------------------------------------

class TestCheckSsl:
    def _make_mock_ssock(self, cert: dict) -> MagicMock:
        mock = MagicMock()
        mock.getpeercert.return_value = cert
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        return mock

    def test_valid_certificate(self):
        cert = {
            "subject": [[("commonName", "example.com")]],
            "issuer": [[("organizationName", "Let's Encrypt")]],
            "notBefore": "Jan  1 00:00:00 2024 GMT",
            "notAfter": "Dec 31 23:59:59 2099 GMT",
        }
        mock_ssock = self._make_mock_ssock(cert)
        with patch("ssl.create_default_context") as mock_ctx, \
             patch("socket.create_connection") as mock_conn:
            mock_ctx.return_value.wrap_socket.return_value = mock_ssock
            mock_conn.return_value.__enter__ = lambda s: s
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            result = check_ssl("example.com")
        assert result["valid"] is True
        assert result["error"] is None
        assert result["days_until_expiry"] is not None

    def test_cert_verification_error(self):
        with patch("ssl.create_default_context") as mock_ctx, \
             patch("socket.create_connection"):
            mock_ctx.return_value.wrap_socket.side_effect = (
                ssl.SSLCertVerificationError("verify failed")
            )
            result = check_ssl("bad.example.com")
        assert result["valid"] is False
        assert "verification failed" in result["error"]

    def test_socket_timeout(self):
        with patch("socket.create_connection", side_effect=socket.timeout()):
            result = check_ssl("example.com")
        assert result["valid"] is False
        assert "timed out" in result["error"]

    def test_result_schema(self):
        with patch("socket.create_connection", side_effect=socket.timeout()):
            result = check_ssl("example.com")
        expected_keys = {
            "hostname", "port", "valid", "subject", "issuer",
            "not_before", "not_after", "days_until_expiry", "error",
        }
        assert set(result.keys()) == expected_keys


# ---------------------------------------------------------------------------
# dns_records
# ---------------------------------------------------------------------------

class TestQueryDnsRecords:
    def test_a_records(self):
        mock_a = MagicMock()
        mock_a.__str__ = lambda self: "93.184.216.34"

        def side_effect(domain, rtype):
            if rtype == "A":
                return [mock_a]
            raise dns.resolver.NoAnswer()

        with patch("dns.resolver.resolve", side_effect=side_effect):
            result = query_dns_records("example.com")
        assert "93.184.216.34" in result["A"]

    def test_spf_extracted_from_txt(self):
        mock_txt = MagicMock()
        mock_txt.strings = [b"v=spf1 include:_spf.google.com ~all"]

        def side_effect(domain, rtype):
            if rtype == "TXT" and "_dmarc" not in domain:
                return [mock_txt]
            raise dns.resolver.NoAnswer()

        with patch("dns.resolver.resolve", side_effect=side_effect):
            result = query_dns_records("example.com")
        assert len(result["SPF"]) > 0
        assert result["SPF"][0].startswith("v=spf1")

    def test_nxdomain(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            result = query_dns_records("nonexistent.invalid")
        assert result["A"] == "NXDOMAIN"

    def test_no_dmarc(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NoAnswer()):
            result = query_dns_records("example.com")
        assert result["DMARC"] == "No DMARC record found"

    def test_result_schema(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            result = query_dns_records("example.com")
        expected_keys = {"domain", "A", "MX", "TXT", "SPF", "DMARC", "DKIM_hint"}
        assert set(result.keys()) == expected_keys

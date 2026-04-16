"""Unit tests for the website health module."""
import pytest
import ssl
import socket
from unittest.mock import patch, MagicMock

import dns.resolver

from security_toolkit.modules.website_health import (
    _ensure_scheme,
    _check_http,
    _check_ssl,
    _query_dns,
    check_website,
)


MOCK_CONFIG = {
    "api_keys": {},
    "settings": {"timeout": 5},
}


class TestEnsureScheme:
    def test_adds_https_if_missing(self):
        assert _ensure_scheme("example.com") == "https://example.com"

    def test_keeps_https(self):
        assert _ensure_scheme("https://example.com") == "https://example.com"

    def test_keeps_http(self):
        assert _ensure_scheme("http://example.com") == "http://example.com"


class TestCheckHTTP:
    def test_successful_request(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.history = []
        with patch("requests.get", return_value=mock_response):
            result = _check_http("https://example.com", 5)
        assert result["status_code"] == 200
        assert result["error"] is None

    def test_redirect_chain(self):
        redirect = MagicMock()
        redirect.url = "http://example.com"
        redirect.status_code = 301
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com"
        mock_response.headers = {}
        mock_response.history = [redirect]
        with patch("requests.get", return_value=mock_response):
            result = _check_http("http://example.com", 5)
        assert len(result["redirect_chain"]) == 1
        assert result["redirect_chain"][0]["status_code"] == 301

    def test_ssl_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.SSLError("cert error")):
            result = _check_http("https://example.com", 5)
        assert result["error"] is not None
        assert "SSL" in result["error"]

    def test_connection_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.ConnectionError("refused")):
            result = _check_http("https://example.com", 5)
        assert "Connection error" in result["error"]

    def test_timeout(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.Timeout()):
            result = _check_http("https://example.com", 5)
        assert "timed out" in result["error"]


class TestCheckSSL:
    def test_valid_certificate(self):
        mock_cert = {
            "subject": [[("commonName", "example.com")]],
            "issuer": [[("organizationName", "Let's Encrypt")]],
            "notBefore": "Jan  1 00:00:00 2024 GMT",
            "notAfter": "Dec 31 23:59:59 2099 GMT",
        }
        mock_ssock = MagicMock()
        mock_ssock.getpeercert.return_value = mock_cert
        mock_ssock.__enter__ = lambda s: s
        mock_ssock.__exit__ = MagicMock(return_value=False)

        with patch("ssl.create_default_context") as mock_ctx, \
             patch("socket.create_connection") as mock_conn:
            mock_ctx.return_value.wrap_socket.return_value = mock_ssock
            mock_conn.return_value.__enter__ = lambda s: s
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            result = _check_ssl("example.com")
        assert result["valid"] is True
        assert result["error"] is None

    def test_ssl_verification_error(self):
        with patch("ssl.create_default_context") as mock_ctx, \
             patch("socket.create_connection"):
            mock_ctx.return_value.wrap_socket.side_effect = ssl.SSLCertVerificationError("cert verify failed")
            result = _check_ssl("bad-cert.example.com")
        assert result["valid"] is False
        assert result["error"] is not None

    def test_connection_timeout(self):
        with patch("socket.create_connection", side_effect=socket.timeout()):
            result = _check_ssl("example.com")
        assert result["valid"] is False
        assert "timed out" in result["error"]


class TestQueryDNS:
    def test_query_dns_a_records(self):
        mock_a = MagicMock()
        mock_a.__str__ = lambda self: "93.184.216.34"

        def side_effect(domain, rtype):
            if rtype == "A":
                return [mock_a]
            raise dns.resolver.NoAnswer()

        with patch("dns.resolver.resolve", side_effect=side_effect):
            result = _query_dns("example.com")
        assert "93.184.216.34" in result["A"]

    def test_query_dns_spf_record(self):
        mock_txt = MagicMock()
        mock_txt.strings = [b"v=spf1 include:_spf.google.com ~all"]

        def side_effect(domain, rtype):
            if rtype == "TXT" and "example" in domain:
                return [mock_txt]
            raise dns.resolver.NoAnswer()

        with patch("dns.resolver.resolve", side_effect=side_effect):
            result = _query_dns("example.com")
        assert len(result["SPF"]) > 0

    def test_query_dns_nxdomain(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            result = _query_dns("nonexistent.example.invalid")
        assert result["A"] == "NXDOMAIN"


class TestCheckWebsite:
    def test_check_website_full(self):
        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 200
        mock_http_resp.url = "https://example.com"
        mock_http_resp.headers = {"Server": "nginx"}
        mock_http_resp.history = []

        mock_cert = {
            "subject": [[("commonName", "example.com")]],
            "issuer": [[("organizationName", "Test CA")]],
            "notBefore": "Jan  1 00:00:00 2024 GMT",
            "notAfter": "Dec 31 23:59:59 2099 GMT",
        }
        mock_ssock = MagicMock()
        mock_ssock.getpeercert.return_value = mock_cert
        mock_ssock.__enter__ = lambda s: s
        mock_ssock.__exit__ = MagicMock(return_value=False)

        with patch("requests.get", return_value=mock_http_resp), \
             patch("ssl.create_default_context") as mock_ctx, \
             patch("socket.create_connection") as mock_conn, \
             patch("dns.resolver.resolve", side_effect=dns.resolver.NoAnswer()):
            mock_ctx.return_value.wrap_socket.return_value = mock_ssock
            mock_conn.return_value.__enter__ = lambda s: s
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            result = check_website("https://example.com", MOCK_CONFIG)

        assert result["hostname"] == "example.com"
        assert result["http"]["status_code"] == 200
        assert result["ssl"]["valid"] is True
        assert "checked_at" in result

    def test_check_website_rejects_private_ip(self):
        result = check_website("http://127.0.0.1/", MOCK_CONFIG)
        assert result["error"] is not None
        assert result["http"] is None

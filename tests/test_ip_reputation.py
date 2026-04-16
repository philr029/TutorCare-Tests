"""Unit tests for the IP reputation module."""
import pytest
from unittest.mock import patch, MagicMock

import dns.resolver

from security_toolkit.modules.ip_reputation import (
    _reverse_ip,
    _is_ip,
    _check_dnsbl,
    _check_abuseipdb,
    _check_virustotal,
    check_reputation,
    check_reputation_bulk,
)


MOCK_CONFIG = {
    "api_keys": {"abuseipdb": "", "virustotal": ""},
    "settings": {"timeout": 5},
    "dnsbl_sources": [
        {"name": "Spamhaus ZEN", "host": "zen.spamhaus.org"},
        {"name": "SURBL", "host": "multi.surbl.org"},
    ],
}


class TestHelpers:
    def test_reverse_ip(self):
        assert _reverse_ip("1.2.3.4") == "4.3.2.1"

    def test_is_ip_valid(self):
        assert _is_ip("192.168.1.1") is True
        assert _is_ip("8.8.8.8") is True

    def test_is_ip_domain(self):
        assert _is_ip("example.com") is False
        assert _is_ip("not-an-ip") is False


class TestDNSBL:
    def test_check_dnsbl_listed(self):
        with patch("dns.resolver.resolve") as mock_resolve:
            mock_resolve.return_value = [MagicMock()]
            result = _check_dnsbl("1.2.3.4", "zen.spamhaus.org")
        assert result["listed"] is True

    def test_check_dnsbl_not_listed(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            result = _check_dnsbl("1.2.3.4", "zen.spamhaus.org")
        assert result["listed"] is False

    def test_check_dnsbl_timeout(self):
        with patch("dns.resolver.resolve", side_effect=dns.exception.Timeout()):
            result = _check_dnsbl("1.2.3.4", "zen.spamhaus.org")
        assert result["listed"] is None
        assert "timed out" in result["details"]

    def test_check_dnsbl_no_nameservers(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NoNameservers()):
            result = _check_dnsbl("1.2.3.4", "zen.spamhaus.org")
        assert result["listed"] is None


class TestAbuseIPDB:
    def test_check_abuseipdb_clean(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"abuseConfidenceScore": 0, "countryCode": "US", "isp": "Google", "totalReports": 0}
        }
        mock_response.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_response):
            result = _check_abuseipdb("8.8.8.8", "fake_key", 5)
        assert result["listed"] is False

    def test_check_abuseipdb_listed(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"abuseConfidenceScore": 90, "countryCode": "XX", "isp": "Bad ISP", "totalReports": 50}
        }
        mock_response.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_response):
            result = _check_abuseipdb("1.2.3.4", "fake_key", 5)
        assert result["listed"] is True

    def test_check_abuseipdb_request_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.RequestException("network error")):
            result = _check_abuseipdb("1.2.3.4", "fake_key", 5)
        assert result["listed"] is None


class TestVirusTotal:
    def test_check_virustotal_clean(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"attributes": {"last_analysis_stats": {"malicious": 0, "harmless": 70}}}
        }
        mock_response.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_response):
            result = _check_virustotal("8.8.8.8", "fake_vt_key", 5)
        assert result["listed"] is False

    def test_check_virustotal_domain(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"attributes": {"last_analysis_stats": {"malicious": 3, "harmless": 67}}}
        }
        mock_response.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_response):
            result = _check_virustotal("evil.com", "fake_vt_key", 5)
        assert result["listed"] is True


class TestCheckReputation:
    def test_check_reputation_ip_no_apis(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            result = check_reputation("8.8.8.8", MOCK_CONFIG)
        assert result["input"] == "8.8.8.8"
        assert result["listed"] is False
        assert isinstance(result["sources"], list)

    def test_check_reputation_domain_resolved(self):
        mock_a = MagicMock()
        mock_a.__str__ = lambda self: "93.184.216.34"

        def side_effect(query, rtype):
            if rtype == "A" and "example.com" in query:
                return [mock_a]
            raise dns.resolver.NXDOMAIN()

        with patch("dns.resolver.resolve", side_effect=side_effect):
            result = check_reputation("example.com", MOCK_CONFIG)
        assert result["input"] == "example.com"
        assert result["resolved_ip"] is not None

    def test_check_reputation_bulk(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            results = check_reputation_bulk(["8.8.8.8", "1.1.1.1"], MOCK_CONFIG)
        assert len(results) == 2
        assert results[0]["input"] == "8.8.8.8"
        assert results[1]["input"] == "1.1.1.1"

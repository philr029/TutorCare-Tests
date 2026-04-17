"""Test stubs for src/ip_reputation/check_rbl.py and check_abuseipdb.py."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

import dns.exception
import dns.resolver

from src.ip_reputation.check_rbl import (
    _reverse_ip,
    check_rbl,
    check_rbl_multi,
)
from src.ip_reputation.check_abuseipdb import check_abuseipdb


# ---------------------------------------------------------------------------
# check_rbl helpers
# ---------------------------------------------------------------------------

class TestReverseIP:
    def test_standard_ipv4(self):
        assert _reverse_ip("1.2.3.4") == "4.3.2.1"

    def test_single_octet(self):
        assert _reverse_ip("8.8.8.8") == "8.8.8.8"


class TestCheckRbl:
    def test_listed(self):
        with patch("dns.resolver.resolve", return_value=[MagicMock()]):
            result = check_rbl("1.2.3.4", "zen.spamhaus.org")
        assert result["listed"] is True
        assert result["ip"] == "1.2.3.4"
        assert result["dnsbl"] == "zen.spamhaus.org"

    def test_clean(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            result = check_rbl("8.8.8.8", "zen.spamhaus.org")
        assert result["listed"] is False

    def test_timeout(self):
        with patch("dns.resolver.resolve", side_effect=dns.exception.Timeout()):
            result = check_rbl("1.2.3.4", "zen.spamhaus.org")
        assert result["listed"] is None
        assert "timed out" in result["details"]

    def test_no_nameservers(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NoNameservers()):
            result = check_rbl("1.2.3.4", "zen.spamhaus.org")
        assert result["listed"] is None

    def test_result_schema(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            result = check_rbl("8.8.8.8", "zen.spamhaus.org")
        assert set(result.keys()) == {"ip", "dnsbl", "listed", "details"}


class TestCheckRblMulti:
    def test_returns_list_per_dnsbl(self):
        hosts = ["zen.spamhaus.org", "multi.surbl.org"]
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            results = check_rbl_multi("8.8.8.8", hosts)
        assert len(results) == 2
        assert all(r["ip"] == "8.8.8.8" for r in results)

    def test_empty_hosts(self):
        results = check_rbl_multi("8.8.8.8", [])
        assert results == []


# ---------------------------------------------------------------------------
# check_abuseipdb
# ---------------------------------------------------------------------------

class TestCheckAbuseIPDB:
    def _mock_response(self, score: int) -> MagicMock:
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {
            "data": {
                "abuseConfidenceScore": score,
                "countryCode": "US",
                "isp": "Test ISP",
                "totalReports": score,
            }
        }
        return resp

    def test_clean_ip(self):
        with patch("requests.get", return_value=self._mock_response(0)):
            result = check_abuseipdb("8.8.8.8", "fake_key", timeout=5)
        assert result["listed"] is False
        assert result["abuse_confidence_score"] == 0
        assert result["error"] is None

    def test_malicious_ip(self):
        with patch("requests.get", return_value=self._mock_response(87)):
            result = check_abuseipdb("1.2.3.4", "fake_key", timeout=5)
        assert result["listed"] is True
        assert result["abuse_confidence_score"] == 87

    def test_no_api_key(self):
        result = check_abuseipdb("8.8.8.8", "", timeout=5)
        assert result["listed"] is None
        assert result["error"] is not None

    def test_request_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.RequestException("network error")):
            result = check_abuseipdb("1.2.3.4", "fake_key", timeout=5)
        assert result["listed"] is None
        assert "error" in result

    def test_result_schema(self):
        with patch("requests.get", return_value=self._mock_response(0)):
            result = check_abuseipdb("8.8.8.8", "fake_key", timeout=5)
        expected_keys = {
            "ip", "source", "listed", "abuse_confidence_score",
            "country_code", "isp", "total_reports", "error",
        }
        assert set(result.keys()) == expected_keys

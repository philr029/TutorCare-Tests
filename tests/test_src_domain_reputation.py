"""Test stubs for src/domain_reputation/check_dnsbl.py."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

import dns.exception
import dns.resolver

from src.domain_reputation.check_dnsbl import (
    check_domain_dnsbl,
    _resolve_domain,
    _check_domain_in_dbl,
)


class TestResolveDomain:
    def test_resolves_to_ip(self):
        mock_a = MagicMock()
        mock_a.__str__ = lambda self: "93.184.216.34"
        with patch("dns.resolver.resolve", return_value=[mock_a]):
            ips = _resolve_domain("example.com")
        assert "93.184.216.34" in ips

    def test_returns_empty_on_failure(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            ips = _resolve_domain("nxdomain.invalid")
        assert ips == []


class TestCheckDomainInDBL:
    def test_listed_domain(self):
        with patch("dns.resolver.resolve", return_value=[MagicMock()]):
            result = _check_domain_in_dbl("spammy.example")
        assert result["status"] == "listed"

    def test_clean_domain(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            result = _check_domain_in_dbl("example.com")
        assert result["status"] == "clean"

    def test_timeout(self):
        with patch("dns.resolver.resolve", side_effect=dns.exception.Timeout()):
            result = _check_domain_in_dbl("example.com")
        assert result["status"] == "unknown"


class TestCheckDomainDnsbl:
    def test_clean_domain_no_ips(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            result = check_domain_dnsbl("nxdomain.invalid")
        assert result["domain"] == "nxdomain.invalid"
        assert result["listed"] is False
        assert isinstance(result["sources"], list)

    def test_result_schema(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            result = check_domain_dnsbl("example.com")
        assert set(result.keys()) == {"domain", "resolved_ips", "listed", "sources"}

    def test_with_resolved_ip(self):
        mock_a = MagicMock()
        mock_a.__str__ = lambda self: "1.2.3.4"

        call_count = {"n": 0}

        def side_effect(query, rtype):
            call_count["n"] += 1
            if rtype == "A" and "example.com" in query:
                return [mock_a]
            raise dns.resolver.NXDOMAIN()

        with patch("dns.resolver.resolve", side_effect=side_effect):
            result = check_domain_dnsbl("example.com", ["zen.spamhaus.org"])
        assert result["resolved_ips"] == ["1.2.3.4"]
        assert len(result["sources"]) >= 2  # DBL + at least one IP check

    def test_default_dnsbl_hosts(self):
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            result = check_domain_dnsbl("example.com")
        assert isinstance(result["sources"], list)

"""Test stubs for src/phone_validation/validate_number.py."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

import phonenumbers

from src.phone_validation.validate_number import (
    _format_variants,
    _line_type_label,
    _enrich_numverify,
    _enrich_twilio,
    validate_number,
)

_NO_API_CONFIG: dict = {
    "api_keys": {"numverify": "", "twilio_sid": "", "twilio_token": ""},
    "settings": {"timeout": 5},
}


class TestFormatVariants:
    def test_us_number_formats(self):
        parsed = phonenumbers.parse("+14155552671")
        fmt = _format_variants(parsed)
        assert fmt["e164"] == "+14155552671"
        assert "415" in fmt["international"]
        assert "415" in fmt["national"]

    def test_gb_number_formats(self):
        parsed = phonenumbers.parse("+441234567890")
        fmt = _format_variants(parsed)
        assert fmt["e164"] == "+441234567890"


class TestLineTypeLabel:
    def test_mobile(self):
        assert _line_type_label(phonenumbers.PhoneNumberType.MOBILE) == "mobile"

    def test_landline(self):
        assert _line_type_label(phonenumbers.PhoneNumberType.FIXED_LINE) == "landline"

    def test_voip(self):
        assert _line_type_label(phonenumbers.PhoneNumberType.VOIP) == "voip"

    def test_unknown_type(self):
        assert _line_type_label(99) == "unknown"


class TestEnrichNumverify:
    def test_success(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "valid": True, "carrier": "AT&T", "line_type": "mobile", "location": "CA",
        }
        with patch("requests.get", return_value=mock_resp):
            result = _enrich_numverify("+14155552671", "fake_key", 5)
        assert result["carrier"] == "AT&T"
        assert result["line_type"] == "mobile"

    def test_request_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.RequestException("timeout")):
            result = _enrich_numverify("+14155552671", "fake_key", 5)
        assert "error" in result


class TestEnrichTwilio:
    def test_success(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "carrier": {"name": "Verizon", "type": "mobile"},
            "country_code": "US",
        }
        with patch("requests.get", return_value=mock_resp):
            result = _enrich_twilio("+14155552671", "ACfake", "token", 5)
        assert result["carrier"] == "Verizon"
        assert result["line_type"] == "mobile"

    def test_request_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.RequestException("auth")):
            result = _enrich_twilio("+14155552671", "ACfake", "token", 5)
        assert "error" in result


class TestValidateNumber:
    def test_valid_us_number(self):
        result = validate_number("+14155552671", config=_NO_API_CONFIG)
        assert result["valid"] is True
        assert result["region"] == "US"
        assert result["error"] is None

    def test_invalid_number(self):
        result = validate_number("not-a-number", config=_NO_API_CONFIG)
        assert result["valid"] is False
        assert result["error"] is not None

    def test_gb_number_with_region_hint(self):
        result = validate_number("02071234567", region="GB", config=_NO_API_CONFIG)
        assert result["valid"] is True
        assert result["region"] == "GB"

    def test_timezones_returned(self):
        result = validate_number("+14155552671", config=_NO_API_CONFIG)
        assert isinstance(result["timezones"], list)
        assert len(result["timezones"]) > 0

    def test_no_network_calls_without_api_keys(self):
        with patch("requests.get") as mock_get:
            validate_number("+14155552671", config=_NO_API_CONFIG)
        mock_get.assert_not_called()

    def test_result_schema(self):
        result = validate_number("+14155552671", config=_NO_API_CONFIG)
        expected_keys = {
            "input", "valid", "possible", "format", "country", "region",
            "carrier", "line_type", "timezones", "sources", "error",
        }
        assert set(result.keys()) == expected_keys

"""Unit tests for the phone validation module."""
import pytest
from unittest.mock import patch, MagicMock

from security_toolkit.modules.phone_validation import (
    _format_phone,
    _line_type_name,
    _check_numverify,
    _check_twilio,
    validate_phone,
)
import phonenumbers


MOCK_CONFIG = {
    "api_keys": {"numverify": "", "twilio_sid": "", "twilio_token": ""},
    "settings": {"timeout": 5},
}


class TestHelpers:
    def test_format_phone(self):
        number = phonenumbers.parse("+14155552671")
        fmt = _format_phone(number)
        assert fmt["e164"] == "+14155552671"
        assert "international" in fmt
        assert "national" in fmt

    def test_line_type_name_mobile(self):
        assert _line_type_name(phonenumbers.PhoneNumberType.MOBILE) == "mobile"

    def test_line_type_name_landline(self):
        assert _line_type_name(phonenumbers.PhoneNumberType.FIXED_LINE) == "landline"

    def test_line_type_name_voip(self):
        assert _line_type_name(phonenumbers.PhoneNumberType.VOIP) == "voip"

    def test_line_type_name_unknown(self):
        assert _line_type_name(phonenumbers.PhoneNumberType.UNKNOWN) == "unknown"


class TestNumverify:
    def test_check_numverify_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "valid": True,
            "carrier": "AT&T",
            "line_type": "mobile",
            "location": "California",
        }
        mock_response.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_response):
            result = _check_numverify("+14155552671", "fake_key", 5)
        assert result["carrier"] == "AT&T"
        assert result["line_type"] == "mobile"

    def test_check_numverify_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.RequestException("network error")):
            result = _check_numverify("+14155552671", "fake_key", 5)
        assert "error" in result


class TestTwilio:
    def test_check_twilio_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "carrier": {"name": "Verizon", "type": "mobile"},
            "country_code": "US",
        }
        mock_response.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_response):
            result = _check_twilio("+14155552671", "ACfake", "fake_token", 5)
        assert result["carrier"] == "Verizon"
        assert result["line_type"] == "mobile"

    def test_check_twilio_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.RequestException("auth error")):
            result = _check_twilio("+14155552671", "ACfake", "fake_token", 5)
        assert "error" in result


class TestValidatePhone:
    def test_validate_valid_us_number(self):
        result = validate_phone("+14155552671", config=MOCK_CONFIG)
        assert result["valid"] is True
        assert result["region"] == "US"
        assert result["format"]["e164"] == "+14155552671"
        assert result["error"] is None

    def test_validate_invalid_number(self):
        result = validate_phone("not-a-phone", config=MOCK_CONFIG)
        assert result["valid"] is False
        assert result["error"] is not None

    def test_validate_uk_number(self):
        result = validate_phone("+441234567890", config=MOCK_CONFIG)
        assert result["valid"] is True
        assert result["region"] == "GB"

    def test_validate_with_region_hint(self):
        result = validate_phone("02071234567", region="GB", config=MOCK_CONFIG)
        assert result["valid"] is True
        assert result["region"] == "GB"

    def test_validate_returns_timezones(self):
        result = validate_phone("+14155552671", config=MOCK_CONFIG)
        assert isinstance(result["timezones"], list)
        assert len(result["timezones"]) > 0

    def test_validate_no_call_ping_probe(self):
        """Ensure no actual network requests are made during libphonenumber validation."""
        with patch("requests.get") as mock_get:
            validate_phone("+14155552671", config=MOCK_CONFIG)
            mock_get.assert_not_called()

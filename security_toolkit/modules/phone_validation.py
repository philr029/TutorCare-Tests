"""Phone number validation module (legal & non-intrusive)."""
from __future__ import annotations

from typing import Any, Dict, Optional

import phonenumbers
from phonenumbers import geocoder, carrier, timezone

import requests

from ..utils.config_loader import load_config
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def _format_phone(number: phonenumbers.PhoneNumber) -> Dict[str, str]:
    return {
        "e164": phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164),
        "international": phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        "national": phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.NATIONAL),
    }


def _line_type_name(number_type: int) -> str:
    types = {
        phonenumbers.PhoneNumberType.FIXED_LINE: "landline",
        phonenumbers.PhoneNumberType.MOBILE: "mobile",
        phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
        phonenumbers.PhoneNumberType.TOLL_FREE: "toll_free",
        phonenumbers.PhoneNumberType.PREMIUM_RATE: "premium_rate",
        phonenumbers.PhoneNumberType.SHARED_COST: "shared_cost",
        phonenumbers.PhoneNumberType.VOIP: "voip",
        phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "personal_number",
        phonenumbers.PhoneNumberType.PAGER: "pager",
        phonenumbers.PhoneNumberType.UAN: "uan",
        phonenumbers.PhoneNumberType.VOICEMAIL: "voicemail",
        phonenumbers.PhoneNumberType.UNKNOWN: "unknown",
    }
    return types.get(number_type, "unknown")


def _check_numverify(phone_e164: str, api_key: str, timeout: int) -> Dict[str, Any]:
    """Query Numverify API for carrier and line-type data."""
    url = "https://apilayer.net/api/validate"
    params = {"access_key": api_key, "number": phone_e164, "format": 1}
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return {
            "source": "Numverify",
            "carrier": data.get("carrier"),
            "line_type": data.get("line_type"),
            "location": data.get("location"),
            "valid": data.get("valid", False),
        }
    except requests.RequestException as exc:
        logger.warning("Numverify query failed: %s", exc)
        return {"source": "Numverify", "error": str(exc)}


def _check_twilio(phone_e164: str, account_sid: str, auth_token: str, timeout: int) -> Dict[str, Any]:
    """Query Twilio Lookup API for carrier and line-type data."""
    url = f"https://lookups.twilio.com/v1/PhoneNumbers/{phone_e164}"
    params = {"Type": "carrier"}
    try:
        resp = requests.get(url, params=params, auth=(account_sid, auth_token), timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        carrier_info = data.get("carrier", {})
        return {
            "source": "Twilio",
            "carrier": carrier_info.get("name"),
            "line_type": carrier_info.get("type"),
            "country_code": data.get("country_code"),
        }
    except requests.RequestException as exc:
        logger.warning("Twilio lookup failed: %s", exc)
        return {"source": "Twilio", "error": str(exc)}


def validate_phone(phone_input: str, region: Optional[str] = None, config: Optional[dict] = None) -> Dict[str, Any]:
    """
    Validate a phone number using libphonenumber and optional APIs.

    Args:
        phone_input: Phone number string (e.g. "+14155552671" or "0207 123 4567").
        region: Default region hint (e.g. "US", "GB").
        config: Optional config dict.

    Returns:
        Structured dict with validation results. NO calls, pings, or probes are made.
    """
    if config is None:
        config = load_config()

    settings = config.get("settings", {})
    api_keys = config.get("api_keys", {})
    timeout = settings.get("timeout", 10)

    result: Dict[str, Any] = {
        "input": phone_input,
        "valid": False,
        "format": None,
        "country": None,
        "region": None,
        "carrier": None,
        "line_type": None,
        "timezones": None,
        "sources": [],
        "error": None,
    }

    try:
        parsed = phonenumbers.parse(phone_input, region)
    except phonenumbers.NumberParseException as exc:
        result["error"] = f"Parse error: {exc}"
        return result

    is_valid = phonenumbers.is_valid_number(parsed)
    is_possible = phonenumbers.is_possible_number(parsed)
    result["valid"] = is_valid
    result["possible"] = is_possible
    result["format"] = _format_phone(parsed)

    region_code = phonenumbers.region_code_for_number(parsed)
    result["region"] = region_code
    result["country"] = geocoder.description_for_number(parsed, "en")
    result["carrier"] = carrier.name_for_number(parsed, "en") or None
    result["line_type"] = _line_type_name(phonenumbers.number_type(parsed))
    result["timezones"] = list(timezone.time_zones_for_number(parsed))

    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    # Numverify
    numverify_key = api_keys.get("numverify", "")
    if numverify_key:
        nv = _check_numverify(e164, numverify_key, timeout)
        result["sources"].append(nv)
        if not result["carrier"] and nv.get("carrier"):
            result["carrier"] = nv["carrier"]
        if nv.get("line_type"):
            result["line_type"] = nv["line_type"]

    # Twilio
    twilio_sid = api_keys.get("twilio_sid", "")
    twilio_token = api_keys.get("twilio_token", "")
    if twilio_sid and twilio_token:
        tw = _check_twilio(e164, twilio_sid, twilio_token, timeout)
        result["sources"].append(tw)
        if not result["carrier"] and tw.get("carrier"):
            result["carrier"] = tw["carrier"]
        if tw.get("line_type"):
            result["line_type"] = tw["line_type"]

    return result

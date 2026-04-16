"""Phone number validation module (offline + optional API enrichment).

Uses Google's ``libphonenumber`` library for offline parsing and validation.
Optionally enriches results with carrier and line-type data from the
Numverify or Twilio Lookup APIs when API keys are present in the config.

**No calls, pings, or probes are ever made to the phone number itself.**

Usage
-----
    from src.phone_validation.validate_number import validate_number

    result = validate_number("+14155552671")
    print(result["valid"])       # True
    print(result["country"])     # "United States"
    print(result["line_type"])   # "fixed_line_or_mobile"

    # With region hint for numbers without country code
    result = validate_number("02071234567", region="GB")
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
import phonenumbers
from phonenumbers import carrier, geocoder, timezone

from src.utils.logger import get_logger

logger = get_logger(__name__)


def _format_variants(number: phonenumbers.PhoneNumber) -> Dict[str, str]:
    """Return E.164, international, and national format strings."""
    return {
        "e164": phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164),
        "international": phonenumbers.format_number(
            number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        ),
        "national": phonenumbers.format_number(
            number, phonenumbers.PhoneNumberFormat.NATIONAL
        ),
    }


def _line_type_label(number_type: int) -> str:
    """Convert a :class:`phonenumbers.PhoneNumberType` int to a readable label."""
    _map = {
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
    return _map.get(number_type, "unknown")


def _enrich_numverify(
    e164: str, api_key: str, timeout: int
) -> Dict[str, Any]:
    """Query the Numverify API for carrier and line-type enrichment.

    Args:
        e164:    E.164-formatted phone number.
        api_key: Numverify access key.
        timeout: HTTP timeout in seconds.

    Returns:
        Dict with ``source``, ``carrier``, ``line_type``, ``location``, and
        optionally ``error``.
    """
    # TODO: Handle Numverify error codes (e.g. 101 = invalid API key).
    url = "https://apilayer.net/api/validate"
    params = {"access_key": api_key, "number": e164, "format": 1}
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
        logger.warning("Numverify query failed for %s: %s", e164, exc)
        return {"source": "Numverify", "error": str(exc)}


def _enrich_twilio(
    e164: str, account_sid: str, auth_token: str, timeout: int
) -> Dict[str, Any]:
    """Query the Twilio Lookup v1 API for carrier enrichment.

    Args:
        e164:        E.164-formatted phone number.
        account_sid: Twilio Account SID.
        auth_token:  Twilio Auth Token.
        timeout:     HTTP timeout in seconds.

    Returns:
        Dict with ``source``, ``carrier``, ``line_type``, ``country_code``, and
        optionally ``error``.
    """
    # TODO: Migrate to Twilio Lookup v2 which supports additional data packages.
    url = f"https://lookups.twilio.com/v1/PhoneNumbers/{e164}"
    try:
        resp = requests.get(
            url,
            params={"Type": "carrier"},
            auth=(account_sid, auth_token),
            timeout=timeout,
        )
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
        logger.warning("Twilio lookup failed for %s: %s", e164, exc)
        return {"source": "Twilio", "error": str(exc)}


def validate_number(
    phone_input: str,
    region: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Parse and validate a phone number using Google's libphonenumber.

    Optionally enriches results with carrier/line-type data from Numverify or
    Twilio if API keys are present in *config*.

    **No calls, pings, or probes are ever made to the phone number itself.**

    Args:
        phone_input: Phone number string, e.g. ``"+14155552671"`` or
                     ``"02071234567"``.
        region:      Default region hint (e.g. ``"US"``, ``"GB"``).  Required
                     for numbers without a leading ``+`` country code.
        config:      Configuration dict.  If ``None``, defaults are used (no
                     API enrichment).

    Returns:
        Dictionary with keys:

        - ``input`` – original input string.
        - ``valid`` – ``True`` if the number is a valid, dialable number.
        - ``possible`` – ``True`` if the number has the right length.
        - ``format`` – ``{"e164": ..., "international": ..., "national": ...}``.
        - ``country`` – human-readable country name.
        - ``region`` – ISO 3166-1 alpha-2 region code.
        - ``carrier`` – carrier name if known, else ``null``.
        - ``line_type`` – e.g. ``"mobile"``, ``"landline"``, ``"voip"``.
        - ``timezones`` – list of IANA timezone strings.
        - ``sources`` – list of API enrichment result dicts.
        - ``error`` – parse error message, or ``null`` on success.

    Example output (valid US number)::

        {
          "input": "+14155552671",
          "valid": true,
          "possible": true,
          "format": {
            "e164": "+14155552671",
            "international": "+1 415-555-2671",
            "national": "(415) 555-2671"
          },
          "country": "United States",
          "region": "US",
          "carrier": null,
          "line_type": "fixed_line_or_mobile",
          "timezones": ["America/Los_Angeles"],
          "sources": [],
          "error": null
        }
    """
    if config is None:
        config = {}

    settings = config.get("settings", {})
    api_keys = config.get("api_keys", {})
    timeout: int = settings.get("timeout", 10)

    result: Dict[str, Any] = {
        "input": phone_input,
        "valid": False,
        "possible": False,
        "format": None,
        "country": None,
        "region": None,
        "carrier": None,
        "line_type": None,
        "timezones": None,
        "sources": [],
        "error": None,
    }

    # --- Offline parsing via libphonenumber ---
    try:
        parsed = phonenumbers.parse(phone_input, region)
    except phonenumbers.NumberParseException as exc:
        result["error"] = f"Parse error: {exc}"
        logger.warning("Failed to parse phone number '%s': %s", phone_input, exc)
        return result

    result["valid"] = phonenumbers.is_valid_number(parsed)
    result["possible"] = phonenumbers.is_possible_number(parsed)
    result["format"] = _format_variants(parsed)

    region_code = phonenumbers.region_code_for_number(parsed)
    result["region"] = region_code
    result["country"] = geocoder.description_for_number(parsed, "en")
    result["carrier"] = carrier.name_for_number(parsed, "en") or None
    result["line_type"] = _line_type_label(phonenumbers.number_type(parsed))
    result["timezones"] = list(timezone.time_zones_for_number(parsed))

    logger.info(
        "Parsed phone %s → valid=%s region=%s line_type=%s",
        phone_input,
        result["valid"],
        region_code,
        result["line_type"],
    )

    e164: str = result["format"]["e164"]

    # --- Optional API enrichment ---
    numverify_key = api_keys.get("numverify", "")
    if numverify_key:
        nv = _enrich_numverify(e164, numverify_key, timeout)
        result["sources"].append(nv)
        if not result["carrier"] and nv.get("carrier"):
            result["carrier"] = nv["carrier"]
        if nv.get("line_type"):
            result["line_type"] = nv["line_type"]

    twilio_sid = api_keys.get("twilio_sid", "")
    twilio_token = api_keys.get("twilio_token", "")
    if twilio_sid and twilio_token:
        tw = _enrich_twilio(e164, twilio_sid, twilio_token, timeout)
        result["sources"].append(tw)
        if not result["carrier"] and tw.get("carrier"):
            result["carrier"] = tw["carrier"]
        if tw.get("line_type"):
            result["line_type"] = tw["line_type"]

    return result

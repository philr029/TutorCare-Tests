"""Lightweight Flask web dashboard."""
from __future__ import annotations

from typing import Optional

from flask import Flask, jsonify, render_template, request

from ..modules.ip_reputation import check_reputation
from ..modules.phone_validation import validate_phone
from ..modules.website_health import check_website
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def create_app(config: Optional[dict] = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder="templates")
    if config is None:
        from ..utils.config_loader import load_config
        config = load_config()

    app.config["TOOLKIT_CONFIG"] = config

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/ip", methods=["GET"])
    def api_ip():
        target = request.args.get("target", "")
        if not target:
            return jsonify({"error": "Missing 'target' parameter"}), 400
        try:
            result = check_reputation(target, app.config["TOOLKIT_CONFIG"])
        except Exception:
            logger.exception("Unhandled error in /api/ip")
            return jsonify({"error": "Internal server error"}), 500
        return jsonify(result)

    @app.route("/api/phone", methods=["GET"])
    def api_phone():
        number = request.args.get("number", "")
        region = request.args.get("region")
        if not number:
            return jsonify({"error": "Missing 'number' parameter"}), 400
        try:
            result = validate_phone(number, region, app.config["TOOLKIT_CONFIG"])
        except Exception:
            logger.exception("Unhandled error in /api/phone")
            return jsonify({"error": "Internal server error"}), 500
        return jsonify(result)

    @app.route("/api/website", methods=["GET"])
    def api_website():
        url = request.args.get("url", "")
        if not url:
            return jsonify({"error": "Missing 'url' parameter"}), 400
        try:
            result = check_website(url, app.config["TOOLKIT_CONFIG"])
        except Exception:
            logger.exception("Unhandled error in /api/website")
            return jsonify({"error": "Internal server error"}), 500
        return jsonify(result)

    return app

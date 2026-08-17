from flask import Blueprint, jsonify

from app.services import analytics_service

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics/shipments/summary", methods=["GET"])
def get_summary():
    summary = analytics_service.get_summary()
    return jsonify(summary)


@analytics_bp.route("/analytics/shipments/carrier-performance", methods=["GET"])
def get_carrier_performance():
    result = analytics_service.get_carrier_performance()
    return jsonify(result)

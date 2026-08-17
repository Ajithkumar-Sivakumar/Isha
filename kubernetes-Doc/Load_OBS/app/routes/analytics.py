from flask import Blueprint, jsonify

from app.services import analytics_service

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics", methods=["GET"])
def get_analytics():
    """Get all analytics data"""
    return jsonify({
        "service": "Analytics",
        "endpoints": {
            "summary": "/api/v1/analytics/shipments/summary",
            "carrier_performance": "/api/v1/analytics/shipments/carrier-performance"
        },
        "message": "Use specific endpoints above for analytics data"
    })


@analytics_bp.route("/analytics/shipments/summary", methods=["GET"])
def get_summary():
    summary = analytics_service.get_summary()
    return jsonify(summary)


@analytics_bp.route("/analytics/shipments/carrier-performance", methods=["GET"])
def get_carrier_performance():
    result = analytics_service.get_carrier_performance()
    return jsonify(result)

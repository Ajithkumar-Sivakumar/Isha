from flask import Blueprint, request, jsonify

from app.services import carrier_service
from app.schemas.carrier import CarrierResponseSchema
from app.schemas.shipment import ShipmentSummaryResponseSchema

carriers_bp = Blueprint("carriers", __name__)

_response_schema = CarrierResponseSchema()
_summary_schema = ShipmentSummaryResponseSchema()


@carriers_bp.route("/carriers", methods=["GET"])
def list_carriers():
    active_only = request.args.get("activeOnly", "true").lower() == "true"
    carriers = carrier_service.list_carriers(
        mode=request.args.get("mode"),
        active_only=active_only,
    )
    return jsonify(_response_schema.dump(carriers, many=True))


@carriers_bp.route("/carriers/<carrier_id>", methods=["GET"])
def get_carrier(carrier_id):
    carrier = carrier_service.get_carrier(carrier_id)
    return jsonify(_response_schema.dump(carrier))


@carriers_bp.route("/carriers/<carrier_id>/shipments", methods=["GET"])
def get_carrier_shipments(carrier_id):
    result = carrier_service.get_carrier_shipments(
        carrier_id,
        page=int(request.args.get("page", 0)),
        size=int(request.args.get("size", 20)),
    )
    return jsonify(
        {
            "content": _summary_schema.dump(result["content"], many=True),
            "page": result["page"],
            "size": result["size"],
            "totalElements": result["totalElements"],
            "totalPages": result["totalPages"],
            "last": result["last"],
        }
    )


@carriers_bp.route("/carriers/available", methods=["GET"])
def find_available_carriers():
    mode = request.args.get("mode")
    required_capacity = request.args.get("requiredCapacity", type=float)
    carriers = carrier_service.find_available_carriers(mode, required_capacity)
    return jsonify(_response_schema.dump(carriers, many=True))

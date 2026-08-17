from flask import Blueprint, request, jsonify

from app.services import shipment_service
from app.schemas.shipment import (
    CreateShipmentRequestSchema,
    UpdateShipmentRequestSchema,
    AssignCarrierRequestSchema,
    ShipmentResponseSchema,
    ShipmentSummaryResponseSchema,
)
from app.schemas.tracking_event import (
    CreateTrackingEventRequestSchema,
    TrackingEventResponseSchema,
)

shipments_bp = Blueprint("shipments", __name__)

_create_schema = CreateShipmentRequestSchema()
_update_schema = UpdateShipmentRequestSchema()
_assign_schema = AssignCarrierRequestSchema()
_event_schema = CreateTrackingEventRequestSchema()
_response_schema = ShipmentResponseSchema()
_summary_schema = ShipmentSummaryResponseSchema()
_event_response_schema = TrackingEventResponseSchema()


@shipments_bp.route("/shipments", methods=["POST"])
def create_shipment():
    data = _create_schema.load(request.get_json())
    shipment = shipment_service.create_shipment(data)
    return jsonify(_response_schema.dump(shipment)), 201


@shipments_bp.route("/shipments/<shipment_id>", methods=["GET"])
def get_shipment(shipment_id):
    shipment = shipment_service.get_shipment(shipment_id)
    return jsonify(_response_schema.dump(shipment))


@shipments_bp.route("/shipments", methods=["GET"])
def list_shipments():
    result = shipment_service.list_shipments(
        status=request.args.get("status"),
        customer_id=request.args.get("customerId"),
        carrier_id=request.args.get("carrierId"),
        transport_mode=request.args.get("transportMode"),
        priority=request.args.get("priority"),
        from_date=request.args.get("fromDate"),
        to_date=request.args.get("toDate"),
        page=int(request.args.get("page", 0)),
        size=int(request.args.get("size", 20)),
        sort_by=request.args.get("sortBy", "created_at"),
        sort_dir=request.args.get("sortDir", "desc"),
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


@shipments_bp.route("/shipments/<shipment_id>", methods=["PUT"])
def update_shipment(shipment_id):
    data = _update_schema.load(request.get_json())
    shipment = shipment_service.update_shipment(shipment_id, data)
    return jsonify(_response_schema.dump(shipment))


@shipments_bp.route("/shipments/<shipment_id>", methods=["DELETE"])
def delete_shipment(shipment_id):
    shipment_service.delete_shipment(shipment_id)
    return "", 204


@shipments_bp.route("/shipments/<shipment_id>/assign-carrier", methods=["POST"])
def assign_carrier(shipment_id):
    data = _assign_schema.load(request.get_json())
    shipment = shipment_service.assign_carrier(shipment_id, data["carrier_id"])
    return jsonify(_response_schema.dump(shipment))


@shipments_bp.route("/shipments/<shipment_id>/tracking-events", methods=["POST"])
def create_tracking_event(shipment_id):
    data = _event_schema.load(request.get_json())
    event = shipment_service.record_tracking_event(shipment_id, data)
    return jsonify(_event_response_schema.dump(event)), 201


@shipments_bp.route("/shipments/<shipment_id>/tracking", methods=["GET"])
def get_tracking_events(shipment_id):
    events = shipment_service.get_tracking_events(shipment_id)
    return jsonify(_event_response_schema.dump(events, many=True))

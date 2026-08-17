from flask import Blueprint, request, jsonify

from app.services import customs_service
from app.schemas.customs_declaration import (
    CreateCustomsDeclarationRequestSchema,
    CustomsDeclarationResponseSchema,
)

customs_bp = Blueprint("customs", __name__)

_create_schema = CreateCustomsDeclarationRequestSchema()
_response_schema = CustomsDeclarationResponseSchema()


@customs_bp.route("/shipments/<shipment_id>/customs-declaration", methods=["POST"])
def create_declaration(shipment_id):
    data = _create_schema.load(request.get_json())
    declaration = customs_service.create_declaration(shipment_id, data)
    return jsonify(_response_schema.dump(declaration)), 201


@customs_bp.route("/shipments/<shipment_id>/customs-declaration", methods=["GET"])
def get_declaration(shipment_id):
    declaration = customs_service.get_declaration(shipment_id)
    return jsonify(_response_schema.dump(declaration))


@customs_bp.route("/customs-declarations/<declaration_id>/submit", methods=["POST"])
def submit_declaration(declaration_id):
    declaration = customs_service.submit_declaration(declaration_id)
    return jsonify(_response_schema.dump(declaration))


@customs_bp.route("/customs-declarations/<declaration_id>/approve", methods=["POST"])
def approve_declaration(declaration_id):
    declaration = customs_service.approve_declaration(declaration_id)
    return jsonify(_response_schema.dump(declaration))


@customs_bp.route("/customs-declarations/<declaration_id>/reject", methods=["POST"])
def reject_declaration(declaration_id):
    reason = request.args.get("reason", "")
    declaration = customs_service.reject_declaration(declaration_id, reason)
    return jsonify(_response_schema.dump(declaration))

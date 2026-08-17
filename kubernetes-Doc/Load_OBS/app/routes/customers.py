from flask import Blueprint, request, jsonify

from app.services import customer_service
from app.schemas.customer import CreateCustomerRequestSchema, CustomerResponseSchema
from app.schemas.shipment import ShipmentSummaryResponseSchema

customers_bp = Blueprint("customers", __name__)

_create_schema = CreateCustomerRequestSchema()
_response_schema = CustomerResponseSchema()
_summary_schema = ShipmentSummaryResponseSchema()


@customers_bp.route("/customers", methods=["POST"])
def create_customer():
    data = _create_schema.load(request.get_json())
    customer = customer_service.create_customer(data)
    return jsonify(_response_schema.dump(customer)), 201


@customers_bp.route("/customers/<customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = customer_service.get_customer(customer_id)
    return jsonify(_response_schema.dump(customer))


@customers_bp.route("/customers", methods=["GET"])
def list_customers():
    result = customer_service.list_customers(
        search=request.args.get("search"),
        page=int(request.args.get("page", 0)),
        size=int(request.args.get("size", 20)),
    )
    return jsonify(
        {
            "content": _response_schema.dump(result["content"], many=True),
            "page": result["page"],
            "size": result["size"],
            "totalElements": result["totalElements"],
            "totalPages": result["totalPages"],
            "last": result["last"],
        }
    )


@customers_bp.route("/customers/<customer_id>/status", methods=["PATCH"])
def update_customer_status(customer_id):
    status = request.args.get("status")
    customer = customer_service.update_customer_status(customer_id, status)
    return jsonify(_response_schema.dump(customer))


@customers_bp.route("/customers/<customer_id>/shipments", methods=["GET"])
def get_customer_shipments(customer_id):
    result = customer_service.get_customer_shipments(
        customer_id,
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

from flask import Blueprint, request, jsonify

from app.models import Port
from app.enums import PortType
from app.schemas.port import PortResponseSchema
from app.exceptions import ResourceNotFoundException

ports_bp = Blueprint("ports", __name__)

_response_schema = PortResponseSchema()


@ports_bp.route("/ports", methods=["GET"])
def list_ports():
    query = Port.query

    port_type = request.args.get("type")
    if port_type:
        query = query.filter(Port.type == PortType(port_type.upper()))

    country = request.args.get("country")
    if country:
        query = query.filter(Port.country == country)

    ports = query.all()
    return jsonify(_response_schema.dump(ports, many=True))


@ports_bp.route("/ports/<port_id>", methods=["GET"])
def get_port(port_id):
    from app.extensions import db

    port = db.session.get(Port, port_id)
    if not port:
        raise ResourceNotFoundException("Port", port_id)
    return jsonify(_response_schema.dump(port))

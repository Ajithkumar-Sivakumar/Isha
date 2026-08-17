from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import Route, Port
from app.enums import TransportMode
from app.schemas.route import RouteResponseSchema
from app.exceptions import ResourceNotFoundException

routes_bp = Blueprint("routes_resource", __name__)

_response_schema = RouteResponseSchema()


@routes_bp.route("/routes", methods=["GET"])
def list_routes():
    query = Route.query

    origin_code = request.args.get("origin")
    if origin_code:
        query = query.join(Port, Route.origin_id == Port.id).filter(
            Port.code == origin_code
        )

    destination_code = request.args.get("destination")
    if destination_code:
        dest_port = db.aliased(Port)
        query = query.join(dest_port, Route.destination_id == dest_port.id).filter(
            dest_port.code == destination_code
        )

    mode = request.args.get("mode")
    if mode:
        query = query.filter(Route.transport_mode == TransportMode(mode.upper()))

    routes = query.all()
    return jsonify(_response_schema.dump(routes, many=True))


@routes_bp.route("/routes/<route_id>", methods=["GET"])
def get_route(route_id):
    route = db.session.get(Route, route_id)
    if not route:
        raise ResourceNotFoundException("Route", route_id)
    return jsonify(_response_schema.dump(route))

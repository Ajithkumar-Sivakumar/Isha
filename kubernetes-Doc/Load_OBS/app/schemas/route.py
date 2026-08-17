from marshmallow import fields

from app.schemas.common import CamelCaseSchema


class RouteResponseSchema(CamelCaseSchema):
    id = fields.UUID()
    origin_port_name = fields.Method("get_origin_name")
    origin_port_code = fields.Method("get_origin_code")
    destination_port_name = fields.Method("get_destination_name")
    destination_port_code = fields.Method("get_destination_code")
    transport_mode = fields.Method("get_transport_mode")
    estimated_transit_days = fields.Integer()
    distance_km = fields.Decimal(as_string=True)
    is_active = fields.Boolean()

    def get_origin_name(self, obj):
        return obj.origin.name if obj.origin else None

    def get_origin_code(self, obj):
        return obj.origin.code if obj.origin else None

    def get_destination_name(self, obj):
        return obj.destination.name if obj.destination else None

    def get_destination_code(self, obj):
        return obj.destination.code if obj.destination else None

    def get_transport_mode(self, obj):
        return obj.transport_mode.value if obj.transport_mode else None

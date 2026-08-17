from decimal import Decimal

from marshmallow import fields, post_dump

from app.schemas.common import CamelCaseSchema


class CarrierResponseSchema(CamelCaseSchema):
    id = fields.UUID()
    name = fields.String()
    code = fields.String()
    transport_modes = fields.Method("get_transport_modes")
    max_capacity_kg = fields.Decimal(as_string=True)
    current_load_kg = fields.Decimal(as_string=True)
    available_capacity_kg = fields.Method("get_available_capacity")
    utilization_percent = fields.Method("get_utilization")
    rating = fields.Decimal(as_string=True)
    contact_email = fields.String()
    is_active = fields.Boolean()

    def get_transport_modes(self, obj):
        return obj.transport_modes

    def get_available_capacity(self, obj):
        avail = Decimal(str(obj.max_capacity_kg)) - Decimal(str(obj.current_load_kg))
        return str(avail)

    def get_utilization(self, obj):
        if obj.max_capacity_kg and Decimal(str(obj.max_capacity_kg)) > 0:
            util = (Decimal(str(obj.current_load_kg)) / Decimal(str(obj.max_capacity_kg))) * 100
            return str(round(util, 4))
        return "0"

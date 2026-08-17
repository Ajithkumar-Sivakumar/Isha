from marshmallow import fields

from app.schemas.common import CamelCaseSchema


class PortResponseSchema(CamelCaseSchema):
    id = fields.UUID()
    name = fields.String()
    code = fields.String()
    type = fields.Method("get_type")
    city = fields.String()
    country = fields.String()
    timezone = fields.String()
    latitude = fields.Float()
    longitude = fields.Float()

    def get_type(self, obj):
        return obj.type.value if obj.type else None

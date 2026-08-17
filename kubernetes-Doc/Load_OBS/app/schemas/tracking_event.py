from marshmallow import fields, validate

from app.schemas.common import CamelCaseSchema


class CreateTrackingEventRequestSchema(CamelCaseSchema):
    status = fields.String(required=True)
    location = fields.String(required=True, validate=validate.Length(max=300))
    notes = fields.String()
    reported_by = fields.String(required=True)
    occurred_at = fields.DateTime(required=True)


class TrackingEventResponseSchema(CamelCaseSchema):
    id = fields.UUID()
    shipment_id = fields.UUID()
    status = fields.Method("get_status")
    location = fields.String()
    notes = fields.String()
    reported_by = fields.String()
    occurred_at = fields.DateTime()
    created_at = fields.DateTime()

    def get_status(self, obj):
        return obj.status.value if obj.status else None

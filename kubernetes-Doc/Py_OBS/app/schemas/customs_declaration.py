from marshmallow import fields, validate

from app.schemas.common import CamelCaseSchema


class CreateCustomsDeclarationRequestSchema(CamelCaseSchema):
    declaration_type = fields.String(
        required=True,
        validate=validate.OneOf(["IMPORT", "EXPORT", "TRANSIT"]),
    )
    total_declared_value = fields.Decimal(
        required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False)
    )
    currency = fields.String(load_default="USD", validate=validate.Length(equal=3))


class CustomsDeclarationResponseSchema(CamelCaseSchema):
    id = fields.UUID()
    shipment_id = fields.UUID()
    declaration_number = fields.String()
    declaration_type = fields.String()
    status = fields.Method("get_status")
    total_declared_value = fields.Decimal(as_string=True)
    currency = fields.String()
    duty_amount = fields.Decimal(as_string=True)
    tax_amount = fields.Decimal(as_string=True)
    rejection_reason = fields.String()
    submitted_at = fields.DateTime()
    cleared_at = fields.DateTime()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    def get_status(self, obj):
        return obj.status.value if obj.status else None

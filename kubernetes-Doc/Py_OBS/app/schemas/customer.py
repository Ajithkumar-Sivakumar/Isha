from marshmallow import fields, validate

from app.schemas.common import CamelCaseSchema


class CreateCustomerRequestSchema(CamelCaseSchema):
    company_name = fields.String(required=True, validate=validate.Length(max=200))
    contact_name = fields.String(required=True, validate=validate.Length(max=100))
    contact_email = fields.Email(required=True)
    contact_phone = fields.String(validate=validate.Length(max=20))
    street = fields.String(required=True)
    city = fields.String(required=True)
    state = fields.String(required=True)
    country = fields.String(required=True)
    postal_code = fields.String()
    credit_limit = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False))


class CustomerResponseSchema(CamelCaseSchema):
    id = fields.UUID()
    company_name = fields.String()
    contact_name = fields.String()
    contact_email = fields.String()
    contact_phone = fields.String()
    street = fields.String()
    city = fields.String()
    state = fields.String()
    country = fields.String()
    postal_code = fields.String()
    account_status = fields.Method("get_account_status")
    credit_limit = fields.Decimal(as_string=True)
    current_balance = fields.Decimal(as_string=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    def get_account_status(self, obj):
        return obj.account_status.value if obj.account_status else None

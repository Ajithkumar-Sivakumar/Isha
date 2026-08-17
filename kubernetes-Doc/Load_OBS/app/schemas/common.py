import re

from marshmallow import Schema, fields, post_dump


def _camel_case(snake_str):
    parts = snake_str.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class CamelCaseSchema(Schema):
    """Schema base that automatically converts snake_case fields to camelCase in output."""

    def on_bind_field(self, field_name, field_obj):
        if field_obj.data_key is None:
            field_obj.data_key = _camel_case(field_name)


class ErrorResponseSchema(CamelCaseSchema):
    timestamp = fields.DateTime()
    status = fields.Integer()
    error_code = fields.String()
    message = fields.String()
    correlation_id = fields.String()
    path = fields.String()
    field_errors = fields.List(fields.Dict())


class PagedResponseSchema(CamelCaseSchema):
    content = fields.List(fields.Dict())
    page = fields.Integer()
    size = fields.Integer()
    total_elements = fields.Integer()
    total_pages = fields.Integer()
    last = fields.Boolean()

from marshmallow import fields, validate

from app.schemas.common import CamelCaseSchema


class CreateShipmentItemRequestSchema(CamelCaseSchema):
    description = fields.String(required=True, validate=validate.Length(max=500))
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    weight = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False))
    length = fields.Decimal(as_string=True, validate=validate.Range(min=0, min_inclusive=False))
    width = fields.Decimal(as_string=True, validate=validate.Range(min=0, min_inclusive=False))
    height = fields.Decimal(as_string=True, validate=validate.Range(min=0, min_inclusive=False))
    hs_code = fields.String(validate=validate.Regexp(r"^\d{4}\.\d{2}(\.\d{2})?$"))
    country_of_origin = fields.String(validate=validate.Length(min=2, max=3))
    is_dangerous = fields.Boolean(load_default=False)
    temperature_controlled = fields.Boolean(load_default=False)
    min_temperature = fields.Float()
    max_temperature = fields.Float()


class CreateShipmentRequestSchema(CamelCaseSchema):
    customer_id = fields.UUID(required=True)
    route_id = fields.UUID(required=True)
    transport_mode = fields.String(
        required=True,
        validate=validate.OneOf(["AIR", "OCEAN", "GROUND"]),
    )
    priority = fields.String(
        load_default="STANDARD",
        validate=validate.OneOf(["STANDARD", "EXPRESS", "CRITICAL"]),
    )
    estimated_departure = fields.DateTime(required=True)
    estimated_arrival = fields.DateTime(required=True)
    total_weight = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False))
    total_volume = fields.Decimal(as_string=True, validate=validate.Range(min=0, min_inclusive=False))
    declared_value = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False))
    currency = fields.String(load_default="USD", validate=validate.Length(equal=3))
    special_instructions = fields.String()
    items = fields.List(
        fields.Nested(CreateShipmentItemRequestSchema),
        required=True,
        validate=validate.Length(min=1),
    )


class UpdateShipmentRequestSchema(CamelCaseSchema):
    priority = fields.String(validate=validate.OneOf(["STANDARD", "EXPRESS", "CRITICAL"]))
    estimated_departure = fields.DateTime()
    estimated_arrival = fields.DateTime()
    special_instructions = fields.String()
    declared_value = fields.Decimal(as_string=True, validate=validate.Range(min=0, min_inclusive=False))


class AssignCarrierRequestSchema(CamelCaseSchema):
    carrier_id = fields.UUID(required=True)


class ShipmentItemResponseSchema(CamelCaseSchema):
    id = fields.UUID()
    description = fields.String()
    quantity = fields.Integer()
    weight = fields.Decimal(as_string=True)
    length = fields.Decimal(as_string=True)
    width = fields.Decimal(as_string=True)
    height = fields.Decimal(as_string=True)
    hs_code = fields.String()
    country_of_origin = fields.String()
    is_dangerous = fields.Boolean()
    temperature_controlled = fields.Boolean()
    min_temperature = fields.Float()
    max_temperature = fields.Float()


class ShipmentResponseSchema(CamelCaseSchema):
    id = fields.UUID()
    reference_number = fields.String()
    customer = fields.Method("get_customer")
    carrier = fields.Method("get_carrier")
    route = fields.Method("get_route")
    status = fields.Method("get_status")
    transport_mode = fields.Method("get_transport_mode")
    priority = fields.Method("get_priority")
    estimated_departure = fields.DateTime()
    actual_departure = fields.DateTime()
    estimated_arrival = fields.DateTime()
    actual_arrival = fields.DateTime()
    total_weight = fields.Decimal(as_string=True)
    total_volume = fields.Decimal(as_string=True)
    declared_value = fields.Decimal(as_string=True)
    currency = fields.String()
    special_instructions = fields.String()
    items = fields.Method("get_items")
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    def get_status(self, obj):
        return obj.status.value if obj.status else None

    def get_transport_mode(self, obj):
        return obj.transport_mode.value if obj.transport_mode else None

    def get_priority(self, obj):
        return obj.priority.value if obj.priority else None

    def get_customer(self, obj):
        if obj.customer:
            return {
                "id": str(obj.customer.id),
                "companyName": obj.customer.company_name,
            }
        return None

    def get_carrier(self, obj):
        if obj.carrier:
            return {
                "id": str(obj.carrier.id),
                "name": obj.carrier.name,
                "code": obj.carrier.code,
            }
        return None

    def get_route(self, obj):
        if obj.route:
            return {
                "id": str(obj.route.id),
                "originPortName": obj.route.origin.name if obj.route.origin else None,
                "originPortCode": obj.route.origin.code if obj.route.origin else None,
                "destinationPortName": obj.route.destination.name if obj.route.destination else None,
                "destinationPortCode": obj.route.destination.code if obj.route.destination else None,
                "estimatedTransitDays": obj.route.estimated_transit_days,
            }
        return None

    def get_items(self, obj):
        schema = ShipmentItemResponseSchema(many=True)
        return schema.dump(obj.items)


class ShipmentSummaryResponseSchema(CamelCaseSchema):
    id = fields.UUID()
    reference_number = fields.String()
    customer_name = fields.Method("get_customer_name")
    carrier_name = fields.Method("get_carrier_name")
    status = fields.Method("get_status")
    transport_mode = fields.Method("get_transport_mode")
    priority = fields.Method("get_priority")
    origin_port = fields.Method("get_origin_port")
    destination_port = fields.Method("get_destination_port")
    estimated_arrival = fields.DateTime()
    total_weight = fields.Decimal(as_string=True)
    declared_value = fields.Decimal(as_string=True)
    created_at = fields.DateTime()

    def get_customer_name(self, obj):
        return obj.customer.company_name if obj.customer else None

    def get_carrier_name(self, obj):
        return obj.carrier.name if obj.carrier else None

    def get_status(self, obj):
        return obj.status.value if obj.status else None

    def get_transport_mode(self, obj):
        return obj.transport_mode.value if obj.transport_mode else None

    def get_priority(self, obj):
        return obj.priority.value if obj.priority else None

    def get_origin_port(self, obj):
        return obj.route.origin.code if obj.route and obj.route.origin else None

    def get_destination_port(self, obj):
        return obj.route.destination.code if obj.route and obj.route.destination else None

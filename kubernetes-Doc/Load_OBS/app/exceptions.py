class ShipmentApiException(Exception):
    def __init__(self, message, error_code, status_code):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class ResourceNotFoundException(ShipmentApiException):
    def __init__(self, resource_type, identifier):
        super().__init__(
            f"{resource_type} not found with identifier: {identifier}",
            "RESOURCE_NOT_FOUND",
            404,
        )


class InvalidStateTransitionException(ShipmentApiException):
    def __init__(self, current_state, target_state):
        super().__init__(
            f"Cannot transition from {current_state} to {target_state}",
            "INVALID_STATE_TRANSITION",
            409,
        )


class CreditLimitExceededException(ShipmentApiException):
    def __init__(self, shipment_value, remaining_credit):
        super().__init__(
            f"Shipment value {shipment_value} exceeds remaining credit {remaining_credit}",
            "CREDIT_LIMIT_EXCEEDED",
            422,
        )


class CarrierCapacityExceededException(ShipmentApiException):
    def __init__(self, carrier_name, overflow):
        super().__init__(
            f"Carrier {carrier_name} capacity exceeded by {overflow} kg",
            "CARRIER_CAPACITY_EXCEEDED",
            422,
        )


class CustomerAccountSuspendedException(ShipmentApiException):
    def __init__(self, customer_id):
        super().__init__(
            f"Customer account {customer_id} is suspended",
            "ACCOUNT_SUSPENDED",
            403,
        )


class DuplicateResourceException(ShipmentApiException):
    def __init__(self, resource_type, identifier):
        super().__init__(
            f"{resource_type} already exists with identifier: {identifier}",
            "DUPLICATE_RESOURCE",
            409,
        )


class InvalidRouteException(ShipmentApiException):
    def __init__(self, origin, destination, mode):
        super().__init__(
            f"No valid route from {origin} to {destination} for mode {mode}",
            "INVALID_ROUTE",
            422,
        )


class CustomsDeclarationException(ShipmentApiException):
    def __init__(self, reason):
        super().__init__(reason, "CUSTOMS_DECLARATION_ERROR", 422)

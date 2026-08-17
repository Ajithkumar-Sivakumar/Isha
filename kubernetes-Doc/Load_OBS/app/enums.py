import enum


class ShipmentStatus(enum.Enum):
    DRAFT = "DRAFT"
    BOOKED = "BOOKED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED_AT_PORT = "ARRIVED_AT_PORT"
    CUSTOMS_HOLD = "CUSTOMS_HOLD"
    CUSTOMS_CLEARED = "CUSTOMS_CLEARED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class TransportMode(enum.Enum):
    AIR = "AIR"
    OCEAN = "OCEAN"
    GROUND = "GROUND"


class ShipmentPriority(enum.Enum):
    STANDARD = "STANDARD"
    EXPRESS = "EXPRESS"
    CRITICAL = "CRITICAL"


class AccountStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class DeclarationStatus(enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PortType(enum.Enum):
    SEAPORT = "SEAPORT"
    AIRPORT = "AIRPORT"
    GROUND_TERMINAL = "GROUND_TERMINAL"

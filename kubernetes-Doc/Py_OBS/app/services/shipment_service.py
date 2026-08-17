import logging
from datetime import datetime, timezone
from decimal import Decimal

from flask import g
from sqlalchemy import func

from app.extensions import db
from app.enums import ShipmentStatus, TransportMode, ShipmentPriority
from app.models import Shipment, ShipmentItem, TrackingEvent, Customer, Carrier, Route
from app.exceptions import (
    ResourceNotFoundException,
    InvalidStateTransitionException,
    CreditLimitExceededException,
    CarrierCapacityExceededException,
    CustomerAccountSuspendedException,
    InvalidRouteException,
)
from app.enums import AccountStatus

logger = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    ShipmentStatus.DRAFT: {ShipmentStatus.BOOKED, ShipmentStatus.CANCELLED},
    ShipmentStatus.BOOKED: {ShipmentStatus.PICKED_UP, ShipmentStatus.CANCELLED},
    ShipmentStatus.PICKED_UP: {ShipmentStatus.IN_TRANSIT},
    ShipmentStatus.IN_TRANSIT: {ShipmentStatus.ARRIVED_AT_PORT},
    ShipmentStatus.ARRIVED_AT_PORT: {ShipmentStatus.CUSTOMS_HOLD, ShipmentStatus.OUT_FOR_DELIVERY},
    ShipmentStatus.CUSTOMS_HOLD: {ShipmentStatus.CUSTOMS_CLEARED},
    ShipmentStatus.CUSTOMS_CLEARED: {ShipmentStatus.OUT_FOR_DELIVERY},
    ShipmentStatus.OUT_FOR_DELIVERY: {ShipmentStatus.DELIVERED},
}


def _generate_reference_number():
    count = db.session.query(func.count(Shipment.id)).scalar() or 0
    year = datetime.now(timezone.utc).year
    return f"EXP-{year}-{count + 1:05d}"


def get_shipment(shipment_id):
    shipment = db.session.get(Shipment, shipment_id)
    if not shipment:
        raise ResourceNotFoundException("Shipment", shipment_id)
    return shipment


def list_shipments(
    status=None,
    customer_id=None,
    carrier_id=None,
    transport_mode=None,
    priority=None,
    from_date=None,
    to_date=None,
    page=0,
    size=20,
    sort_by="created_at",
    sort_dir="desc",
):
    query = Shipment.query

    if status:
        query = query.filter(Shipment.status == ShipmentStatus(status))
    if customer_id:
        query = query.filter(Shipment.customer_id == customer_id)
    if carrier_id:
        query = query.filter(Shipment.carrier_id == carrier_id)
    if transport_mode:
        query = query.filter(Shipment.transport_mode == TransportMode(transport_mode))
    if priority:
        query = query.filter(Shipment.priority == ShipmentPriority(priority))
    if from_date:
        query = query.filter(Shipment.created_at >= from_date)
    if to_date:
        query = query.filter(Shipment.created_at <= to_date)

    sort_column = getattr(Shipment, sort_by, Shipment.created_at)
    if sort_dir == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    pagination = query.paginate(page=page + 1, per_page=size, error_out=False)
    return {
        "content": pagination.items,
        "page": page,
        "size": size,
        "totalElements": pagination.total,
        "totalPages": pagination.pages,
        "last": not pagination.has_next,
    }


def create_shipment(data):
    customer = db.session.get(Customer, data["customer_id"])
    if not customer:
        raise ResourceNotFoundException("Customer", data["customer_id"])

    if customer.account_status != AccountStatus.ACTIVE:
        raise CustomerAccountSuspendedException(customer.id)

    declared_value = Decimal(str(data["declared_value"]))
    remaining_credit = customer.credit_limit - customer.current_balance
    if declared_value > remaining_credit:
        raise CreditLimitExceededException(declared_value, remaining_credit)

    route = db.session.get(Route, data["route_id"])
    if not route:
        raise ResourceNotFoundException("Route", data["route_id"])
    if not route.is_active:
        origin_code = route.origin.code if route.origin else "?"
        dest_code = route.destination.code if route.destination else "?"
        raise InvalidRouteException(origin_code, dest_code, data["transport_mode"])

    transport_mode = TransportMode(data["transport_mode"].upper())
    priority = ShipmentPriority(data.get("priority", "STANDARD").upper())

    reference_number = _generate_reference_number()

    shipment = Shipment(
        reference_number=reference_number,
        customer_id=data["customer_id"],
        route_id=data["route_id"],
        status=ShipmentStatus.DRAFT,
        transport_mode=transport_mode,
        priority=priority,
        estimated_departure=data.get("estimated_departure"),
        estimated_arrival=data.get("estimated_arrival"),
        total_weight=data["total_weight"],
        total_volume=data.get("total_volume"),
        declared_value=declared_value,
        currency=data.get("currency", "USD"),
        special_instructions=data.get("special_instructions"),
    )
    db.session.add(shipment)
    db.session.flush()

    for item_data in data["items"]:
        item = ShipmentItem(
            shipment_id=shipment.id,
            description=item_data["description"],
            quantity=item_data["quantity"],
            weight=item_data["weight"],
            length=item_data.get("length"),
            width=item_data.get("width"),
            height=item_data.get("height"),
            hs_code=item_data.get("hs_code"),
            country_of_origin=item_data.get("country_of_origin"),
            is_dangerous=item_data.get("is_dangerous", False),
            temperature_controlled=item_data.get("temperature_controlled", False),
            min_temperature=item_data.get("min_temperature"),
            max_temperature=item_data.get("max_temperature"),
        )
        db.session.add(item)

    customer.current_balance = customer.current_balance + declared_value
    db.session.commit()

    logger.info(
        "Shipment created",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "referenceNumber": shipment.reference_number,
            "customerId": str(customer.id),
            "customerName": customer.company_name,
            "route": f"{route.origin.code} -> {route.destination.code}",
            "mode": transport_mode.value,
            "weight": str(shipment.total_weight),
            "value": str(declared_value),
            "service": "logistics-api",
        },
    )

    db.session.refresh(shipment)
    return shipment


def update_shipment(shipment_id, data):
    shipment = get_shipment(shipment_id)

    if shipment.status not in (ShipmentStatus.DRAFT, ShipmentStatus.BOOKED):
        raise InvalidStateTransitionException(shipment.status.value, "UPDATE")

    if "priority" in data and data["priority"] is not None:
        shipment.priority = ShipmentPriority(data["priority"].upper())
    if "estimated_departure" in data:
        shipment.estimated_departure = data["estimated_departure"]
    if "estimated_arrival" in data:
        shipment.estimated_arrival = data["estimated_arrival"]
    if "special_instructions" in data:
        shipment.special_instructions = data["special_instructions"]
    if "declared_value" in data and data["declared_value"] is not None:
        shipment.declared_value = data["declared_value"]

    db.session.commit()
    db.session.refresh(shipment)
    return shipment


def delete_shipment(shipment_id):
    shipment = get_shipment(shipment_id)

    allowed = VALID_TRANSITIONS.get(shipment.status, set())
    if ShipmentStatus.CANCELLED not in allowed:
        raise InvalidStateTransitionException(shipment.status.value, "CANCELLED")

    if shipment.carrier:
        shipment.carrier.current_load_kg = (
            Decimal(str(shipment.carrier.current_load_kg))
            - Decimal(str(shipment.total_weight))
        )

    shipment.customer.current_balance = (
        Decimal(str(shipment.customer.current_balance))
        - Decimal(str(shipment.declared_value))
    )

    shipment.status = ShipmentStatus.CANCELLED
    db.session.commit()

    logger.info(
        "Shipment cancelled",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "referenceNumber": shipment.reference_number,
            "service": "logistics-api",
        },
    )


def assign_carrier(shipment_id, carrier_id):
    shipment = get_shipment(shipment_id)

    if shipment.status != ShipmentStatus.BOOKED:
        raise InvalidStateTransitionException(shipment.status.value, "ASSIGN_CARRIER")

    carrier = db.session.get(Carrier, carrier_id)
    if not carrier:
        raise ResourceNotFoundException("Carrier", carrier_id)

    if shipment.transport_mode.value not in carrier.transport_modes:
        raise InvalidRouteException(
            "carrier", carrier.name, f"incompatible mode {shipment.transport_mode.value}"
        )

    available = Decimal(str(carrier.max_capacity_kg)) - Decimal(str(carrier.current_load_kg))
    weight = Decimal(str(shipment.total_weight))
    if weight > available:
        raise CarrierCapacityExceededException(carrier.name, weight - available)

    has_dangerous = any(item.is_dangerous for item in shipment.items)
    if has_dangerous:
        logger.warning(
            "Shipment contains dangerous goods",
            extra={
                "correlationId": getattr(g, "correlation_id", None),
                "referenceNumber": shipment.reference_number,
                "carrierId": str(carrier.id),
                "service": "logistics-api",
            },
        )

    shipment.carrier_id = carrier.id
    carrier.current_load_kg = Decimal(str(carrier.current_load_kg)) + weight

    utilization = (Decimal(str(carrier.current_load_kg)) / Decimal(str(carrier.max_capacity_kg))) * 100
    if utilization > 85:
        logger.warning(
            "Carrier utilization above 85%%",
            extra={
                "correlationId": getattr(g, "correlation_id", None),
                "carrierCode": carrier.code,
                "utilization": str(round(utilization, 2)),
                "service": "logistics-api",
            },
        )

    db.session.commit()
    db.session.refresh(shipment)

    logger.info(
        "Carrier assigned to shipment",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "referenceNumber": shipment.reference_number,
            "carrierCode": carrier.code,
            "service": "logistics-api",
        },
    )

    return shipment


def record_tracking_event(shipment_id, data):
    shipment = get_shipment(shipment_id)
    new_status = ShipmentStatus(data["status"].upper())

    allowed = VALID_TRANSITIONS.get(shipment.status, set())
    if new_status not in allowed:
        raise InvalidStateTransitionException(shipment.status.value, new_status.value)

    shipment.status = new_status

    if new_status == ShipmentStatus.DELIVERED:
        shipment.actual_arrival = data["occurred_at"]
        if shipment.carrier:
            shipment.carrier.current_load_kg = (
                Decimal(str(shipment.carrier.current_load_kg))
                - Decimal(str(shipment.total_weight))
            )

    if new_status in (ShipmentStatus.PICKED_UP, ShipmentStatus.IN_TRANSIT):
        if shipment.actual_departure is None:
            shipment.actual_departure = data["occurred_at"]

    event = TrackingEvent(
        shipment_id=shipment.id,
        status=new_status,
        location=data.get("location"),
        notes=data.get("notes"),
        reported_by=data["reported_by"],
        occurred_at=data["occurred_at"],
    )
    db.session.add(event)
    db.session.commit()
    db.session.refresh(event)

    logger.info(
        "Tracking event recorded",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "referenceNumber": shipment.reference_number,
            "newStatus": new_status.value,
            "service": "logistics-api",
        },
    )

    return event


def get_tracking_events(shipment_id):
    shipment = get_shipment(shipment_id)
    return shipment.tracking_events

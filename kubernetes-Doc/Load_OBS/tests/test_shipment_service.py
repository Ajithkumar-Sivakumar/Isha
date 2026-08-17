import uuid
from decimal import Decimal

import pytest

from app.enums import ShipmentStatus, AccountStatus, TransportMode
from app.exceptions import (
    CustomerAccountSuspendedException,
    CreditLimitExceededException,
    CarrierCapacityExceededException,
    InvalidStateTransitionException,
    InvalidRouteException,
)
from app.services import shipment_service
from tests.factories import (
    CustomerFactory,
    CarrierFactory,
    RouteFactory,
    ShipmentFactory,
    PortFactory,
)
from app.models import CarrierTransportMode
from app.extensions import db


def _base_shipment_data(customer_id, route_id):
    return {
        "customer_id": customer_id,
        "route_id": route_id,
        "transport_mode": "OCEAN",
        "priority": "STANDARD",
        "estimated_departure": "2026-07-01T08:00:00",
        "estimated_arrival": "2026-07-15T08:00:00",
        "total_weight": Decimal("1000"),
        "declared_value": Decimal("10000"),
        "currency": "USD",
        "items": [
            {"description": "Test Item", "quantity": 1, "weight": Decimal("1000")}
        ],
    }


def test_create_shipment_success(client, db):
    customer = CustomerFactory(credit_limit=Decimal("500000"))
    route = RouteFactory()
    data = _base_shipment_data(customer.id, route.id)

    shipment = shipment_service.create_shipment(data)

    assert shipment.status == ShipmentStatus.DRAFT
    assert shipment.reference_number.startswith("EXP-")
    assert len(shipment.items) == 1


def test_create_shipment_suspended_customer(client, db):
    customer = CustomerFactory(account_status=AccountStatus.SUSPENDED)
    route = RouteFactory()
    data = _base_shipment_data(customer.id, route.id)

    with pytest.raises(CustomerAccountSuspendedException):
        shipment_service.create_shipment(data)


def test_create_shipment_credit_exceeded(client, db):
    customer = CustomerFactory(
        credit_limit=Decimal("5000"), current_balance=Decimal("4500")
    )
    route = RouteFactory()
    data = _base_shipment_data(customer.id, route.id)
    data["declared_value"] = Decimal("1000")

    with pytest.raises(CreditLimitExceededException):
        shipment_service.create_shipment(data)


def test_assign_carrier_success(client, db):
    shipment = ShipmentFactory(status=ShipmentStatus.BOOKED)
    carrier = CarrierFactory()

    result = shipment_service.assign_carrier(shipment.id, carrier.id)
    assert result.carrier_id == carrier.id


def test_assign_carrier_wrong_mode(client, db):
    origin = PortFactory()
    dest = PortFactory()
    route = RouteFactory(
        origin_id=origin.id,
        destination_id=dest.id,
        transport_mode=TransportMode.AIR,
    )
    shipment = ShipmentFactory(
        status=ShipmentStatus.BOOKED,
        transport_mode=TransportMode.AIR,
        route_id=route.id,
    )
    carrier = CarrierFactory()

    with pytest.raises(InvalidRouteException):
        shipment_service.assign_carrier(shipment.id, carrier.id)


def test_assign_carrier_capacity_exceeded(client, db):
    carrier = CarrierFactory()
    carrier.max_capacity_kg = Decimal("100")
    carrier.current_load_kg = Decimal("90")
    db.session.commit()

    shipment = ShipmentFactory(
        status=ShipmentStatus.BOOKED, total_weight=Decimal("50")
    )

    with pytest.raises(CarrierCapacityExceededException):
        shipment_service.assign_carrier(shipment.id, carrier.id)


def test_record_tracking_event_valid_transition(client, db):
    shipment = ShipmentFactory(status=ShipmentStatus.DRAFT)

    event = shipment_service.record_tracking_event(
        shipment.id,
        {
            "status": "BOOKED",
            "location": "Office",
            "reported_by": "agent",
            "occurred_at": "2026-07-01T09:00:00",
        },
    )

    assert event.status == ShipmentStatus.BOOKED


def test_record_tracking_event_invalid_transition(client, db):
    shipment = ShipmentFactory(status=ShipmentStatus.DRAFT)

    with pytest.raises(InvalidStateTransitionException):
        shipment_service.record_tracking_event(
            shipment.id,
            {
                "status": "DELIVERED",
                "location": "Office",
                "reported_by": "agent",
                "occurred_at": "2026-07-01T09:00:00",
            },
        )


def test_cancel_shipment_releases_carrier_capacity(client, db):
    carrier = CarrierFactory()
    initial_load = Decimal(str(carrier.current_load_kg))

    shipment = ShipmentFactory(
        status=ShipmentStatus.BOOKED,
        carrier_id=carrier.id,
        total_weight=Decimal("5000"),
    )
    carrier.current_load_kg = initial_load + Decimal("5000")
    db.session.commit()

    shipment_service.delete_shipment(shipment.id)

    db.session.refresh(carrier)
    assert Decimal(str(carrier.current_load_kg)) == initial_load


def test_cancel_shipment_restores_credit(client, db):
    customer = CustomerFactory(
        credit_limit=Decimal("100000"), current_balance=Decimal("50000")
    )
    route = RouteFactory()
    shipment = ShipmentFactory(
        status=ShipmentStatus.DRAFT,
        customer_id=customer.id,
        route_id=route.id,
        declared_value=Decimal("20000"),
    )
    customer.current_balance = Decimal("50000")
    db.session.commit()

    shipment_service.delete_shipment(shipment.id)

    db.session.refresh(customer)
    assert Decimal(str(customer.current_balance)) == Decimal("30000")

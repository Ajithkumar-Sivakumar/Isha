import uuid
from decimal import Decimal

import factory

from app.extensions import db
from app.enums import (
    AccountStatus,
    ShipmentStatus,
    TransportMode,
    ShipmentPriority,
    PortType,
)
from app.models import Customer, Carrier, CarrierTransportMode, Port, Route, Shipment


class CustomerFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Customer
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(uuid.uuid4)
    company_name = factory.Sequence(lambda n: f"Test Company {n}")
    contact_name = factory.Sequence(lambda n: f"Contact {n}")
    contact_email = factory.Sequence(lambda n: f"contact{n}@test.example.com")
    contact_phone = "+1-555-0000"
    street = "123 Test St"
    city = "TestCity"
    state = "TS"
    country = "US"
    postal_code = "00000"
    account_status = AccountStatus.ACTIVE
    credit_limit = Decimal("500000")
    current_balance = Decimal("0")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        session = db.session
        obj = model_class(*args, **kwargs)
        session.add(obj)
        session.commit()
        return obj


class PortFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Port
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Test Port {n}")
    code = factory.Sequence(lambda n: f"TP{n:03d}")
    type = PortType.SEAPORT
    city = "PortCity"
    country = "US"
    timezone = "America/Los_Angeles"
    latitude = 47.0
    longitude = -122.0

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        session = db.session
        obj = model_class(*args, **kwargs)
        session.add(obj)
        session.commit()
        return obj


class CarrierFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Carrier
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Test Carrier {n}")
    code = factory.Sequence(lambda n: f"TC{n:03d}")
    max_capacity_kg = Decimal("1000000")
    current_load_kg = Decimal("0")
    rating = Decimal("4.0")
    contact_email = factory.Sequence(lambda n: f"carrier{n}@test.example.com")
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        session = db.session
        obj = model_class(*args, **kwargs)
        session.add(obj)
        session.commit()
        tm = CarrierTransportMode(carrier_id=obj.id, transport_mode="OCEAN")
        session.add(tm)
        session.commit()
        return obj


class RouteFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Route
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(uuid.uuid4)
    origin_id = None
    destination_id = None
    transport_mode = TransportMode.OCEAN
    estimated_transit_days = 14
    distance_km = Decimal("8500")
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if kwargs.get("origin_id") is None:
            origin = PortFactory()
            kwargs["origin_id"] = origin.id
        if kwargs.get("destination_id") is None:
            dest = PortFactory()
            kwargs["destination_id"] = dest.id
        session = db.session
        obj = model_class(*args, **kwargs)
        session.add(obj)
        session.commit()
        return obj


class ShipmentFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Shipment
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(uuid.uuid4)
    reference_number = factory.Sequence(lambda n: f"EXP-TEST-{n:05d}")
    customer_id = None
    route_id = None
    status = ShipmentStatus.DRAFT
    transport_mode = TransportMode.OCEAN
    priority = ShipmentPriority.STANDARD
    total_weight = Decimal("1000")
    declared_value = Decimal("10000")
    currency = "USD"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if kwargs.get("customer_id") is None:
            customer = CustomerFactory()
            kwargs["customer_id"] = customer.id
        if kwargs.get("route_id") is None:
            route = RouteFactory()
            kwargs["route_id"] = route.id
        session = db.session
        obj = model_class(*args, **kwargs)
        session.add(obj)
        session.commit()
        return obj

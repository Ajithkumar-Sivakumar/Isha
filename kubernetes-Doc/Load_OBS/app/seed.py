import click
from datetime import datetime, timezone
from decimal import Decimal

from flask.cli import with_appcontext

from app.extensions import db
from app.enums import (
    ShipmentStatus,
    TransportMode,
    ShipmentPriority,
    AccountStatus,
    PortType,
)
from app.models import (
    Port,
    Carrier,
    CarrierTransportMode,
    Route,
    Customer,
    Shipment,
    ShipmentItem,
    TrackingEvent,
)


def _dt(s):
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


@click.command("seed")
@with_appcontext
def seed_command():
    """Seed the database with sample data."""
    if db.session.query(Port).count() > 0:
        click.echo("Database already seeded, skipping.")
        return

    click.echo("Seeding database...")

    # --- Ports ---
    ports_data = [
        ("Port of Seattle", "USSEA", PortType.SEAPORT, "Seattle", "US", "America/Los_Angeles", 47.6062, -122.3321),
        ("Port of Los Angeles", "USLAX", PortType.SEAPORT, "Los Angeles", "US", "America/Los_Angeles", 33.7405, -118.2653),
        ("Port of Shanghai", "CNSHA", PortType.SEAPORT, "Shanghai", "CN", "Asia/Shanghai", 31.2304, 121.4737),
        ("Port of Rotterdam", "NLRTM", PortType.SEAPORT, "Rotterdam", "NL", "Europe/Amsterdam", 51.9225, 4.47917),
        ("Port of Singapore", "SGSIN", PortType.SEAPORT, "Singapore", "SG", "Asia/Singapore", 1.2644, 103.8220),
        ("Tokyo Narita Airport", "JPNRT", PortType.AIRPORT, "Tokyo", "JP", "Asia/Tokyo", 35.7720, 140.3929),
        ("Seattle-Tacoma Airport", "USSEA-AIR", PortType.AIRPORT, "Seattle", "US", "America/Los_Angeles", 47.4502, -122.3088),
        ("Frankfurt Airport", "DEFRA", PortType.AIRPORT, "Frankfurt", "DE", "Europe/Berlin", 50.0379, 8.5622),
        ("Chicago Intermodal Terminal", "USCHI-GND", PortType.GROUND_TERMINAL, "Chicago", "US", "America/Chicago", 41.8781, -87.6298),
        ("Dallas Distribution Hub", "USDAL-GND", PortType.GROUND_TERMINAL, "Dallas", "US", "America/Chicago", 32.7767, -96.7970),
    ]

    ports = {}
    for name, code, ptype, city, country, tz, lat, lon in ports_data:
        port = Port(
            name=name, code=code, type=ptype, city=city,
            country=country, timezone=tz, latitude=lat, longitude=lon,
        )
        db.session.add(port)
        ports[code] = port

    db.session.flush()

    # --- Carriers ---
    carriers_data = [
        ("Maersk Line", "MAER", ["OCEAN"], 5000000, 2100000, 4.5, "ops@maersk.example.com"),
        ("Evergreen Marine", "EGRN", ["OCEAN"], 4000000, 1500000, 4.2, "dispatch@evergreen.example.com"),
        ("FedEx Freight", "FDXF", ["AIR", "GROUND"], 800000, 350000, 4.7, "freight@fedex.example.com"),
        ("Nippon Cargo Airlines", "NCA", ["AIR"], 600000, 280000, 4.3, "cargo@nca.example.com"),
        ("XPO Logistics", "XPO", ["GROUND"], 1200000, 700000, 4.0, "ops@xpo.example.com"),
        ("Hapag-Lloyd", "HPLG", ["OCEAN"], 3500000, 2800000, 4.1, "booking@hapag.example.com"),
    ]

    carriers = {}
    for name, code, modes, max_cap, cur_load, rating, email in carriers_data:
        carrier = Carrier(
            name=name, code=code, max_capacity_kg=max_cap,
            current_load_kg=cur_load, rating=rating, contact_email=email,
        )
        db.session.add(carrier)
        db.session.flush()
        for mode in modes:
            tm = CarrierTransportMode(carrier_id=carrier.id, transport_mode=mode)
            db.session.add(tm)
        carriers[code] = carrier

    db.session.flush()

    # --- Routes ---
    routes_data = [
        ("USSEA", "CNSHA", TransportMode.OCEAN, 14, 8500),
        ("CNSHA", "USSEA", TransportMode.OCEAN, 14, 8500),
        ("USLAX", "CNSHA", TransportMode.OCEAN, 12, 9600),
        ("USSEA", "NLRTM", TransportMode.OCEAN, 21, 14500),
        ("NLRTM", "SGSIN", TransportMode.OCEAN, 18, 15000),
        ("USSEA-AIR", "JPNRT", TransportMode.AIR, 1, 7700),
        ("USSEA-AIR", "DEFRA", TransportMode.AIR, 1, 8200),
        ("JPNRT", "USSEA-AIR", TransportMode.AIR, 1, 7700),
        ("USCHI-GND", "USDAL-GND", TransportMode.GROUND, 2, 1300),
        ("USDAL-GND", "USCHI-GND", TransportMode.GROUND, 2, 1300),
    ]

    routes = {}
    for origin_code, dest_code, mode, transit_days, distance in routes_data:
        route = Route(
            origin_id=ports[origin_code].id,
            destination_id=ports[dest_code].id,
            transport_mode=mode,
            estimated_transit_days=transit_days,
            distance_km=distance,
        )
        db.session.add(route)
        key = f"{origin_code}->{dest_code}"
        routes[key] = route

    db.session.flush()

    # --- Customers ---
    customers_data = [
        ("Pacific Electronics Co.", "Sarah Chen", "sarah.chen@pacelec.example.com", "+1-206-555-0100", "1200 Harbor Ave", "Seattle", "WA", "US", "98101", 500000, AccountStatus.ACTIVE),
        ("Nordic Furniture AB", "Erik Lindqvist", "erik@nordicfurn.example.com", "+46-8-555-0200", "Storgatan 15", "Stockholm", None, "SE", "11123", 300000, AccountStatus.ACTIVE),
        ("Tokyo Auto Parts Ltd", "Yuki Tanaka", "ytanaka@tokyoauto.example.com", "+81-3-555-0300", "2-1-1 Marunouchi", "Tokyo", None, "JP", "100-0005", 750000, AccountStatus.ACTIVE),
        ("Rhine Chemical GmbH", "Hans Mueller", "mueller@rhinechem.example.com", "+49-69-555-0400", "Industriestr. 42", "Frankfurt", None, "DE", "60311", 1000000, AccountStatus.ACTIVE),
        ("Suspended Trading Co", "Bob Inactive", "bob@suspended.example.com", "+1-555-0500", "999 Closed Rd", "Portland", "OR", "US", "97201", 100000, AccountStatus.SUSPENDED),
    ]

    customers = {}
    for company, contact, email, phone, street, city, state, country, postal, credit, status in customers_data:
        customer = Customer(
            company_name=company, contact_name=contact, contact_email=email,
            contact_phone=phone, street=street, city=city, state=state,
            country=country, postal_code=postal, credit_limit=credit,
            current_balance=0, account_status=status,
        )
        db.session.add(customer)
        customers[company] = customer

    db.session.flush()

    # --- Shipment 1: EXP-2026-00001 ---
    pacific = customers["Pacific Electronics Co."]
    nordic = customers["Nordic Furniture AB"]

    s1 = Shipment(
        reference_number="EXP-2026-00001",
        customer_id=pacific.id,
        carrier_id=carriers["MAER"].id,
        route_id=routes["USSEA->CNSHA"].id,
        status=ShipmentStatus.IN_TRANSIT,
        transport_mode=TransportMode.OCEAN,
        priority=ShipmentPriority.STANDARD,
        estimated_departure=_dt("2026-06-01T08:00:00"),
        actual_departure=_dt("2026-06-02T06:00:00"),
        estimated_arrival=_dt("2026-06-15T08:00:00"),
        total_weight=Decimal("12500"),
        total_volume=Decimal("55"),
        declared_value=Decimal("125000"),
        currency="USD",
    )
    db.session.add(s1)
    db.session.flush()

    s1_items = [
        ShipmentItem(shipment_id=s1.id, description="LCD Display Panels", quantity=500, weight=Decimal("5000")),
        ShipmentItem(shipment_id=s1.id, description="Circuit Board Assembly Kits", quantity=1000, weight=Decimal("4500")),
        ShipmentItem(shipment_id=s1.id, description="Power Supply Units", quantity=300, weight=Decimal("3000")),
    ]
    for item in s1_items:
        db.session.add(item)

    s1_events = [
        TrackingEvent(shipment_id=s1.id, status=ShipmentStatus.BOOKED, location="Seattle Office", reported_by="booking-agent", occurred_at=_dt("2026-06-01T09:00:00")),
        TrackingEvent(shipment_id=s1.id, status=ShipmentStatus.PICKED_UP, location="Customer Warehouse, Seattle", reported_by="driver-12", occurred_at=_dt("2026-06-02T06:00:00")),
        TrackingEvent(shipment_id=s1.id, status=ShipmentStatus.IN_TRANSIT, location="Port of Seattle, Terminal 5", reported_by="terminal-ops", occurred_at=_dt("2026-06-02T14:00:00")),
    ]
    for event in s1_events:
        db.session.add(event)

    # --- Shipment 2: EXP-2026-00002 ---
    s2 = Shipment(
        reference_number="EXP-2026-00002",
        customer_id=nordic.id,
        route_id=routes["USSEA->NLRTM"].id,
        status=ShipmentStatus.BOOKED,
        transport_mode=TransportMode.OCEAN,
        priority=ShipmentPriority.EXPRESS,
        estimated_departure=_dt("2026-06-10T08:00:00"),
        estimated_arrival=_dt("2026-07-01T08:00:00"),
        total_weight=Decimal("8200"),
        total_volume=Decimal("120"),
        declared_value=Decimal("89000"),
        currency="USD",
    )
    db.session.add(s2)
    db.session.flush()

    s2_items = [
        ShipmentItem(shipment_id=s2.id, description="Flat-Pack Furniture Sets", quantity=200, weight=Decimal("6000")),
        ShipmentItem(shipment_id=s2.id, description="Decorative Lighting Fixtures", quantity=150, weight=Decimal("2200")),
    ]
    for item in s2_items:
        db.session.add(item)

    # --- Shipment 3: EXP-2026-00003 ---
    s3 = Shipment(
        reference_number="EXP-2026-00003",
        customer_id=pacific.id,
        route_id=routes["USSEA->CNSHA"].id,
        status=ShipmentStatus.DRAFT,
        transport_mode=TransportMode.OCEAN,
        priority=ShipmentPriority.STANDARD,
        estimated_departure=_dt("2026-06-20T08:00:00"),
        estimated_arrival=_dt("2026-07-04T08:00:00"),
        total_weight=Decimal("5000"),
        total_volume=Decimal("30"),
        declared_value=Decimal("45000"),
        currency="USD",
        special_instructions="Fragile electronics - handle with care",
    )
    db.session.add(s3)
    db.session.flush()

    s3_items = [
        ShipmentItem(shipment_id=s3.id, description="Laptop Screens", quantity=400, weight=Decimal("3000")),
        ShipmentItem(shipment_id=s3.id, description="Keyboard Assemblies", quantity=600, weight=Decimal("2000")),
    ]
    for item in s3_items:
        db.session.add(item)

    # Set customer balances
    pacific.current_balance = Decimal("170000")
    nordic.current_balance = Decimal("89000")

    # Set suspended customer balance
    customers["Suspended Trading Co"].current_balance = Decimal("95000")

    db.session.commit()
    click.echo("Database seeded successfully!")

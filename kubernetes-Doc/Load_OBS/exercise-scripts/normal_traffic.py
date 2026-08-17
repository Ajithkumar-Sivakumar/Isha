"""
Normal Traffic - Baseline Script

Simulates a healthy day of operations: steady shipment creation,
carrier assignments, and lifecycle progression. Run this first so
students can see what "normal" looks like in Grafana before running
a scenario script.

Runs for approximately 2-3 minutes.
"""

import random
import time
from client import LogisticsClient, make_item, progress

client = LogisticsClient()

TRANSPORT_MODES = ["OCEAN", "OCEAN", "OCEAN", "OCEAN", "OCEAN", "OCEAN",
                   "AIR", "AIR", "AIR", "GROUND"]
PRIORITIES = ["STANDARD", "STANDARD", "STANDARD", "EXPRESS", "CRITICAL"]


def get_seed_data():
    """Load existing seed data IDs."""
    customers = client.get_customers()["content"]
    active_customers = [c for c in customers if c["accountStatus"] == "ACTIVE"]

    routes = client.get_routes()
    carriers = client.get_carriers()

    return active_customers, routes, carriers


def create_new_customers():
    """Create a couple of fresh customers for this traffic run."""
    suffix = int(time.time()) % 10000
    new_customers = []

    names = [
        (f"TrafficTest Corp {suffix}", f"Agent {suffix}", f"agent{suffix}@traffictest.example.com"),
        (f"LoadTest Industries {suffix}", f"Tester {suffix}", f"tester{suffix}@loadtest.example.com"),
    ]
    for company, contact, email in names:
        r = client.create_customer(company, contact, email, credit_limit=500000)
        if r.status_code == 201:
            new_customers.append(r.json())
            progress(f"Created customer: {company}")
        else:
            progress(f"Customer creation returned {r.status_code} (may already exist)")
    return new_customers


def pick_compatible_carrier(carriers, mode):
    """Find a carrier that supports the given mode."""
    compatible = [c for c in carriers if mode in c.get("transportModes", [])]
    if not compatible:
        return None
    return random.choice(compatible)


def simulate_shipment_lifecycle(customer, routes, carriers, progress_fully=True):
    """Create a shipment and optionally move it through its lifecycle."""
    mode = random.choice(TRANSPORT_MODES)
    compatible_routes = [r for r in routes if r["transportMode"] == mode]
    if not compatible_routes:
        return

    route = random.choice(compatible_routes)
    priority = random.choice(PRIORITIES)
    weight = random.randint(500, 15000)
    value = random.randint(5000, 100000)

    items = [make_item(
        description=random.choice([
            "Electronics", "Furniture", "Auto Parts", "Chemicals", "Textiles",
            "Machinery", "Food Products", "Medical Supplies"
        ]),
        quantity=random.randint(1, 100),
        weight=weight,
    )]

    r = client.create_shipment(
        customer_id=customer["id"],
        route_id=route["id"],
        transport_mode=mode,
        total_weight=weight,
        declared_value=value,
        items=items,
        priority=priority,
    )

    if r.status_code != 201:
        progress(f"  Shipment creation: {r.status_code} (expected for some edge cases)")
        return

    shipment = r.json()
    ref = shipment["referenceNumber"]
    progress(f"  Created shipment {ref} [{mode}/{priority}]")

    if not progress_fully:
        return

    # DRAFT -> BOOKED
    r = client.create_tracking_event(
        shipment["id"], "BOOKED", "Operations Center", "booking-system"
    )
    if r.status_code != 201:
        return

    # Assign carrier
    carrier = pick_compatible_carrier(carriers, mode)
    if carrier:
        r = client.assign_carrier(shipment["id"], carrier["id"])
        if r.status_code == 200:
            progress(f"  Assigned carrier {carrier['code']} to {ref}")

    # Some shipments progress further
    if random.random() < 0.5:
        client.create_tracking_event(
            shipment["id"], "PICKED_UP", "Customer Warehouse", "driver-01"
        )
        if random.random() < 0.6:
            client.create_tracking_event(
                shipment["id"], "IN_TRANSIT", "Port Terminal", "terminal-ops"
            )


def send_intentional_bad_request():
    """~3% of traffic has validation errors (realistic noise)."""
    bad_payloads = [
        {},
        {"customerId": "not-a-uuid"},
        {"customerId": "00000000-0000-0000-0000-000000000000", "routeId": "00000000-0000-0000-0000-000000000000"},
    ]
    payload = random.choice(bad_payloads)
    client._post("/shipments", json=payload)
    progress("  Sent malformed request (expected 400)")


def main():
    progress("=" * 60)
    progress("NORMAL TRAFFIC SIMULATION")
    progress("Generating baseline traffic for ~2-3 minutes")
    progress("Watch Grafana to see what healthy operations look like")
    progress("=" * 60)
    print()

    progress("Checking API health...")
    client.wait_for_ready()
    progress("API is ready!")
    print()

    progress("Loading seed data...")
    active_customers, routes, carriers = get_seed_data()
    progress(f"Found {len(active_customers)} active customers, {len(routes)} routes, {len(carriers)} carriers")
    print()

    progress("Creating test customers...")
    new_customers = create_new_customers()
    all_customers = active_customers + new_customers
    print()

    progress("Starting steady-state traffic generation...")
    progress("(~1 shipment per second for 2 minutes)")
    print()

    shipments_created = 0
    start_time = time.time()
    duration = 120

    while time.time() - start_time < duration:
        customer = random.choice(all_customers)

        if random.random() < 0.03:
            send_intentional_bad_request()
        else:
            progress_fully = random.random() < 0.7
            simulate_shipment_lifecycle(customer, routes, carriers, progress_fully)
            shipments_created += 1

        # Read operations mixed in
        if random.random() < 0.3:
            client.get_shipments()
        if random.random() < 0.2:
            client.get_analytics_summary()
        if random.random() < 0.1:
            client.get_carriers()

        time.sleep(random.uniform(0.8, 1.5))

    elapsed = time.time() - start_time
    print()
    progress("=" * 60)
    progress(f"DONE - Generated {shipments_created} shipments in {elapsed:.0f}s")
    progress("Check Grafana to review the baseline metrics")
    progress("=" * 60)


if __name__ == "__main__":
    main()

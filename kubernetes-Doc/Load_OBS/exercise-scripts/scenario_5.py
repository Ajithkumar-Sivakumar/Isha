"""
Scenario 5 - Analytics endpoint degradation from data volume.

(Instructor notes - DO NOT SHARE WITH STUDENTS)
This runs in 3 phases:
  1. ~60 seconds of normal traffic (establishes baseline on the graph)
  2. Creates 300 shipments to increase data volume, then repeatedly
     queries the analytics endpoint. Students should see latency
     gradually climb — not a sudden spike, but a creeping degradation.
  3. ~60 seconds of normal traffic (latency stays elevated because
     the data is still there — it doesn't "recover" like the others)
This teaches students that some problems don't recover on their own.
Total runtime: ~5 minutes.
"""

import time
import random
from client import LogisticsClient, make_item, progress

client = LogisticsClient()

MODES = ["OCEAN", "AIR", "GROUND"]
PRIORITIES = ["STANDARD", "EXPRESS", "CRITICAL"]


def normal_traffic(duration):
    """Generate steady-state traffic for the given duration."""
    start = time.time()
    while time.time() - start < duration:
        endpoint = random.choice(["shipments", "customers", "carriers", "summary"])
        if endpoint == "shipments":
            client.get_shipments()
        elif endpoint == "customers":
            client.get_customers()
        elif endpoint == "carriers":
            client.get_carriers()
        else:
            client.get_analytics_summary()

        time.sleep(random.uniform(0.8, 1.2))


def main():
    progress("=" * 60)
    progress("SCENARIO 5 - Gradual Degradation")
    progress("This script runs normal traffic, then causes a problem,")
    progress("then continues with normal traffic.")
    progress("Watch your Grafana dashboard — this one is subtle.")
    progress("Total runtime: ~5 minutes")
    progress("=" * 60)
    print()

    client.wait_for_ready()

    # Get routes
    routes = client.get_routes()

    # Create a high-credit customer
    suffix = int(time.time()) % 10000
    r = client.create_customer(
        f"DataVolume Corp {suffix}",
        f"Volume Tester {suffix}",
        f"volume{suffix}@datatest.example.com",
        credit_limit=99999999,
    )
    if r.status_code == 201:
        big_customer = r.json()
    else:
        customers_data = client.get_customers()
        big_customer = [c for c in customers_data["content"] if c["accountStatus"] == "ACTIVE"][0]

    # Phase 1: Normal traffic
    progress("PHASE 1: Generating normal baseline traffic (~60 seconds)...")
    progress("(This gives Grafana something to show as 'healthy')")
    print()

    normal_traffic(60)

    progress("Baseline phase complete.")
    print()

    # Phase 2: Build up data volume then query analytics repeatedly
    progress("PHASE 2: Triggering the problem...")
    progress("(This one takes longer to set up — watch for gradual change)")
    print()

    progress("  Creating 300 shipments to increase data volume...")
    created = 0

    for i in range(300):
        mode = random.choice(MODES)
        compatible_routes = [r for r in routes if r["transportMode"] == mode]
        if not compatible_routes:
            continue
        route = random.choice(compatible_routes)

        items = [make_item(
            description=f"Volume test item {i}",
            quantity=random.randint(1, 50),
            weight=random.randint(100, 5000),
        )]

        r = client.create_shipment(
            customer_id=big_customer["id"],
            route_id=route["id"],
            transport_mode=mode,
            total_weight=random.randint(100, 5000),
            declared_value=random.randint(100, 5000),
            items=items,
            priority=random.choice(PRIORITIES),
        )

        if r.status_code == 201:
            created += 1
            shipment = r.json()

            if random.random() < 0.6:
                client.create_tracking_event(
                    shipment["id"], "BOOKED", "Office", "system"
                )
            if random.random() < 0.3:
                client.create_tracking_event(
                    shipment["id"], "PICKED_UP", "Warehouse", "driver"
                )
                client.create_tracking_event(
                    shipment["id"], "IN_TRANSIT", "Port", "terminal-ops"
                )

        if (i + 1) % 100 == 0:
            progress(f"  Created {i+1}/300 shipments...")

        time.sleep(0.05)

    progress(f"  {created} shipments created.")
    print()

    # Now query analytics repeatedly to show degradation
    progress("  Querying analytics endpoint repeatedly...")
    for i in range(25):
        client.get_analytics_summary()
        time.sleep(0.5)

    print()
    progress("Problem phase complete.")
    print()

    # Phase 3: Normal traffic (but latency stays elevated)
    progress("PHASE 3: Returning to normal traffic (~60 seconds)...")
    progress("(Does the dashboard fully recover? Pay attention...)")
    print()

    normal_traffic(60)

    print()
    progress("=" * 60)
    progress("SCENARIO 5 COMPLETE")
    progress("Look at your Grafana dashboard. You should see:")
    progress("  - A flat period (normal latency)")
    progress("  - Latency gradually increasing")
    progress("  - Latency stays elevated even after 'normal' traffic resumes")
    progress("")
    progress("Why didn't it recover? The data is still there.")
    progress("Investigate: Which endpoint is slow now?")
    progress("=" * 60)


if __name__ == "__main__":
    main()

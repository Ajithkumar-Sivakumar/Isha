"""
Scenario 1 - Slow shipment lookups for a major customer.

(Instructor notes - DO NOT SHARE WITH STUDENTS)
This runs in 3 phases:
  1. ~60 seconds of normal traffic (establishes baseline on the graph)
  2. Creates a customer with 200 shipments, then hammers the customer
     shipments endpoint. This triggers N+1-like query behavior and shows
     how data volume affects endpoint performance. Only ONE endpoint is
     slow — students need to break down by uri to find it.
  3. ~60 seconds of normal traffic (shows recovery)
Total runtime: ~4 minutes.
"""

import time
import random
from client import LogisticsClient, make_item, progress

client = LogisticsClient()


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
    progress("SCENARIO 1 - Slow Endpoint")
    progress("This script runs normal traffic, then triggers a problem,")
    progress("then returns to normal traffic.")
    progress("Watch your Grafana dashboard — look for changes in P95 Latency.")
    progress("Total runtime: ~4 minutes")
    progress("=" * 60)
    print()

    client.wait_for_ready()

    # Phase 1: Normal traffic
    progress("PHASE 1: Generating normal baseline traffic (~60 seconds)...")
    progress("(This gives Grafana something to show as 'healthy')")
    print()

    normal_traffic(60)

    progress("Baseline phase complete.")
    print()

    # Phase 2: Create a large customer and hammer the slow endpoint
    progress("PHASE 2: Triggering the problem...")
    progress("(Watch the P95 Latency panel on your dashboard)")
    print()

    # Get a route for creating shipments
    routes = client.get_routes()
    ocean_routes = [r for r in routes if r["transportMode"] == "OCEAN"]
    route = ocean_routes[0]

    # Create a dedicated customer
    suffix = int(time.time()) % 10000
    r = client.create_customer(
        f"MegaCorp International {suffix}",
        f"Operations {suffix}",
        f"ops{suffix}@megacorp.example.com",
        credit_limit=99999999,
    )
    if r.status_code != 201:
        progress(f"Failed to create customer: {r.status_code}")
        return
    customer = r.json()
    customer_id = customer["id"]

    # Create 200 shipments for this customer
    progress("  Building up shipment history...")
    created = 0
    for i in range(200):
        items = [make_item(description=f"Batch item {i}", quantity=1, weight=100)]
        r = client.create_shipment(
            customer_id=customer_id,
            route_id=route["id"],
            transport_mode="OCEAN",
            total_weight=100,
            declared_value=100,
            items=items,
        )
        if r.status_code == 201:
            created += 1
        if (i + 1) % 50 == 0:
            progress(f"  Created {i + 1}/200 shipments...")
        time.sleep(0.05)

    progress(f"  {created} shipments created. Now querying repeatedly...")
    print()

    # Hammer the customer shipments endpoint
    for i in range(40):
        client.get_customer_shipments(customer_id, page=0, size=50)
        time.sleep(0.4)

    print()
    progress("Problem phase complete.")
    print()

    # Phase 3: Return to normal traffic
    progress("PHASE 3: Returning to normal traffic (~60 seconds)...")
    progress("(Watch the dashboard recover)")
    print()

    normal_traffic(60)

    print()
    progress("=" * 60)
    progress("SCENARIO 1 COMPLETE")
    progress("Look at your Grafana dashboard. You should see:")
    progress("  - A flat period (normal latency)")
    progress("  - A spike in P95 latency (the problem)")
    progress("  - A return to normal")
    progress("")
    progress("Investigate: Which endpoint was slow? Why?")
    progress("=" * 60)


if __name__ == "__main__":
    main()

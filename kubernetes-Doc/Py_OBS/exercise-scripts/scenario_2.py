"""
Scenario 2 - Slow external service (customs submissions).

(Instructor notes - DO NOT SHARE WITH STUDENTS)
This runs in 3 phases:
  1. ~60 seconds of normal traffic (establishes baseline on the graph)
  2. Prepares shipments then submits customs declarations which hit a
     simulated external API with variable latency (200ms to 10s).
     Students should see P95 latency spike on the customs endpoint.
  3. ~60 seconds of normal traffic (shows recovery)
Students should investigate using Tempo traces to find the slow spans.
Total runtime: ~3-4 minutes.
"""

import time
import random
import threading
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


def prepare_shipment_for_customs(route, customer_id, index):
    """Create a shipment and move it to a state suitable for customs."""
    items = [make_item(description=f"Import goods batch {index}", quantity=5, weight=1000)]
    r = client.create_shipment(
        customer_id=customer_id,
        route_id=route["id"],
        transport_mode="OCEAN",
        total_weight=1000,
        declared_value=1000,
        items=items,
    )
    if r.status_code != 201:
        return None
    shipment = r.json()

    client.create_tracking_event(shipment["id"], "BOOKED", "Office", "system")
    time.sleep(0.05)

    return shipment


def submit_declaration(shipment, index, results):
    """Submit a customs declaration (runs in a thread)."""
    r = client.create_customs_declaration(
        shipment["id"], "IMPORT", total_declared_value=1000
    )
    if r.status_code != 201:
        results.append((index, "create_failed", r.status_code, 0))
        return

    declaration = r.json()
    decl_id = declaration["id"]

    start = time.time()
    r = client.submit_customs_declaration(decl_id)
    elapsed_ms = (time.time() - start) * 1000
    results.append((index, "submitted", r.status_code, elapsed_ms))


def main():
    progress("=" * 60)
    progress("SCENARIO 2 - Slow Requests")
    progress("This script runs normal traffic, then triggers a problem,")
    progress("then returns to normal traffic.")
    progress("Watch your Grafana dashboard — look for changes in P95 Latency.")
    progress("Total runtime: ~3-4 minutes")
    progress("=" * 60)
    print()

    client.wait_for_ready()

    # Load resources
    routes = client.get_routes()
    ocean_routes = [r for r in routes if r["transportMode"] == "OCEAN"]
    route = ocean_routes[0]

    # Create a high-credit customer for this scenario
    suffix = int(time.time()) % 10000
    r = client.create_customer(
        f"Customs Testing Corp {suffix}",
        f"Import Manager {suffix}",
        f"imports{suffix}@customstest.example.com",
        credit_limit=99999999,
    )
    if r.status_code == 201:
        customer = r.json()
    else:
        customer = client.get_customer_by_name("Pacific Electronics")
        if not customer:
            progress("ERROR: Could not find a customer. Is data seeded?")
            return
    customer_id = customer["id"]

    # Phase 1: Normal traffic
    progress("PHASE 1: Generating normal baseline traffic (~60 seconds)...")
    progress("(This gives Grafana something to show as 'healthy')")
    print()

    normal_traffic(60)

    progress("Baseline phase complete.")
    print()

    # Phase 2: Slow customs submissions
    progress("PHASE 2: Triggering the problem...")
    progress("(Watch the P95 Latency panel on your dashboard)")
    print()

    progress("  Preparing shipments for customs submission...")
    shipments = []
    for i in range(15):
        s = prepare_shipment_for_customs(route, customer_id, i)
        if s:
            shipments.append(s)
        time.sleep(0.1)

    progress(f"  {len(shipments)} shipments ready. Submitting customs declarations...")
    print()

    results = []
    threads = []
    for i, shipment in enumerate(shipments):
        t = threading.Thread(target=submit_declaration, args=(shipment, i, results))
        threads.append(t)
        t.start()
        time.sleep(0.3)

    for t in threads:
        t.join(timeout=30)

    slow_count = sum(1 for _, _, _, ms in results if ms > 3000)
    print()
    progress(f"Problem phase complete: {slow_count}/{len(results)} requests were slow (>3s)")
    print()

    # Phase 3: Return to normal traffic
    progress("PHASE 3: Returning to normal traffic (~60 seconds)...")
    progress("(Watch the dashboard recover)")
    print()

    normal_traffic(60)

    print()
    progress("=" * 60)
    progress("SCENARIO 2 COMPLETE")
    progress("Look at your Grafana dashboard. You should see:")
    progress("  - A flat period (normal latency)")
    progress("  - A spike in P95 latency (the slow requests)")
    progress("  - A return to normal")
    progress("")
    progress("Now investigate: WHY were those requests slow?")
    progress("Hint: Check Tempo traces for long spans.")
    progress("=" * 60)


if __name__ == "__main__":
    main()

"""
Scenario 3 - Buggy endpoint causing 500 errors.

(Instructor notes - DO NOT SHARE WITH STUDENTS)
This runs in 3 phases:
  1. ~60 seconds of normal traffic (establishes baseline on the graph)
  2. Repeatedly hits the /analytics/shipments/carrier-performance endpoint
     which has a NullPointerException bug (it calls .getCarrier().getName()
     on shipments that have no carrier assigned). Every call returns 500.
  3. ~60 seconds of normal traffic (shows recovery)
Students should see a clear spike in 5xx errors on their Error Rate panel,
then investigate logs to find the NullPointerException stack trace.
Total runtime: ~3 minutes.
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
    progress("SCENARIO 3 - Application Error")
    progress("This script runs normal traffic, then triggers a problem,")
    progress("then returns to normal traffic.")
    progress("Watch your Grafana dashboard — look for changes in the Error Rate.")
    progress("Total runtime: ~3 minutes")
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

    # Phase 2: Hit the buggy endpoint repeatedly
    progress("PHASE 2: Triggering the problem...")
    progress("(Watch the Error Rate panel on your dashboard)")
    print()

    errors = 0
    successes = 0

    for i in range(30):
        r = client.get_carrier_performance()
        if r.status_code >= 500:
            errors += 1
        else:
            successes += 1
        time.sleep(0.5)

    print()
    progress(f"Problem phase complete: {successes} succeeded, {errors} returned 500")
    print()

    # Phase 3: Return to normal traffic
    progress("PHASE 3: Returning to normal traffic (~60 seconds)...")
    progress("(Watch the dashboard recover)")
    print()

    normal_traffic(60)

    print()
    progress("=" * 60)
    progress("SCENARIO 3 COMPLETE")
    progress("Look at your Grafana dashboard. You should see:")
    progress("  - A flat period (normal traffic, no errors)")
    progress("  - A spike in 5xx errors (the problem)")
    progress("  - A return to normal (recovery)")
    progress("")
    progress("Now investigate: What caused the 500s? Check the logs!")
    progress("=" * 60)


if __name__ == "__main__":
    main()

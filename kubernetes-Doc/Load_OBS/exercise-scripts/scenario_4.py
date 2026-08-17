"""
Scenario 4 - Traffic spike.

(Instructor notes - DO NOT SHARE WITH STUDENTS)
This runs in 3 phases:
  1. ~60 seconds of normal traffic (establishes baseline on the graph)
  2. 500 concurrent requests across 50 threads in ~10 seconds (the spike)
  3. ~60 seconds of normal traffic (shows recovery)
Students just run this one script and see the full before/during/after story
on their Grafana dashboard. Total runtime: ~3 minutes.
"""

import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from client import LogisticsClient, progress

client = LogisticsClient()


def random_request(request_num):
    """Send a random API request and return timing info."""
    start = time.time()
    endpoint = random.choice([
        "get_shipments",
        "get_shipments",
        "get_shipments",
        "get_customers",
        "get_carriers",
        "get_routes",
        "get_ports",
        "get_analytics",
    ])

    try:
        if endpoint == "get_shipments":
            r = client.get_shipments(page=0, size=20)
        elif endpoint == "get_customers":
            r = client.get_customers()
        elif endpoint == "get_carriers":
            r = client.get_carriers()
        elif endpoint == "get_routes":
            r = client.get_routes()
        elif endpoint == "get_ports":
            r = client.get_ports()
        elif endpoint == "get_analytics":
            r = client.get_analytics_summary()
        else:
            r = client.get_shipments()

        elapsed_ms = (time.time() - start) * 1000
        status = r.status_code if hasattr(r, 'status_code') else 0
        return (request_num, endpoint, status, elapsed_ms)
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return (request_num, endpoint, 0, elapsed_ms)


def main():
    progress("=" * 60)
    progress("SCENARIO 4 - Traffic Spike")
    progress("This script runs normal traffic, then a burst, then normal again.")
    progress("Watch your Grafana dashboard — you'll see the spike clearly.")
    progress("Total runtime: ~3 minutes")
    progress("=" * 60)
    print()

    client.wait_for_ready()

    # Phase 1: Normal traffic to establish baseline on the graph
    progress("PHASE 1: Generating normal baseline traffic (~60 seconds)...")
    progress("(This gives Grafana something to show as 'healthy')")
    print()

    baseline_start = time.time()
    baseline_duration = 60
    while time.time() - baseline_start < baseline_duration:
        random_request(0)
        time.sleep(random.uniform(0.8, 1.2))

    progress("Baseline phase complete.")
    print()

    # Measure baseline latency for comparison
    progress("Measuring baseline latency (5 requests)...")
    baseline_times = []
    for i in range(5):
        start = time.time()
        client.get_shipments()
        baseline_times.append((time.time() - start) * 1000)
    avg_baseline = sum(baseline_times) / len(baseline_times)
    progress(f"Baseline: avg={avg_baseline:.0f}ms")
    print()

    # Phase 2: Traffic burst
    progress("PHASE 2: Sending traffic burst — 500 requests across 50 threads...")
    progress("(Watch Grafana NOW — you should see all panels react)")
    print()

    total_requests = 500
    max_workers = 50
    results = []

    burst_start = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(total_requests):
            futures.append(executor.submit(random_request, i))
            time.sleep(0.02)  # spread slightly over ~10s

        for future in as_completed(futures):
            results.append(future.result())
    burst_elapsed = time.time() - burst_start

    # Analyze results
    latencies = [r[3] for r in results]
    statuses = [r[2] for r in results]

    success = sum(1 for s in statuses if 200 <= s < 300)
    client_errors = sum(1 for s in statuses if 400 <= s < 500)
    server_errors = sum(1 for s in statuses if s >= 500)
    connection_errors = sum(1 for s in statuses if s == 0)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
    p99 = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
    max_latency = max(latencies) if latencies else 0

    print()
    progress("Burst complete!")
    progress(f"  Duration: {burst_elapsed:.1f}s")
    progress(f"  Total requests: {total_requests}")
    progress(f"  Successful (2xx): {success}")
    progress(f"  Client errors (4xx): {client_errors}")
    progress(f"  Server errors (5xx): {server_errors}")
    progress(f"  Connection errors: {connection_errors}")
    print()
    progress(f"  Latency - avg: {avg_latency:.0f}ms, p95: {p95:.0f}ms, p99: {p99:.0f}ms, max: {max_latency:.0f}ms")
    progress(f"  Baseline was: {avg_baseline:.0f}ms")
    progress(f"  Latency increased by: {(avg_latency / avg_baseline):.1f}x" if avg_baseline > 0 else "")

    # After the burst, show recovery
    print()
    progress("PHASE 3: Returning to normal traffic (~60 seconds)...")
    progress("(Watch the dashboard recover back to baseline)")
    print()

    recovery_start = time.time()
    recovery_duration = 60
    while time.time() - recovery_start < recovery_duration:
        random_request(0)
        time.sleep(random.uniform(0.8, 1.2))

    # Final measurement
    progress("Measuring post-recovery latency...")
    recovery_times = []
    for i in range(5):
        start = time.time()
        client.get_shipments()
        recovery_times.append((time.time() - start) * 1000)
    avg_recovery = sum(recovery_times) / len(recovery_times)
    progress(f"Recovery: avg={avg_recovery:.0f}ms (baseline was {avg_baseline:.0f}ms)")

    print()
    progress("=" * 60)
    progress("SCENARIO 4 COMPLETE")
    progress("Look at your Grafana dashboard. You should see:")
    progress("  - A flat period (normal traffic)")
    progress("  - A spike (the burst)")
    progress("  - A return to normal (recovery)")
    progress("=" * 60)


if __name__ == "__main__":
    main()

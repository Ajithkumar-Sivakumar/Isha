"""
Scenario 6 - Broken observability (missing correlation IDs).

(Instructor notes - DO NOT SHARE WITH STUDENTS)
This sends a mix of requests: some with proper X-Correlation-ID headers,
some with empty/garbage correlation IDs, and some without the header at all.
Students should notice in Loki that some requests are untraceable because
they lack a consistent correlation ID. This demonstrates why correlation
standards matter for debugging in production.
"""

import time
import uuid
import random
from client import LogisticsClient, progress

client = LogisticsClient()


def request_with_header(header_value):
    """Send a GET /shipments with a specific X-Correlation-ID header."""
    headers = {}
    if header_value is not None:
        headers["X-Correlation-ID"] = header_value
    return client._get("/shipments", headers=headers)


def request_customers_with_header(header_value):
    """Send a GET /customers with a specific X-Correlation-ID header."""
    headers = {}
    if header_value is not None:
        headers["X-Correlation-ID"] = header_value
    return client._get("/customers", headers=headers)


def main():
    progress("=" * 60)
    progress("SCENARIO 6 - Running...")
    progress("(Sending requests with various correlation ID patterns)")
    progress("=" * 60)
    print()

    client.wait_for_ready()

    progress("Sending 60 requests with mixed correlation ID behavior...")
    progress("(Some valid, some empty, some missing, some garbage)")
    print()

    valid_count = 0
    empty_count = 0
    missing_count = 0
    garbage_count = 0

    for i in range(60):
        choice = random.random()

        if choice < 0.3:
            # Valid correlation ID
            corr_id = str(uuid.uuid4())
            request_with_header(corr_id)
            valid_count += 1
            label = f"valid ({corr_id[:8]}...)"
        elif choice < 0.5:
            # Empty string
            request_with_header("")
            empty_count += 1
            label = "empty string"
        elif choice < 0.7:
            # No header at all
            request_with_header(None)
            missing_count += 1
            label = "no header"
        elif choice < 0.85:
            # Garbage value
            garbage = random.choice(["null", "undefined", "N/A", "test", "123", "xxx"])
            request_with_header(garbage)
            garbage_count += 1
            label = f"garbage ('{garbage}')"
        else:
            # Valid but reused (same ID for multiple requests - wrong pattern)
            shared_id = "reused-id-00000000-0000-0000-0000-000000000000"
            request_with_header(shared_id)
            request_customers_with_header(shared_id)
            valid_count += 1
            label = "reused ID (bad practice)"

        if (i + 1) % 10 == 0:
            progress(f"  Sent {i+1}/60 requests...")

        time.sleep(0.3)

    print()
    progress("Request breakdown:")
    progress(f"  Valid correlation IDs: {valid_count}")
    progress(f"  Empty string: {empty_count}")
    progress(f"  No header (missing): {missing_count}")
    progress(f"  Garbage values: {garbage_count}")
    print()
    progress("=" * 60)
    progress("SCENARIO 6 COMPLETE")
    progress("Now try to trace a request through Loki:")
    progress("  - Search for a valid correlationId - you'll find it easily")
    progress("  - Try to find the requests with empty/missing IDs - much harder!")
    progress("  - Notice how 'reused-id-...' shows unrelated requests grouped together")
    progress("This is why consistent correlation ID standards matter.")
    progress("=" * 60)


if __name__ == "__main__":
    main()

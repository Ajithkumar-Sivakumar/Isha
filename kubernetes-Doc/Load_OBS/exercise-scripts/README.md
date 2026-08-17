# Observability Exercise Scripts

These scripts simulate production traffic patterns against the Logistics API. Your job is to use **Grafana** (dashboards, Loki logs, Tempo traces, Prometheus metrics) to figure out what's happening.

## Setup

Make sure the API is running:

```bash
docker compose up -d --build
```

Then install the script dependency:

```bash
cd exercise-scripts
pip install -r requirements.txt
```

---

## How to Use

### Step 1: Establish a Baseline

Run the normal traffic script first. This generates ~2 minutes of healthy operations so you can see what "normal" looks like in Grafana.

```bash
python normal_traffic.py
```

While it runs, open Grafana at http://localhost:3000 (admin/admin) and explore:
- **Prometheus** metrics (request rates, latency histograms)
- **Loki** logs (structured JSON, correlation IDs)
- **Tempo** traces (request spans, database queries)

Take note of what baseline latency looks like, what error rates look like (should be near zero), and how logs flow normally.

### Step 2: Run a Scenario

Your instructor will tell you which scenario to run. Each one simulates a different production problem. You do NOT know what the script does internally. Your job is to investigate using the observability tools and figure out:

1. **What** is happening? (Which endpoint/service is affected?)
2. **When** did it start? (Can you see the change point in metrics?)
3. **Why** is it happening? (What do logs/traces reveal about the root cause?)

---

## IMPORTANT: Reset Between Scenarios

Each scenario modifies the database. You MUST reset before running a different scenario, or the data from one scenario will interfere with the next.

```bash
bash reset.sh
```

This takes about 30 seconds. It stops all containers, wipes the database and Prometheus metrics, and restarts everything with fresh seed data. **Your Grafana dashboards are preserved.**

**Always reset before switching to a new scenario.**

---

## Scenarios

### Scenario 1

> "We're getting reports from customer support that one of our largest customers is experiencing very slow load times when viewing their shipment history. Other customers seem fine. Investigate."

```bash
python scenario_1.py
```

### Scenario 2

> "The customs team is reporting that declaration submissions are taking much longer than usual. Some are timing out entirely. The rest of the API seems fine. Investigate."

```bash
python scenario_2.py
```

### Scenario 3

> "Operations just flagged that a lot of carrier assignment requests are failing this morning. They say they haven't changed their process. Figure out what's happening."

```bash
python scenario_3.py
```

### Scenario 4

> "Multiple teams are reporting that the entire API feels sluggish. It's not just one endpoint -- everything is slower than usual. What's going on?"

```bash
python scenario_4.py
```

### Scenario 5

> "The analytics dashboard that management uses is loading extremely slowly today. It was fine yesterday. Nothing was deployed. Investigate."

```bash
python scenario_5.py
```

### Scenario 6

> "A developer is trying to trace a customer complaint through our logs but can't find the request. They have the timestamp but no correlation ID appears in Loki. Look at the recent traffic patterns and figure out what's wrong with our observability."

```bash
python scenario_6.py
```

---

## Where to Look in Grafana

| Tool | What it shows | How to access |
|------|--------------|---------------|
| **Prometheus** | Request rates, latency percentiles, error rates | Grafana > Explore > select Prometheus datasource |
| **Loki** | Application logs (JSON structured) | Grafana > Explore > select Loki datasource |
| **Tempo** | Distributed traces (request lifecycle) | Grafana > Explore > select Tempo datasource |

### Golden Signals dashboard queries (Flask/Python)

Build these four panels in Grafana (students build the dashboard in class):

| Panel | Query | Unit |
|-------|-------|------|
| Request Rate | `sum(rate(http_server_requests_seconds_count[$__rate_interval]))` | reqps |
| P95 Latency | `histogram_quantile(0.95, sum(rate(http_server_requests_seconds_bucket[$__rate_interval])) by (le))` | seconds |
| Error Rate | `sum(rate(http_server_requests_seconds_count{status=~"5.."}[$__rate_interval]))` | reqps |
| Saturation | `process_resident_memory_bytes` | bytes (IEC) |

To isolate a slow endpoint (Scenario 1), add `by (uri)` to the P95 query.

### Useful Loki queries (Flask/Python)

After `docker compose up`, verify labels in Grafana Explore or with:

```bash
curl -s http://localhost:3100/loki/api/v1/labels
```

Typical Docker service discovery label for app logs:

```
{service_name="/observability-app-1"}
```

Examples:

- All app logs: `{service_name="/observability-app-1"}`
- Errors only: `{service_name="/observability-app-1"} |= "ERROR"`
- By correlation ID: `{service_name="/observability-app-1"} |= "correlationId"`
- Scenario 3 stack traces: `{service_name="/observability-app-1"} |= "AttributeError"`

If `service` appears as a parsed JSON label, you can also try `{service="logistics-api"}`.

### Useful Prometheus queries

- Request rate: `sum(rate(http_server_requests_seconds_count[$__rate_interval]))`
- P95 latency: `histogram_quantile(0.95, sum(rate(http_server_requests_seconds_bucket[$__rate_interval])) by (le))`
- Error rate: `sum(rate(http_server_requests_seconds_count{status=~"5.."}[$__rate_interval]))`
- Per-endpoint latency: `histogram_quantile(0.95, sum(rate(http_server_requests_seconds_bucket[$__rate_interval])) by (le, uri))`

---

## Tips

- Set the Grafana time range to "Last 15 minutes" so you're focused on recent activity
- Use "Compare" in Prometheus to overlay before/during the scenario
- In Tempo, sort traces by duration to find the slowest requests
- In Loki, search for specific error codes like `CARRIER_CAPACITY_EXCEEDED` or `INVALID_STATE_TRANSITION`
- The correlation ID links logs to traces — if you find a suspicious log entry, grab its correlationId and search Tempo for that trace
- Scripts use `http://127.0.0.1:5000` (not `localhost`) to avoid Windows/WSL IPv6 issues

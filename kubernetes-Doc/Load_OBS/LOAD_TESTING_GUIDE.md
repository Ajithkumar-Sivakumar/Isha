# 🚀 Load Testing & Scenario Execution Guide

## ✅ API Status: READY FOR TESTING

All endpoints are working and returning data. The API is running on **http://localhost:5000**

---

## 📊 Available Test Collections

### Insomnia Collections
Found in your project:
- `insomnia-collection.json` - Postman/Insomnia format
- `insomnia-collection_python.json` - Python API documentation format

---

## 🧪 How to Run Load Tests

### Option 1: Using Apache JMeter (Recommended)

#### Prerequisites:
```bash
# Check if JMeter is installed
jmeter --version

# If not installed:
# macOS
brew install jmeter

# Or download from: https://jmeter.apache.org/download_jmeter.cgi
```

#### Create a JMeter Test Plan:
```bash
jmeter -n -t your_test_plan.jmx -l results.csv -j jmeter.log -Jhost=localhost -Jport=5000
```

#### Sample Test Scenarios:

**1. Simple Load Test (100 users, 10 ramp-up seconds)**
```bash
# Create test_plan.jmx and run with:
jmeter -n -t test_plan.jmx -l load_test.csv -Jusers=100 -Jrampup=10 -Jduration=60
```

**2. Stress Test (gradually increase load)**
```bash
jmeter -n -t stress_test.jmx -l stress_results.csv -Jstartheap=512m -Jmaxheap=2048m
```

---

### Option 2: Using Apache Bench (Simple load testing)

```bash
# Test single endpoint with 1000 requests, 10 concurrent
ab -n 1000 -c 10 http://localhost:5000/api/v1/shipments

# Output will show:
# - Requests per second
# - Time per request
# - Failed requests
# - Throughput
```

---

### Option 3: Using curl with loop (Quick test)

```bash
# Test health endpoint 100 times
for i in {1..100}; do
  curl -s http://localhost:5000/health
done

# Test with time measurement
time for i in {1..50}; do
  curl -s http://localhost:5000/api/v1/shipments > /dev/null
done
```

---

### Option 4: Using Python (Load Testing Script)

```python
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, stdev

BASE_URL = "http://localhost:5000"

def test_endpoint(url):
    start = time.time()
    try:
        response = requests.get(url, timeout=5)
        return time.time() - start, response.status_code
    except Exception as e:
        return time.time() - start, 500

# Test parameters
endpoint = f"{BASE_URL}/api/v1/shipments"
num_requests = 100
num_threads = 10

print(f"Testing {endpoint}")
print(f"Total Requests: {num_requests}")
print(f"Concurrent Threads: {num_threads}")
print("-" * 50)

start_time = time.time()
response_times = []
status_codes = []

with ThreadPoolExecutor(max_workers=num_threads) as executor:
    futures = [executor.submit(test_endpoint, endpoint) for _ in range(num_requests)]
    for future in futures:
        duration, status = future.result()
        response_times.append(duration)
        status_codes.append(status)

total_time = time.time() - start_time

# Results
successful = sum(1 for s in status_codes if s == 200)
print(f"\nResults:")
print(f"Total Time: {total_time:.2f}s")
print(f"Successful Requests: {successful}/{num_requests}")
print(f"Average Response Time: {mean(response_times)*1000:.2f}ms")
print(f"Min Response Time: {min(response_times)*1000:.2f}ms")
print(f"Max Response Time: {max(response_times)*1000:.2f}ms")
print(f"Requests/Second: {num_requests/total_time:.2f}")
if len(response_times) > 1:
    print(f"Std Dev: {stdev(response_times)*1000:.2f}ms")
```

Save as `load_test.py` and run:
```bash
python3 load_test.py
```

---

### Option 5: Using Grafana Dashboards (Monitor in Real-time)

1. Open Grafana: **http://localhost:3000**
   - Default credentials: admin/admin
2. Navigate to Dashboards
3. View real-time metrics while running load tests
4. Monitor:
   - Request rate
   - Response times
   - Error rates
   - Database performance

---

## 📝 Scenario Testing Examples

### Scenario 1: Customer Order Workflow
```bash
# 1. Create customer
curl -X POST http://localhost:5000/api/v1/customers \
  -H "Content-Type: application/json" \
  -d '{
    "companyName": "Test Company",
    "contactName": "John Doe",
    "contactEmail": "john@test.com",
    "country": "US"
  }'

# 2. List shipments
curl http://localhost:5000/api/v1/shipments

# 3. Get specific shipment
curl http://localhost:5000/api/v1/shipments/[shipment-id]

# 4. Get analytics
curl http://localhost:5000/api/v1/analytics/shipments/summary
```

### Scenario 2: Multiple Concurrent Requests
```bash
# Run 50 concurrent requests to different endpoints
for i in {1..50}; do
  curl -s http://localhost:5000/api/v1/customers &
  curl -s http://localhost:5000/api/v1/shipments &
  curl -s http://localhost:5000/api/v1/carriers &
done
wait
```

---

## 🔍 Monitoring During Tests

### View Logs in Real-time:
```bash
docker compose logs -f app
```

### Monitor Metrics:
```bash
# Prometheus metrics (raw)
curl http://localhost:9090/api/v1/targets

# InfluxDB time-series data
curl http://localhost:8086/query?db=main&q=SELECT * FROM measurements
```

### Check Grafana:
- URL: http://localhost:3000
- Dashboards show:
  - Request rates
  - Response times
  - Error rates
  - Database queries
  - System resources

---

## 📊 Key Metrics to Monitor

During load testing, watch these metrics:

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Response Time (avg) | < 100ms | > 200ms | > 500ms |
| Requests/sec | High | Dropping | Errors |
| Error Rate | 0% | > 1% | > 5% |
| CPU Usage | < 70% | > 80% | > 95% |
| Memory Usage | < 70% | > 80% | > 95% |
| DB Connections | < 50% | > 70% | > 90% |

---

## ✅ API Endpoints Ready for Testing

**Base URL:** `http://localhost:5000`

| Endpoint | Method | Purpose | Load Test Suitable |
|----------|--------|---------|-------------------|
| `/health` | GET | Health check | ✅ Yes (baseline) |
| `/api/v1/customers` | GET | List customers | ✅ Yes |
| `/api/v1/shipments` | GET | List shipments | ✅ Yes |
| `/api/v1/carriers` | GET | List carriers | ✅ Yes |
| `/api/v1/ports` | GET | List ports | ✅ Yes |
| `/api/v1/routes` | GET | List routes | ✅ Yes |
| `/api/v1/customs` | GET | List customs | ✅ Yes |
| `/api/v1/analytics` | GET | Analytics | ✅ Yes |

---

## 🚀 Quick Start Load Test

```bash
# 1. Open terminal
# 2. Run this simple load test
cd /Users/official/Documents/Isha/kubernetes-Doc/ObservabilityShipping_Python_Jmeter

# Install Apache Bench if needed (macOS)
# brew install httpd

# Run 1000 requests, 10 concurrent to main endpoint
ab -n 1000 -c 10 http://localhost:5000/api/v1/shipments

# Results will show performance metrics
```

---

## 📌 Important Notes

1. ✅ All endpoints are operational
2. ✅ Database is populated with test data
3. ✅ Monitoring stack is running
4. ✅ Observability is enabled (logging, tracing, metrics)
5. ⚠️ Start with low load (10-50 concurrent) then increase
6. ⚠️ Monitor Grafana during tests
7. ⚠️ Check logs for any errors

---

## 🎯 Test Recommendations

1. **First Run:** Use `ab` for quick baseline
2. **Load Test:** Use JMeter for complex scenarios (100-500 users)
3. **Stress Test:** Gradually increase users until system breaks
4. **Monitor:** Watch Grafana dashboards in real-time
5. **Document:** Save results for analysis

---

**Status: API is ready for comprehensive load and scenario testing! 🎉**

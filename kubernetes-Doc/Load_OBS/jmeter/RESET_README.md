# JMeter Reset Scripts

This directory contains scripts to reset the JMeter InfluxDB data between load test runs.

## 📋 Overview

When you run a JMeter load test, all metrics (response times, throughput, errors, etc.) are written to InfluxDB. Over time, this data accumulates. The reset scripts allow you to:

- ✅ Clear old load test data from InfluxDB
- ✅ Recreate a fresh `jmeter` database
- ✅ Start a new load test run with a clean slate

This is useful when:
- You want to compare different test scenarios without old data interfering
- The dashboard becomes cluttered with old results
- You're re-running the same test for baseline comparison
- You want to start the day with fresh metrics

---

## 📁 Files

| File | OS | Purpose |
|------|----|----|
| `reset.sh` | Linux / macOS / WSL | Bash script to reset InfluxDB |
| `reset.ps1` | Windows (PowerShell) | PowerShell script to reset InfluxDB |

---

## 🚀 Usage

### Bash (Linux / macOS / WSL)

```bash
cd jmeter
chmod +x reset.sh
./reset.sh
```

### PowerShell (Windows)

```powershell
cd jmeter
.\reset.ps1
```

---

## 📊 What the Scripts Do

1. **Check if InfluxDB is running** — starts it if needed
2. **Drop the existing `jmeter` database** — removes all old load test data
3. **Create a fresh `jmeter` database** — ready for new metrics
4. **Verify the database** — confirms the reset was successful

### Output Example

```
================================================
JMeter InfluxDB Reset Script
================================================

[1/4] Checking if InfluxDB is running...
[2/4] Dropping existing jmeter database...
[3/4] Creating fresh jmeter database...
[4/4] Verifying database creation...
✓ Success! jmeter database is ready

================================================
✓ JMeter InfluxDB reset complete!
================================================

You can now run a fresh load test:
  ./run-load-test.sh
```

---

## 💡 When to Use

### Before a new load test scenario:
```bash
./reset.sh
./run-load-test.sh logistics-baseline.jmx
```

### When switching between test plans:
```bash
./reset.sh
./run-load-test.sh logistics-spike.jmx
```

### When comparing results:
```bash
# Run baseline
./run-load-test.sh logistics-baseline.jmx
# Take screenshots of Grafana dashboard
# Reset for clean comparison
./reset.sh
# Run another scenario
./run-load-test.sh logistics-spike.jmx
```

---

## 📋 Prerequisites

- Docker must be running
- `docker compose` must be available
- InfluxDB service must be defined in `docker-compose.yml`

---

## 🔍 Verify Reset Manually

To manually check if the database was reset:

```bash
# List all databases
docker compose exec influxdb influx -execute "SHOW DATABASES"

# Query jmeter measurements
docker compose exec influxdb influx -database jmeter -execute "SHOW MEASUREMENTS"

# Count total points in jmeter database
docker compose exec influxdb influx -database jmeter -execute "SELECT COUNT(*) FROM /.*/"
```

---

## 🚨 Important Notes

⚠️ **This script DELETES all load test data** — make sure you've saved/documented any results you need before running it.

To preserve results:
1. Take screenshots of the Grafana dashboard
2. Download the HTML report from `results/` directory
3. Export the InfluxDB data if needed

---

## 📚 Workflow Example

```bash
# 1. Make sure the stack is up
docker compose up -d

# 2. Reset JMeter data
./reset.sh

# 3. Open Grafana dashboard in browser
# http://localhost:3000/d/jmeter-logistics

# 4. Run a baseline test
./run-load-test.sh logistics-baseline.jmx 10 30 300

# 5. Watch results in Grafana (last 15 minutes)

# 6. Take screenshots for documentation

# 7. Reset for next scenario
./reset.sh

# 8. Run spike test
./run-load-test.sh logistics-spike.jmx

# 9. Compare results
```

---

## ⚙️ Advanced Usage

### Reset InfluxDB without scripts

If you prefer to do it manually:

```bash
# Drop database
docker compose exec influxdb influx -execute "DROP DATABASE jmeter"

# Create database
docker compose exec influxdb influx -execute "CREATE DATABASE jmeter"
```

### Partial reset (keep some data)

To reset only data older than a certain time:

```bash
docker compose exec influxdb influx -database jmeter -execute \
  "DELETE FROM jmeter WHERE time < now() - 1h"
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `bash: reset.sh: command not found` | Run `chmod +x reset.sh` first |
| `docker compose exec` hangs | Stop and restart the stack: `docker compose down && docker compose up -d` |
| InfluxDB won't start | Check disk space: `docker system df` |
| Permission denied (PowerShell) | Set execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |

---

## 📖 Related Scripts

- `run-load-test.sh` / `run-load-test.ps1` — Run JMeter tests
- See [JMETER_LOAD_TESTING.md](../JMETER_LOAD_TESTING.md) for complete guide

---

**Status: Reset scripts ready to use** ✅

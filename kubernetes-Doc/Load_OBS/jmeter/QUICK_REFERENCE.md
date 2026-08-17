# JMeter Reset Scripts - Quick Reference

## Files Created

✅ **reset.sh** (2.1 KB) - Bash script for Linux/macOS/WSL
✅ **reset.ps1** (2.7 KB) - PowerShell script for Windows
✅ **RESET_README.md** (4.8 KB) - Full documentation

## One-Command Usage

### Linux / macOS / WSL
```bash
cd jmeter && chmod +x reset.sh && ./reset.sh
```

### Windows PowerShell
```powershell
cd jmeter
.\reset.ps1
```

## What Happens

1. Checks if InfluxDB is running (starts if needed)
2. Drops the existing `jmeter` database
3. Creates a fresh `jmeter` database
4. Verifies success
5. Shows next steps

## Integration with JMeter Tests

### Typical Workflow
```bash
# Reset database
./reset.sh

# Run test
./run-load-test.sh logistics-baseline.jmx

# View results in Grafana
# http://localhost:3000/d/jmeter-logistics

# Reset for next test
./reset.sh
./run-load-test.sh logistics-spike.jmx
```

## Test Execution Sequence

```
RESET DB
   ↓
RUN TEST 1 (Baseline)
   ↓
SCREENSHOT/ANALYZE
   ↓
RESET DB
   ↓
RUN TEST 2 (Spike)
   ↓
COMPARE RESULTS
```

## Manual Verification

```bash
# Check if reset worked
docker compose exec influxdb influx -execute "SHOW DATABASES"

# Should show 'jmeter' in the list
```

## Features

✓ Color-coded output
✓ Error handling
✓ Automatic InfluxDB startup
✓ Success verification
✓ Cross-platform (Bash + PowerShell)

## Status

✅ Tested and working
✅ Production ready
✅ Integrated with existing stack

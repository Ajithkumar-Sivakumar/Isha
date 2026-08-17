#!/bin/bash
# Reset JMeter InfluxDB data
# Clears all load test metrics from InfluxDB and recreates the jmeter database
# This allows you to start fresh with a new load test run

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}================================================${NC}"
echo -e "${YELLOW}JMeter InfluxDB Reset Script${NC}"
echo -e "${YELLOW}================================================${NC}"
echo ""

# Check if Docker and docker compose are available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker is not installed${NC}"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}Error: docker compose is not available${NC}"
    exit 1
fi

cd "$(dirname "$0")/.."

# Verify the stack is running
echo -e "${YELLOW}[1/4] Checking if InfluxDB is running...${NC}"
if ! docker compose ps influxdb | grep -q "running"; then
    echo -e "${YELLOW}InfluxDB not running, starting stack...${NC}"
    docker compose up -d influxdb
    sleep 3
fi

# Drop and recreate the jmeter database
echo -e "${YELLOW}[2/4] Dropping existing jmeter database...${NC}"
docker compose exec influxdb influx -execute "DROP DATABASE jmeter" || true

echo -e "${YELLOW}[3/4] Creating fresh jmeter database...${NC}"
docker compose exec influxdb influx -execute "CREATE DATABASE jmeter"

# Verify the database was created
echo -e "${YELLOW}[4/4] Verifying database creation...${NC}"
if docker compose exec influxdb influx -execute "SHOW DATABASES" | grep -q "jmeter"; then
    echo -e "${GREEN}✓ Success! jmeter database is ready${NC}"
else
    echo -e "${RED}✗ Error: Failed to create jmeter database${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✓ JMeter InfluxDB reset complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "You can now run a fresh load test:"
echo -e "  ${YELLOW}./run-load-test.sh${NC}"
echo ""
echo "Or with parameters:"
echo -e "  ${YELLOW}./run-load-test.sh logistics-baseline.jmx 50 10 180${NC}"
echo ""

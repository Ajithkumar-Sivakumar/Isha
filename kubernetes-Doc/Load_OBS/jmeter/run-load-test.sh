#!/usr/bin/env bash
# Runs a JMeter test plan inside Docker and streams the results to InfluxDB/Grafana.
#
# Usage:
#   ./run-load-test.sh
#   ./run-load-test.sh logistics-spike.jmx 50 10 180
set -euo pipefail

PLAN="${1:-logistics-baseline.jmx}"
THREADS="${2:-10}"
RAMPUP="${3:-30}"
DURATION="${4:-300}"

cd "$(dirname "$0")/.."

export JMETER_PLAN="$PLAN"
export THREADS RAMPUP
export TEST_DURATION="$DURATION"

echo "Making sure the stack is up..."
docker compose up -d

echo "Starting JMeter: $PLAN (threads=$THREADS rampup=$RAMPUP duration=${DURATION}s)"
echo "Watch live results: http://localhost:3000/d/jmeter-logistics"

docker compose --profile load run --rm jmeter

echo "Done. HTML report and .jtl file are in jmeter/results/"

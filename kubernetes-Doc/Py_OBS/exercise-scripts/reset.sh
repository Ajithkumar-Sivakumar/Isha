#!/bin/bash
# Reset the environment between scenarios.
# Wipes database + Prometheus metrics only. Grafana dashboards are preserved.

echo "=============================================="
echo "  RESETTING ENVIRONMENT"
echo "  This will take about 30 seconds..."
echo "=============================================="
echo ""

cd "$(dirname "$0")/.."

echo "[1/3] Stopping app and wiping database and metrics..."
docker compose down
docker volume rm observability_postgres_data 2>/dev/null || true
docker volume rm observability_prometheus_data 2>/dev/null || true

echo ""
echo "[2/3] Starting fresh containers..."
docker compose up -d

echo ""
echo "[3/3] Waiting for services to be healthy..."
sleep 25

# Verify the API is responding (Flask /health or Spring /actuator/health)
echo ""
if curl -sf http://127.0.0.1:5000/health > /dev/null 2>&1; then
    echo "=============================================="
    echo "  RESET COMPLETE"
    echo "  API is healthy. Seed data has been restored."
    echo "  You can now run a scenario script."
    echo "=============================================="
else
    echo "WARNING: API may not be ready yet."
    echo "Wait a few more seconds, then try:"
    echo "  curl http://127.0.0.1:5000/health"
fi

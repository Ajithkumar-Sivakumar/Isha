
# Reset the environment between scenarios.
# Wipes database + Prometheus metrics only. Grafana dashboards are preserved.

Write-Host "=============================================="
Write-Host "  RESETTING ENVIRONMENT"
Write-Host "  This will take about 30 seconds..."
Write-Host "=============================================="
Write-Host ""

Push-Location "$PSScriptRoot/.."

Write-Host "[1/3] Stopping app and wiping database and metrics..."
docker compose down
docker volume rm observability_postgres_data 2>$null
docker volume rm observability_prometheus_data 2>$null

Write-Host ""
Write-Host "[2/3] Starting fresh containers..."
docker compose up -d

Write-Host ""
Write-Host "[3/3] Waiting for services to be healthy..."
Start-Sleep -Seconds 25

Write-Host ""
$healthy = $false
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $healthy = $true
    }
} catch {
    $healthy = $false
}

if ($healthy) {
    Write-Host "=============================================="
    Write-Host "  RESET COMPLETE"
    Write-Host "  API is healthy. Seed data has been restored."
    Write-Host "  You can now run a scenario script."
    Write-Host "=============================================="
} else {
    Write-Host "WARNING: API may not be ready yet."
    Write-Host "Wait a few more seconds, then try opening:"
    Write-Host "  http://127.0.0.1:5000/health"
}

Pop-Location

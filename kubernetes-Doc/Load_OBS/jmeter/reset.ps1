# Reset JMeter InfluxDB data
# Clears all load test metrics from InfluxDB and recreates the jmeter database
# This allows you to start fresh with a new load test run
#
# Usage:
#   .\reset.ps1

param(
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param(
        [string]$Message,
        [ValidateSet("Green", "Red", "Yellow", "Cyan")]
        [string]$Color = "Cyan"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "================================================" "Yellow"
Write-ColorOutput "JMeter InfluxDB Reset Script (PowerShell)" "Yellow"
Write-ColorOutput "================================================" "Yellow"
Write-Host ""

# Check if Docker is available
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-ColorOutput "Error: docker is not installed" "Red"
    exit 1
}

# Navigate to parent directory (where docker-compose.yml is)
Push-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Push-Location ..

try {
    # Verify the stack is running
    Write-ColorOutput "[1/4] Checking if InfluxDB is running..." "Yellow"
    $influxStatus = docker compose ps influxdb 2>$null
    
    if ($influxStatus -notlike "*running*") {
        Write-ColorOutput "InfluxDB not running, starting stack..." "Yellow"
        docker compose up -d influxdb
        Start-Sleep -Seconds 3
    }

    # Drop and recreate the jmeter database
    Write-ColorOutput "[2/4] Dropping existing jmeter database..." "Yellow"
    docker compose exec influxdb influx -execute "DROP DATABASE jmeter" 2>$null | Out-Null
    
    Write-ColorOutput "[3/4] Creating fresh jmeter database..." "Yellow"
    docker compose exec influxdb influx -execute "CREATE DATABASE jmeter" | Out-Null

    # Verify the database was created
    Write-ColorOutput "[4/4] Verifying database creation..." "Yellow"
    $databases = docker compose exec influxdb influx -execute "SHOW DATABASES"
    
    if ($databases -like "*jmeter*") {
        Write-ColorOutput "✓ Success! jmeter database is ready" "Green"
    } else {
        Write-ColorOutput "✗ Error: Failed to create jmeter database" "Red"
        exit 1
    }

    Write-Host ""
    Write-ColorOutput "================================================" "Green"
    Write-ColorOutput "✓ JMeter InfluxDB reset complete!" "Green"
    Write-ColorOutput "================================================" "Green"
    Write-Host ""
    Write-Host "You can now run a fresh load test:"
    Write-ColorOutput "  .\run-load-test.ps1" "Yellow"
    Write-Host ""
    Write-Host "Or with parameters:"
    Write-ColorOutput "  .\run-load-test.ps1 -Plan logistics-baseline.jmx -Threads 50 -RampUp 10 -Duration 180" "Yellow"
    Write-Host ""
}
finally {
    Pop-Location
    Pop-Location
}

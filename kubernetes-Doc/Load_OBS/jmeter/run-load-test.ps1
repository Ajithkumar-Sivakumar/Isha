<#
.SYNOPSIS
    Runs a JMeter test plan inside Docker and streams the results to InfluxDB/Grafana.

.EXAMPLE
    .\run-load-test.ps1
    .\run-load-test.ps1 -Plan logistics-spike.jmx -Threads 50 -Duration 180
#>
param(
    [ValidateSet('logistics-baseline.jmx', 'logistics-spike.jmx', 'logistics-error-scenario.jmx')]
    [string]$Plan = 'logistics-baseline.jmx',

    [int]$Threads = 10,
    [int]$RampUp = 30,
    [int]$Duration = 300
)

$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

$env:JMETER_PLAN = $Plan
$env:THREADS = $Threads
$env:RAMPUP = $RampUp
$env:TEST_DURATION = $Duration

Write-Host "Making sure the stack is up..." -ForegroundColor Cyan
docker compose up -d

Write-Host "Starting JMeter: $Plan (threads=$Threads rampup=$RampUp duration=${Duration}s)" -ForegroundColor Cyan
Write-Host "Watch live results: http://localhost:3000/d/jmeter-logistics" -ForegroundColor Yellow

docker compose --profile load run --rm jmeter

Write-Host "Done. HTML report and .jtl file are in jmeter/results/" -ForegroundColor Green

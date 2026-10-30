# Automated self-test for React Health Check API
$ErrorActionPreference = "Stop"

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TestScript = Join-Path $PSScriptRoot "test.mjs"

Write-Host "Running React API self-tests..." -ForegroundColor Cyan
node $TestScript


# Automated self-test for Angular Health Check API
$ErrorActionPreference = "Stop"

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TestScript = Join-Path $PSScriptRoot "test.mjs"

Write-Host "Running Angular API self-tests..." -ForegroundColor Cyan
node $TestScript


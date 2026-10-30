# Run Angular SSR / API server on port 4200
$ErrorActionPreference = "Stop"

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerScript = Join-Path $PSScriptRoot "server.mjs"

Write-Host "Starting Angular API Server on http://localhost:4200..." -ForegroundColor Green
node $ServerScript 4200


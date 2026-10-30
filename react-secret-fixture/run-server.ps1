# Run React / Next.js API server on port 3000
$ErrorActionPreference = "Stop"

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerScript = Join-Path $PSScriptRoot "server.mjs"

Write-Host "Starting React API Server on http://localhost:3000..." -ForegroundColor Green
node $ServerScript 3000


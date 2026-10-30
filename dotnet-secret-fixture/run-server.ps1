# Start .NET Health Check HTTP Server on port 5000
$ErrorActionPreference = "Stop"

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectFile = Join-Path $PSScriptRoot "FinanceApi.csproj"

Write-Host "Starting .NET Finance API on http://localhost:5000..." -ForegroundColor Green
dotnet run --project $ProjectFile --urls "http://localhost:5000"


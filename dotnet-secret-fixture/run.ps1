# Self-test runner for .NET Finance API & Auth Demo
$ErrorActionPreference = "Stop"

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectFile = Join-Path $PSScriptRoot "FinanceApi.csproj"

Write-Host "Running .NET self-tests..." -ForegroundColor Cyan
dotnet run --project $ProjectFile -- --test


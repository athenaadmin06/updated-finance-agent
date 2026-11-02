param(
    [int]$Port = 8080,
    [string]$Token = $env:AUTH_TOKEN
)

if (-not $Token) {
    $Token = "sec_health_check_token_9f8d7c6b5a4e3d2c1b0a"
}

$HealthUrl = "http://localhost:$Port/api/health"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Testing Java Health Check API on $HealthUrl" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$allPassed = $true

# Test 1: No auth
Write-Host "`n[Test 1] Request without Authorization header..."
try {
    $resp1 = Invoke-WebRequest -Uri $HealthUrl -Method Get -SkipHttpErrorCheck
    if ($resp1.StatusCode -eq 401) {
        Write-Host "  -> Status: 401 [PASSED (401 Unauthorized)]" -ForegroundColor Green
    } else {
        Write-Host "  -> Status: $($resp1.StatusCode) [FAILED: expected 401]" -ForegroundColor Red
        $allPassed = $false
    }
} catch {
    Write-Host "  -> Error connecting: $($_.Exception.Message)" -ForegroundColor Red
    $allPassed = $false
}

# Test 2: Invalid token
Write-Host "`n[Test 2] Request with invalid token..."
try {
    $resp2 = Invoke-WebRequest -Uri $HealthUrl -Method Get -Headers @{ "Authorization" = "Bearer wrong_token_12345" } -SkipHttpErrorCheck
    if ($resp2.StatusCode -eq 401) {
        Write-Host "  -> Status: 401 [PASSED (401 Unauthorized)]" -ForegroundColor Green
    } else {
        Write-Host "  -> Status: $($resp2.StatusCode) [FAILED: expected 401]" -ForegroundColor Red
        $allPassed = $false
    }
} catch {
    Write-Host "  -> Error connecting: $($_.Exception.Message)" -ForegroundColor Red
    $allPassed = $false
}

# Test 3: Valid token
Write-Host "`n[Test 3] Request with valid token..."
try {
    $resp3 = Invoke-WebRequest -Uri $HealthUrl -Method Get -Headers @{ "Authorization" = "Bearer $Token" } -SkipHttpErrorCheck
    if ($resp3.StatusCode -eq 200) {
        Write-Host "  -> Status: 200 [PASSED (200 OK)]" -ForegroundColor Green
        Write-Host "  -> Body: $($resp3.Content)" -ForegroundColor Yellow
    } else {
        Write-Host "  -> Status: $($resp3.StatusCode) [FAILED: expected 200]" -ForegroundColor Red
        $allPassed = $false
    }
} catch {
    Write-Host "  -> Error connecting: $($_.Exception.Message)" -ForegroundColor Red
    $allPassed = $false
}

Write-Host "`n==================================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host " [SUCCESS] Health Check API is WORKING FINE!" -ForegroundColor Green
    exit 0
} else {
    Write-Host " [FAILURE] Health Check API tests FAILED!" -ForegroundColor Red
    exit 1
}

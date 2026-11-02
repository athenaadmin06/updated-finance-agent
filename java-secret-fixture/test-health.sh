#!/usr/bin/env bash
# Health Check API verification script using curl

PORT=${1:-8080}
TOKEN=${AUTH_TOKEN:-"sec_health_check_token_9f8d7c6b5a4e3d2c1b0a"}
BASE_URL="http://localhost:${PORT}/api/health"

echo "=================================================="
echo " Testing Java Health Check API on ${BASE_URL}"
echo "=================================================="

# Test 1: No auth
echo -e "\n[Test 1] Request without Authorization header..."
STATUS1=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}")
if [ "$STATUS1" = "401" ]; then
    echo "  -> Status: 401 [PASSED (401 Unauthorized)]"
else
    echo "  -> Status: $STATUS1 [FAILED: expected 401]"
    FAILED=1
fi

# Test 2: Invalid token
echo -e "\n[Test 2] Request with invalid token..."
STATUS2=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer wrong_token_12345" "${BASE_URL}")
if [ "$STATUS2" = "401" ]; then
    echo "  -> Status: 401 [PASSED (401 Unauthorized)]"
else
    echo "  -> Status: $STATUS2 [FAILED: expected 401]"
    FAILED=1
fi

# Test 3: Valid token
echo -e "\n[Test 3] Request with valid token..."
BODY=$(curl -s -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}")
STATUS3=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}")
if [ "$STATUS3" = "200" ]; then
    echo "  -> Status: 200 [PASSED (200 OK)]"
    echo "  -> Body: ${BODY}"
else
    echo "  -> Status: $STATUS3 [FAILED: expected 200]"
    FAILED=1
fi

echo -e "\n=================================================="
if [ -z "$FAILED" ]; then
    echo " [SUCCESS] Health Check API is WORKING FINE!"
    exit 0
else
    echo " [FAILURE] Health Check API tests FAILED!"
    exit 1
fi

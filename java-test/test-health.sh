#!/usr/bin/env bash
# Test script for Java Health Check API using curl

set -e

PORT=${1:-${PORT:-8080}}
TOKEN=${AUTH_TOKEN:-"secret-health-token-12345"}
BASE_URL="http://localhost:${PORT}/health"
FAILED=0

echo "=================================================="
echo " Testing Java Health Check API on ${BASE_URL}"
echo " Token: ${TOKEN}"
echo "=================================================="

# Test 1: No auth header
echo -e "\n[Test 1] Request without Authorization header..."
STATUS1=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}" || echo "000")
BODY1=$(curl -s "${BASE_URL}" || echo "")
if [ "$STATUS1" = "401" ]; then
    echo "  -> Status: 401 [PASSED (401 Unauthorized)]"
    echo "  -> Response: ${BODY1}"
else
    echo "  -> Status: ${STATUS1} [FAILED: expected 401]"
    FAILED=1
fi

# Test 2: Invalid auth token
echo -e "\n[Test 2] Request with invalid token..."
STATUS2=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer invalid-token-xyz" "${BASE_URL}" || echo "000")
BODY2=$(curl -s -H "Authorization: Bearer invalid-token-xyz" "${BASE_URL}" || echo "")
if [ "$STATUS2" = "401" ]; then
    echo "  -> Status: 401 [PASSED (401 Unauthorized)]"
    echo "  -> Response: ${BODY2}"
else
    echo "  -> Status: ${STATUS2} [FAILED: expected 401]"
    FAILED=1
fi

# Test 3: Valid Bearer token
echo -e "\n[Test 3] Request with valid Bearer token..."
STATUS3=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}" || echo "000")
BODY3=$(curl -s -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}" || echo "")
if [ "$STATUS3" = "200" ]; then
    echo "  -> Status: 200 [PASSED (200 OK)]"
    echo "  -> Response: ${BODY3}"
else
    echo "  -> Status: ${STATUS3} [FAILED: expected 200]"
    FAILED=1
fi

# Test 4: Valid X-Auth-Token header
echo -e "\n[Test 4] Request with X-Auth-Token header..."
STATUS4=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Auth-Token: ${TOKEN}" "${BASE_URL}" || echo "000")
BODY4=$(curl -s -H "X-Auth-Token: ${TOKEN}" "${BASE_URL}" || echo "")
if [ "$STATUS4" = "200" ]; then
    echo "  -> Status: 200 [PASSED (200 OK)]"
    echo "  -> Response: ${BODY4}"
else
    echo "  -> Status: ${STATUS4} [FAILED: expected 200]"
    FAILED=1
fi

echo -e "\n=================================================="
if [ "$FAILED" -eq 0 ]; then
    echo " [SUCCESS] All Health Check API tests PASSED!"
    exit 0
else
    echo " [FAILURE] Some Health Check API tests FAILED!"
    exit 1
fi


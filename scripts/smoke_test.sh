#!/usr/bin/env bash
# ZeroHarm AI - End-to-End Smoke Test
# Usage: bash scripts/smoke_test.sh [base_url]
# Default base_url: http://localhost:8000

BASE="${1:-http://localhost:8000}"
API="$BASE/api"
PASS=0
FAIL=0

green() { printf "\033[32m%s\033[0m\n" "$1"; }
red()   { printf "\033[31m%s\033[0m\n" "$1"; }

check() {
    local label="$1" method="$2" url="$3" status="$4" extra="$5"
    if [ "$method" = "GET" ]; then
        resp=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    else
        resp=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" -H "Content-Type: application/json" $extra "$url" 2>/dev/null)
    fi
    if [ "$resp" = "$status" ]; then
        green "  PASS [$resp] $label"
        PASS=$((PASS + 1))
    else
        red "  FAIL [got $resp, expected $status] $label"
        FAIL=$((FAIL + 1))
    fi
}

echo "============================================"
echo "  ZeroHarm AI - Smoke Test"
echo "  Target: $BASE"
echo "============================================"

# Health
check "Health endpoint" GET "$API/health" 200

# Auth
TOKEN=$(curl -s "$API/auth/login" -X POST -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
AUTH="-H 'Authorization: Bearer $TOKEN'"

check "Login" GET "$API/health" 200 "$AUTH"
check "Zones" GET "$API/zones" 200
check "Sensors" GET "$API/sensors" 200
check "Risk status" GET "$API/risk-status" 200
check "Risk trend" GET "$API/risk-trend" 200
check "Activity feed" GET "$API/activity-feed" 200
check "Compliance history" GET "$API/compliance/history" 200
check "Incident history" GET "$API/incident/history" 200
check "Health index" GET "$API/health-index" 200
check "Investigation list" GET "$API/investigation/list" 200
check "Scenarios" GET "$API/scenarios" 200
check "Cost of Safety" GET "$API/cost-of-safety" 200
check "Chat assistant" POST "$API/chat" 200 "-d '{\"message\":\"what is the risk\"}'"
check "Shift handover" GET "$API/reports/shift-handover?shift=Day" 200

echo "============================================"
echo "  Results: $PASS passed, $FAIL failed"
echo "============================================"
exit $FAIL

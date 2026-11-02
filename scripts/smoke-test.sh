#!/usr/bin/env bash
# Post-deployment smoke test: health, version, and one job end-to-end.
#   scripts/smoke-test.sh http://staging.jobs.localtest.me
set -euo pipefail
BASE="${1:-http://localhost:8080}"
TIMEOUT="${SMOKE_TIMEOUT:-60}"
pass() { printf '  \033[32m✔\033[0m %s\n' "$*"; }
fail() { printf '  \033[31m✘\033[0m %s\n' "$*"; exit 1; }

echo "Smoke testing $BASE"
curl -fsS --max-time 5 "$BASE/" | grep -q "<title>Jobs Platform</title>" && pass "frontend serves index" || fail "frontend"
curl -fsS --max-time 5 "$BASE/version" | grep -q '"version"' && pass "API reachable through frontend" || fail "version endpoint"

id=$(curl -fsS --max-time 5 -H 'Content-Type: application/json' \
      -d '{"type":"reverse","payload":{"text":"smoke"}}' "$BASE/api/jobs" | sed -E 's/.*"id":"([^"]+)".*/\1/')
[[ -n "$id" ]] && pass "job submitted ($id)" || fail "job submission"

deadline=$((SECONDS + TIMEOUT))
while (( SECONDS < deadline )); do
  body=$(curl -fsS --max-time 5 "$BASE/api/jobs/$id")
  if grep -q '"status":"completed"' <<<"$body"; then
    grep -q '"reversed":"ekoms"' <<<"$body" && pass "worker processed job" || fail "wrong result: $body"
    curl -fsS -X DELETE "$BASE/api/jobs/$id" >/dev/null
    echo "All smoke tests passed"; exit 0
  fi
  grep -q '"status":"failed"' <<<"$body" && fail "job failed: $body"
  sleep 1
done
fail "job not completed within ${TIMEOUT}s"

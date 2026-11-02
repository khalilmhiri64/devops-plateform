#!/usr/bin/env bash
# Seed the docker-compose Vault (profile "security") so the API can load its DB
# password from Vault instead of an env var:
#   docker compose --profile security up -d vault && scripts/vault-dev-init.sh
#   then set DATABASE_URL=postgresql://jobs:__VAULT__@postgres:5432/jobs
#        VAULT_ADDR=http://vault:8200 VAULT_TOKEN=<app token printed below>
set -euo pipefail
cd "$(dirname "$0")/.."
export VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
export VAULT_TOKEN="${VAULT_TOKEN:-root-local-only}"
v() { docker compose exec -T -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN="$VAULT_TOKEN" vault vault "$@"; }

v kv put secret/jobs-platform/database \
  username=jobs password="${POSTGRES_PASSWORD:-jobs-local-only}" \
  database_url="postgresql://jobs:${POSTGRES_PASSWORD:-jobs-local-only}@postgres:5432/jobs"
v policy write jobs-app - < security/vault/policies/jobs-app.hcl
echo "App token (read-only, 24h):"
v token create -policy=jobs-app -ttl=24h -field=token

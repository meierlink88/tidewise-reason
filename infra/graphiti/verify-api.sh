#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
env_file="${GRAPHITI_ENV_FILE:-$repo_root/.runtime/graphiti.env}"
compose_file="$repo_root/infra/graphiti/compose.yaml"

# shellcheck source=runtime-env.sh
source "$repo_root/infra/graphiti/runtime-env.sh"
require_private_graphiti_env "$env_file"

set -a
# shellcheck disable=SC1090
source "$env_file"
set +a
require_reason_api_token

compose=(docker compose --env-file "$env_file" -f "$compose_file")
container_id="$(${compose[@]} ps -q api)"
[ -n "$container_id" ] || { echo 'Reason ingestion API is not running' >&2; exit 1; }
[ "$(docker inspect --format '{{.State.Health.Status}}' "$container_id")" = healthy ]

curl --fail --silent --show-error "http://127.0.0.1:8890/healthz" | grep -q '"status":"ok"'
curl --fail --silent --show-error "http://127.0.0.1:8890/readyz" | grep -q '"status":"ready"'
curl --silent --show-error \
  -H "Authorization: Bearer ${REASON_API_SERVICE_TOKEN}" \
  "http://127.0.0.1:8890/api/reason/v1/evidence-episodes/EVD00000000-0000-4000-8000-000000000000" \
  --output /dev/null --write-out '%{http_code}' | grep -q '^404$'

echo 'PASS Reason ingestion API is healthy and requires authenticated Evidence access'

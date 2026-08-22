#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
env_file="${GRAPHITI_ENV_FILE:-$repo_root/.runtime/graphiti.env}"
compose_file="$repo_root/infra/graphiti/compose.yaml"
expected_image='neo4j:5.26.28-community@sha256:ff32db30b2baff97971e441b46bfd9c832c1b62c970398ef579244c06b21d357'

# shellcheck source=runtime-env.sh
source "$repo_root/infra/graphiti/runtime-env.sh"
require_private_graphiti_env "$env_file"

set -a
# shellcheck disable=SC1090
source "$env_file"
set +a

compose=(docker compose --env-file "$env_file" -f "$compose_file")
container_id="$(${compose[@]} ps -q neo4j)"
[ -n "$container_id" ] || { echo 'Graphiti Neo4j is not running' >&2; exit 1; }

[ "$(docker inspect --format '{{.Config.Image}}' "$container_id")" = "$expected_image" ]
[ "$(docker inspect --format '{{.State.Health.Status}}' "$container_id")" = healthy ]
[ "$(docker exec "$container_id" neo4j --version)" = 5.26.28 ]

mounts="$(docker inspect --format '{{range .Mounts}}{{println .Name .Destination}}{{end}}' "$container_id")"
grep -q '^tidewise-reason_graphiti-neo4j-data /data$' <<<"$mounts"
grep -q '^tidewise-reason_graphiti-neo4j-logs /logs$' <<<"$mounts"

NEO4J_USERNAME="$NEO4J_USER" NEO4J_PASSWORD="$NEO4J_PASSWORD" \
  ${compose[@]} exec -T -e NEO4J_USERNAME -e NEO4J_PASSWORD neo4j \
  bash -c 'cypher-shell -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" "RETURN 1 AS ready"' \
  | grep -q '^1$'

echo 'PASS Graphiti Neo4j 5.26.28 is healthy and uses dedicated volumes'

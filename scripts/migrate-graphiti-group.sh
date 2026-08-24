#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${GRAPHITI_ENV_FILE:-$repo_root/.runtime/graphiti.env}"
compose_file="$repo_root/infra/graphiti/compose.yaml"
mode="${1:-plan}"

# shellcheck source=../infra/graphiti/runtime-env.sh
source "$repo_root/infra/graphiti/runtime-env.sh"
require_private_graphiti_env "$env_file"

case "$mode" in
  plan|run) ;;
  *) echo 'usage: scripts/migrate-graphiti-group.sh [plan|run]' >&2; exit 2 ;;
esac

set -a
# shellcheck disable=SC1090
source "$env_file"
set +a

compose=(docker compose --env-file "$env_file" -f "$compose_file")
container_id="$(${compose[@]} ps -q neo4j)"
[ -n "$container_id" ] || { echo 'Graphiti Neo4j is not running' >&2; exit 1; }

cypher() {
  NEO4J_USERNAME="$NEO4J_USER" NEO4J_PASSWORD="$NEO4J_PASSWORD" \
    ${compose[@]} exec -T -e NEO4J_USERNAME -e NEO4J_PASSWORD neo4j \
    bash -c 'cypher-shell -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" "$1"' -- "$1"
}

cypher "MATCH (n) WHERE n.group_id IN ['tidewise-investment-research', 'neo4j'] RETURN n.group_id AS group_id, count(n) AS nodes ORDER BY group_id"
cypher "MATCH ()-[r]->() WHERE r.group_id IN ['tidewise-investment-research', 'neo4j'] RETURN r.group_id AS group_id, count(r) AS relationships ORDER BY group_id"

if [ "$mode" = plan ]; then
  echo 'PLAN only; no graph data changed'
  exit 0
fi

cypher "MATCH (n {group_id: 'tidewise-investment-research'}) SET n.group_id = 'neo4j' RETURN count(n) AS migrated_nodes"
cypher "MATCH ()-[r]->() WHERE r.group_id = 'tidewise-investment-research' SET r.group_id = 'neo4j' RETURN count(r) AS migrated_relationships"

remaining_nodes="$(cypher "MATCH (n {group_id: 'tidewise-investment-research'}) RETURN count(n) AS remaining" | tail -n 1)"
remaining_relationships="$(cypher "MATCH ()-[r]->() WHERE r.group_id = 'tidewise-investment-research' RETURN count(r) AS remaining" | tail -n 1)"
[ "$remaining_nodes" = '0' ]
[ "$remaining_relationships" = '0' ]

cypher "MATCH (n {group_id: 'neo4j'}) RETURN count(n) AS nodes"
cypher "MATCH ()-[r]->() WHERE r.group_id = 'neo4j' RETURN count(r) AS relationships"
echo 'PASS Graphiti group_id migrated in place without deleting graph data'

#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${GRAPHITI_ENV_FILE:-$repo_root/.runtime/graphiti.env}"
compose_file="$repo_root/infra/graphiti/compose.yaml"

# shellcheck source=../infra/graphiti/runtime-env.sh
source "$repo_root/infra/graphiti/runtime-env.sh"
require_private_graphiti_env "$env_file"

set -a
# shellcheck disable=SC1090
source "$env_file"
set +a
require_reason_api_token

api_port="${REASON_API_PORT:-8890}"
data_url="${TIDEWISE_DATA_BASE_URL%/}/api/data/v1/evidences?page=1&page_size=1"
evidence_response="$(
  curl --fail --silent --show-error \
    -H "Authorization: Bearer ${TIDEWISE_DATA_SERVICE_TOKEN}" \
    "$data_url"
)"
evidence_id="$(
  python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["items"][0]["id"])' \
    <<<"$evidence_response"
)"
request_body="$(
  python3 -c 'import json,sys; data=json.load(sys.stdin); print(json.dumps({"evidences": [data["result"]["items"][0]]}, ensure_ascii=False, separators=(",", ":")))' \
    <<<"$evidence_response"
)"

curl --fail --silent --show-error \
  -H "Authorization: Bearer ${REASON_API_SERVICE_TOKEN}" \
  -H 'Content-Type: application/json' \
  --data-binary "$request_body" \
  "http://127.0.0.1:${api_port}/api/reason/v1/evidence-episodes" \
  --output /dev/null

episode_uuid=''
for _ in {1..150}; do
  status_response="$(
    curl --fail --silent --show-error \
      -H "Authorization: Bearer ${REASON_API_SERVICE_TOKEN}" \
      "http://127.0.0.1:${api_port}/api/reason/v1/evidence-episodes/${evidence_id}"
  )"
  processing_status="$(
    python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])' \
      <<<"$status_response"
  )"
  if [ "$processing_status" = 'SUCCEEDED' ]; then
    episode_uuid="$(
      python3 -c 'import json,sys; print(json.load(sys.stdin)["graphiti_episode_uuid"])' \
        <<<"$status_response"
    )"
    break
  fi
  if [ "$processing_status" = 'FAILED' ]; then
    echo "Evidence Episode processing failed for $evidence_id" >&2
    exit 1
  fi
  sleep 2
done
[ -n "$episode_uuid" ] || { echo "Evidence Episode processing timed out for $evidence_id" >&2; exit 1; }

compose=(docker compose --env-file "$env_file" -f "$compose_file")
verification="$(
  NEO4J_USERNAME="$NEO4J_USER" NEO4J_PASSWORD="$NEO4J_PASSWORD" \
    EVIDENCE_ID="$evidence_id" EPISODE_UUID="$episode_uuid" \
    ${compose[@]} exec -T \
      -e NEO4J_USERNAME -e NEO4J_PASSWORD -e EVIDENCE_ID -e EPISODE_UUID neo4j \
      bash -c 'cypher-shell -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" "MATCH (episode:Episodic {name: '\''$EVIDENCE_ID'\'', uuid: '\''$EPISODE_UUID'\'', group_id: '\''neo4j'\''}) RETURN count(episode) AS episodes, coalesce(episode.tidewise_ingestion_complete, false) AS complete"' \
      | tail -n 1
)"
[ "$verification" = '1, TRUE' ] || [ "$verification" = '1, true' ]

echo "PASS published Evidence $evidence_id traversed Reason API, Graphiti and Neo4j"

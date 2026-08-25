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

anchor_name='人工智能'
data_url="${TIDEWISE_DATA_BASE_URL%/}/api/data/v1/evidences?page=1&page_size=100"
evidence_response="$(
  curl --fail --silent --show-error \
    -H "Authorization: Bearer ${TIDEWISE_DATA_SERVICE_TOKEN}" \
    "$data_url"
)"
evidence_id="$(
  ANCHOR_NAME="$anchor_name" python3 -c 'import json,os,sys; items=json.load(sys.stdin)["result"]["items"]; item=next(value for value in items if os.environ["ANCHOR_NAME"] in json.dumps(value, ensure_ascii=False)); print(item["id"])' \
    <<<"$evidence_response"
)"
request_body="$(
  ANCHOR_NAME="$anchor_name" python3 -c 'import json,os,sys; items=json.load(sys.stdin)["result"]["items"]; item=next(value for value in items if os.environ["ANCHOR_NAME"] in json.dumps(value, ensure_ascii=False)); print(json.dumps({"evidences": [item]}, ensure_ascii=False, separators=(",", ":")))' \
    <<<"$evidence_response"
)"

curl --fail --silent --show-error \
  -H "Authorization: Bearer ${REASON_API_SERVICE_TOKEN}" \
  -H 'Content-Type: application/json' \
  --data-binary "$request_body" \
  "http://127.0.0.1:8890/api/reason/v1/evidence-episodes" \
  --output /dev/null

episode_uuid=''
for _ in {1..150}; do
  status_response="$(
    curl --fail --silent --show-error \
      -H "Authorization: Bearer ${REASON_API_SERVICE_TOKEN}" \
      "http://127.0.0.1:8890/api/reason/v1/evidence-episodes/${evidence_id}"
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
    "${compose[@]}" exec -T \
      -e NEO4J_USERNAME -e NEO4J_PASSWORD -e EVIDENCE_ID -e EPISODE_UUID neo4j \
      bash -c 'cypher-shell -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" "MATCH (episode:Episodic {name: '\''$EVIDENCE_ID'\'', uuid: '\''$EPISODE_UUID'\'', group_id: '\''neo4j'\''}) OPTIONAL MATCH (episode)-[:MENTIONS]->(target) WITH episode, count(DISTINCT target) AS total, count(DISTINCT CASE WHEN target.data_object_id IS NOT NULL THEN target END) AS canonical OPTIONAL MATCH (episode)-[:MENTIONS]->(anchor:Concept {name: '\''人工智能'\''}) WHERE anchor.data_object_id IS NOT NULL RETURN coalesce(episode.tidewise_ingestion_complete, false) AS complete, episode.episode_kind = '\''EVIDENCE'\'' AS evidence_kind, total = canonical AS all_authoritative, count(DISTINCT anchor) = 1 AS canonical_anchor"' \
      | tail -n 1
)"
[ "$verification" = 'TRUE, TRUE, TRUE, TRUE' ] \
  || [ "$verification" = 'true, true, true, true' ]

echo "PASS published Evidence $evidence_id resolved canonical $anchor_name through Reason, Graphiti and Neo4j"

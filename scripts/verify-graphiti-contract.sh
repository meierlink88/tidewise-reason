#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compose_file="$repo_root/infra/graphiti/compose.yaml"
env_file="$repo_root/infra/graphiti/.env.example"

config_json="$(docker compose --env-file "$env_file" -f "$compose_file" config --format json)"
CONFIG_JSON="$config_json" python3 - <<'PY'
import json
import os

config = json.loads(os.environ["CONFIG_JSON"])
assert config["name"] == "tidewise-reasoning"
assert set(config["services"]) == {"api", "neo4j"}
service = config["services"]["neo4j"]
assert service["container_name"] == "reason-graphiti-neo4j"
assert service["image"] == "neo4j:5.26.28-community@sha256:ff32db30b2baff97971e441b46bfd9c832c1b62c970398ef579244c06b21d357"
assert {item["target"] for item in service["ports"]} == {7474, 7687}
assert {item["host_ip"] for item in service["ports"]} == {"127.0.0.1"}
assert config["volumes"]["graphiti-neo4j-data"]["name"] == "tidewise-reason_graphiti-neo4j-data"
assert config["volumes"]["graphiti-neo4j-logs"]["name"] == "tidewise-reason_graphiti-neo4j-logs"
api = config["services"]["api"]
assert api["container_name"] == "reason-graphiti-api"
assert api["ports"][0]["host_ip"] == "127.0.0.1"
assert api["ports"][0]["target"] == 8890
assert api["ports"][0]["published"] == "8890"
assert config["volumes"]["graphiti-api-state"]["name"] == "tidewise-reason_graphiti-api-state"
PY

grep -qx 'fastapi==0.116.1' "$repo_root/ontology/requirements.in"
grep -qx 'graphiti-core==0.29.3' "$repo_root/ontology/requirements.in"
grep -qx 'httpx==0.28.1' "$repo_root/ontology/requirements.in"
grep -qx 'neo4j==6.2.0' "$repo_root/ontology/requirements.in"
grep -q '^graphiti-core==0[.]29[.]3' "$repo_root/ontology/requirements.lock"
grep -q -- '--hash=sha256:' "$repo_root/ontology/requirements.lock"
grep -q -- '--python 3.12.11' "$repo_root/scripts/install-graphiti-runtime.sh"
grep -q -- '--require-hashes' "$repo_root/scripts/install-graphiti-runtime.sh"
grep -q 'TIDEWISE_DATA_BASE_URL' "$repo_root/infra/graphiti/.env.example"
grep -q 'REASON_API_SERVICE_TOKEN' "$repo_root/infra/graphiti/.env.example"
! grep -q 'REASON_API_PORT' "$repo_root/infra/graphiti/.env.example"
grep -q 'require_private_graphiti_env' "$repo_root/infra/graphiti/start.sh"
grep -q 'require_private_graphiti_env' "$repo_root/infra/graphiti/stop.sh"
grep -q 'require_private_graphiti_env' "$repo_root/infra/graphiti/verify.sh"
grep -q 'require_private_graphiti_env' "$repo_root/infra/graphiti/start-api.sh"
grep -q 'require_private_graphiti_env' "$repo_root/infra/graphiti/stop-api.sh"
grep -q 'require_private_graphiti_env' "$repo_root/infra/graphiti/verify-api.sh"
grep -q 'require_private_graphiti_env' "$repo_root/scripts/verify-evidence-episode.sh"
grep -Fq 'snapshot_file="$(mktemp)"' "$repo_root/scripts/initialize-chainnode-graph.sh"
grep -Fq '> "$snapshot_file"' "$repo_root/scripts/initialize-chainnode-graph.sh"
grep -Fq '< "$snapshot_file"' "$repo_root/scripts/initialize-chainnode-graph.sh"
git -C "$repo_root" check-ignore -q .runtime/graphiti.env

permission_test_file="$(mktemp)"
pycache_root="$(mktemp -d)"
trap 'rm -f "$permission_test_file"; rm -rf "$pycache_root"' EXIT
chmod 0644 "$permission_test_file"
if bash -c 'source "$1"; require_private_graphiti_env "$2"' _ \
  "$repo_root/infra/graphiti/runtime-env.sh" "$permission_test_file" 2>/dev/null; then
  echo 'Graphiti lifecycle accepted an insecure runtime environment' >&2
  exit 1
fi
chmod 0600 "$permission_test_file"
bash -c 'source "$1"; require_private_graphiti_env "$2"' _ \
  "$repo_root/infra/graphiti/runtime-env.sh" "$permission_test_file"

if rg -n 'docker exec|openspg\.kg_user_model|FROM evidences|JOIN raw_evidences' \
  "$repo_root/ontology"; then
  echo 'Graphiti ontology bypasses an owning service contract' >&2
  exit 1
fi

if rg -n 'graphiti_core[.]utils[.]bulk_utils|add_nodes_and_edges_bulk' \
  "$repo_root/projection"; then
  echo 'Canonical projection bypasses the public Graphiti Namespace API' >&2
  exit 1
fi

if rg -n '[.]add_episode[(]' "$repo_root/ingestion/episcode/evidence"; then
  echo 'Evidence ingestion delegates to Graphiti add_episode and can create non-authoritative Entities' >&2
  exit 1
fi

if rg -n 'docker compose .*down|--remove-orphans|docker volume rm' \
  "$repo_root/infra/graphiti" "$repo_root/scripts/install-graphiti-runtime.sh"; then
  echo 'Graphiti lifecycle includes a destructive or unscoped command' >&2
  exit 1
fi

PYTHONPYCACHEPREFIX="$pycache_root" python3 -m py_compile \
  "$repo_root"/ontology/*.py \
  "$repo_root"/ontology/entities/*.py \
  "$repo_root"/projection/*.py \
  "$repo_root"/initialization/*.py \
  "$repo_root"/initialization/chainnode/*.py \
  "$repo_root"/ingestion/*.py \
  "$repo_root"/ingestion/episcode/*.py \
  "$repo_root"/ingestion/episcode/evidence/*.py \
  "$repo_root"/ingestion/episcode/evidence/graphiti/*.py \
  "$repo_root"/tests/test_ontology_contract.py
bash "$repo_root/scripts/test-ontology.sh"
bash "$repo_root/scripts/test-projection.sh"
echo 'PASS Graphiti static contract'

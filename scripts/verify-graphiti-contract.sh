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
assert set(config["services"]) == {"neo4j"}
service = config["services"]["neo4j"]
assert service["container_name"] == "reason-graphiti-neo4j"
assert service["image"] == "neo4j:5.26.28-community@sha256:ff32db30b2baff97971e441b46bfd9c832c1b62c970398ef579244c06b21d357"
assert {item["target"] for item in service["ports"]} == {7474, 7687}
assert {item["host_ip"] for item in service["ports"]} == {"127.0.0.1"}
assert config["volumes"]["graphiti-neo4j-data"]["name"] == "tidewise-reason_graphiti-neo4j-data"
assert config["volumes"]["graphiti-neo4j-logs"]["name"] == "tidewise-reason_graphiti-neo4j-logs"
PY

grep -qx 'graphiti-core==0.29.3' "$repo_root/graphiti_demo/requirements.in"
grep -qx 'httpx==0.28.1' "$repo_root/graphiti_demo/requirements.in"
grep -qx 'neo4j==6.2.0' "$repo_root/graphiti_demo/requirements.in"
grep -q '^graphiti-core==0[.]29[.]3' "$repo_root/graphiti_demo/requirements.lock"
grep -q -- '--hash=sha256:' "$repo_root/graphiti_demo/requirements.lock"
grep -q -- '--python 3.12.11' "$repo_root/scripts/install-graphiti-runtime.sh"
grep -q -- '--require-hashes' "$repo_root/scripts/install-graphiti-runtime.sh"
grep -q 'TIDEWISE_DATA_BASE_URL' "$repo_root/infra/graphiti/.env.example"
grep -q 'api/data/v1/evidences' "$repo_root/graphiti_demo/runtime.py"
grep -q 'ontology_schema' "$repo_root/graphiti_demo/pipeline.py"
grep -q 'EVIDENCE_EPISODE_UUIDS' "$repo_root/graphiti_demo/pipeline.py"
grep -q 'runtime environment must have mode 0600' "$repo_root/graphiti_demo/runtime.py"
grep -q 'require_private_graphiti_env' "$repo_root/infra/graphiti/start.sh"
grep -q 'require_private_graphiti_env' "$repo_root/infra/graphiti/stop.sh"
grep -q 'require_private_graphiti_env' "$repo_root/infra/graphiti/verify.sh"
git -C "$repo_root" check-ignore -q .runtime/graphiti.env

permission_test_file="$(mktemp)"
trap 'rm -f "$permission_test_file"' EXIT
chmod 0644 "$permission_test_file"
if bash -c 'source "$1"; require_private_graphiti_env "$2"' _ \
  "$repo_root/infra/graphiti/runtime-env.sh" "$permission_test_file" 2>/dev/null; then
  echo 'Graphiti lifecycle accepted an insecure runtime environment' >&2
  exit 1
fi
chmod 0600 "$permission_test_file"
bash -c 'source "$1"; require_private_graphiti_env "$2"' _ \
  "$repo_root/infra/graphiti/runtime-env.sh" "$permission_test_file"

if rg -n 'graphiti_core|execute_query|MATCH \(' \
  "$repo_root/graphiti_demo/cli.py" "$repo_root/graphiti_demo/pipeline.py"; then
  echo 'Graphiti concrete provider behavior escaped the adapter' >&2
  exit 1
fi

if rg -n 'docker exec|openspg\.kg_user_model|FROM evidences|JOIN raw_evidences' \
  "$repo_root/graphiti_demo"; then
  echo 'Graphiti demo bypasses an owning service contract' >&2
  exit 1
fi

if rg -n 'docker compose .*down|--remove-orphans|docker volume rm' \
  "$repo_root/infra/graphiti" "$repo_root/scripts/graphiti-demo.sh" \
  "$repo_root/scripts/install-graphiti-runtime.sh"; then
  echo 'Graphiti lifecycle includes a destructive or unscoped command' >&2
  exit 1
fi

python3 -m py_compile "$repo_root"/graphiti_demo/*.py
echo 'PASS Graphiti static contract'

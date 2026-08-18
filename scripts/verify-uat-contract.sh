#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compose_file="$repo_root/infra/uat/compose.yaml"
env_file="$repo_root/infra/uat/.env.example"
workflow_file="$repo_root/.github/workflows/deploy-uat.yml"

docker compose --env-file "$env_file" -f "$compose_file" config --quiet
[ "$(docker compose --env-file "$env_file" -f "$compose_file" config --services)" = server ]
[ "$(docker compose --env-file "$env_file" -f "$compose_file" config --images)" = \
  spg-registry.cn-hangzhou.cr.aliyuncs.com/spg/openspg-server:latest ]

COMPOSE_FILE="$compose_file" ENV_FILE="$env_file" python3 - <<'PY'
import json
import os
import subprocess

result = subprocess.run(
    [
        "docker",
        "compose",
        "--env-file",
        os.environ["ENV_FILE"],
        "-f",
        os.environ["COMPOSE_FILE"],
        "config",
        "--format",
        "json",
    ],
    check=True,
    capture_output=True,
    text=True,
)
config = json.loads(result.stdout)
assert config["name"] == "tidewise-reason-uat"
assert set(config["services"]) == {"server"}
service = config["services"]["server"]
assert service["container_name"] == "reason-server-uat"
assert service["ports"] == [
    {
        "mode": "ingress",
        "target": 8887,
        "published": "8887",
        "protocol": "tcp",
        "host_ip": "127.0.0.1",
    }
]
assert set(service["networks"]) == {"tidewise-uat"}
assert config["networks"]["tidewise-uat"]["external"] is True
assert config["networks"]["tidewise-uat"]["name"] == "tidewise-uat"
extra_hosts = service["extra_hosts"]
if isinstance(extra_hosts, dict):
    assert extra_hosts["release-openspg-neo4j"] == "host-gateway"
else:
    assert "release-openspg-neo4j=host-gateway" in extra_hosts
command = "\n".join(service["command"])
assert "--cloudext.objectstorage.url=minio://minio:9000?" in command
assert "--jasypt.encryptor.password=" in command
assert not any("--remove-orphans" in item for item in service.get("command", []))
PY

if grep -REn --include='*.sh' --include='*.yml' --include='*.yaml' \
  'docker compose.* down|--remove-orphans' \
  "$repo_root/infra/uat" "$repo_root/.github"; then
  echo "UAT deployment must not use unscoped down or --remove-orphans" >&2
  exit 1
fi

if grep -REn --include='*.sh' --include='*.yml' --include='*.yaml' \
  'neo4j (start|stop|restart)|systemctl (start|stop|restart) neo4j|openspg-neo4j.*(pull|up|stop|rm)' \
  "$repo_root/infra/uat" "$repo_root/.github"; then
  echo "Reason deployment must not own Neo4j lifecycle" >&2
  exit 1
fi

grep -q 'runs-on: \[self-hosted, linux, x64, tidewise-uat-ecs\]' \
  "$workflow_file"
grep -q 'REASON_CONTENT_SOURCE=' "$workflow_file"
grep -q 'git archive --format=tar.gz' "$workflow_file"
grep -q 'uses: actions/download-artifact@' "$workflow_file"
grep -q 'sha256sum --check reason-release.tar.gz.sha256' "$workflow_file"
[ "$(grep -c 'uses: actions/checkout@' "$workflow_file")" -eq 1 ]
grep -q 'knext project list' "$repo_root/infra/uat/verify.sh"

echo "PASS UAT repository contract"

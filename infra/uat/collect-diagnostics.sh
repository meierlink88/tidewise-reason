#!/usr/bin/env bash

set -euo pipefail

runtime_env="${RUNTIME_ENV:?RUNTIME_ENV is required}"
compose_file="${COMPOSE_FILE:?COMPOSE_FILE is required}"

echo "### host"
uname -srmo
df -h / /opt 2>/dev/null || true
free -h

echo "### reason container"
docker ps -a --filter label=com.docker.compose.project=tidewise-reason-uat \
  --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker inspect reason-server-uat \
  --format 'image_id={{.Image}} status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' \
  2>/dev/null || true

echo "### reason logs"
docker compose --env-file "$runtime_env" -f "$compose_file" logs --no-color --tail=300 server 2>&1 \
  | sed -E 's/((password|secretKey|accessKey)=)[^&[:space:]]+/\1<redacted>/g'

echo "### reason release"
if [ -L "${DEPLOY_ROOT:-/opt/tidewise/reason-uat}/state/current" ]; then
  current="$(readlink -f "${DEPLOY_ROOT:-/opt/tidewise/reason-uat}/state/current")"
  printf 'current=%s\n' "$current"
  sed -n '1p' "$current/commit.sha" 2>/dev/null || true
  sed -n '1,20p' "$current/schemas.sha256" 2>/dev/null || true
fi

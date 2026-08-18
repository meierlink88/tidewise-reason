#!/usr/bin/env bash

set -euo pipefail

runtime_env="${RUNTIME_ENV:?RUNTIME_ENV is required}"
compose_file="${COMPOSE_FILE:?COMPOSE_FILE is required}"

set -a
# shellcheck disable=SC1090
. "$runtime_env"
set +a

compose=(docker compose --env-file "$runtime_env" -f "$compose_file")
web_port="${OPENSPG_WEB_PORT:-8887}"

configured_image="$("${compose[@]}" config --images)"
[ "$configured_image" = "$OPENSPG_SERVER_IMAGE" ]
expected_image_id="$(docker image inspect "$OPENSPG_SERVER_IMAGE" --format '{{.Id}}')"
running_image_id="$(docker inspect reason-server-uat --format '{{.Image}}')"
[ "$running_image_id" = "$expected_image_id" ]
[ "$(docker inspect reason-server-uat --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}')" = healthy ]

curl --fail --silent --show-error "http://127.0.0.1:${web_port}/actuator/health" >/dev/null
curl --fail --silent --show-error "http://127.0.0.1:${web_port}/" | grep -qi '<html'
"${compose[@]}" exec -T server \
  python -c "import importlib.metadata; print(importlib.metadata.version('openspg-kag'))" >/dev/null
"${compose[@]}" exec -T -e KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 \
  server kag --help >/dev/null
"${compose[@]}" exec -T -e KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 \
  server knext --help >/dev/null
timeout 60 "${compose[@]}" exec -T -e KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 \
  server knext project list --host_addr http://127.0.0.1:8887 >/dev/null

kag_version="$("${compose[@]}" exec -T server \
  python -c "import importlib.metadata; print(importlib.metadata.version('openspg-kag'))")"
printf 'PASS Reason UAT Web+KAG+KNEXT image=%s id=%s KAG=%s\n' \
  "$OPENSPG_SERVER_IMAGE" "$running_image_id" "$kag_version"

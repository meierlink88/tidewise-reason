#!/usr/bin/env bash

set -euo pipefail

[ "$(id -u)" -eq 0 ] || {
  echo "bootstrap must run as root" >&2
  exit 1
}

deploy_user="${TIDEWISE_DEPLOY_USER:-tidewise-deploy}"
deploy_root="${TIDEWISE_REASON_DEPLOY_ROOT:-/opt/tidewise/reason-uat}"

id "$deploy_user" >/dev/null 2>&1 || {
  echo "deploy user $deploy_user does not exist" >&2
  exit 1
}
getent group docker | grep -Eq "(^|,)$deploy_user(,|$)" || {
  echo "deploy user $deploy_user is not in the docker group" >&2
  exit 1
}
docker info >/dev/null
docker compose version >/dev/null
docker network inspect tidewise-uat >/dev/null

install -d -m 0750 -o "$deploy_user" -g "$deploy_user" \
  "$deploy_root" \
  "$deploy_root/state"

echo "Reason UAT deployment root ready at $deploy_root"

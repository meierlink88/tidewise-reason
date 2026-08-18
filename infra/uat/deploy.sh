#!/usr/bin/env bash

set -Eeuo pipefail

deployment_root="${DEPLOY_ROOT:?DEPLOY_ROOT is required}"
runtime_env="${RUNTIME_ENV:?RUNTIME_ENV is required}"
compose_file="${COMPOSE_FILE:?COMPOSE_FILE is required}"
content_source="${REASON_CONTENT_SOURCE:?REASON_CONTENT_SOURCE is required}"
release_sha="${RELEASE_SHA:?RELEASE_SHA is required}"
release_id="${RELEASE_ID:?RELEASE_ID is required}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
state_dir="$deployment_root/state"
releases_dir="$deployment_root/releases"
current_link="$state_dir/current"
previous_link="$state_dir/previous"
candidate_dir=""
rollback_in_progress=false

[[ "$release_sha" =~ ^[0-9a-f]{40}$ ]]
[[ "$release_id" =~ ^[0-9a-f]{40}-[0-9]+-[0-9]+$ ]]

compose_for() {
  local env_file="$1"
  local file="$2"
  shift 2
  docker compose --env-file "$env_file" -f "$file" "$@"
}

verify_for() {
  RUNTIME_ENV="$1" COMPOSE_FILE="$2" "$script_dir/verify.sh"
}

has_current_release() {
  [ -L "$current_link" ] &&
    [ -s "$current_link/runtime.env" ] &&
    [ -s "$current_link/compose.yaml" ] &&
    [ -s "$current_link/commit.sha" ]
}

cleanup_candidate() {
  [ -n "$candidate_dir" ] || return 0
  case "$candidate_dir" in
    "$releases_dir/.candidate.$release_id."*) find "$candidate_dir" -depth -delete ;;
    *) echo "FAIL cleanup: unexpected candidate path $candidate_dir" >&2; return 1 ;;
  esac
}
trap cleanup_candidate EXIT

rollback() {
  rollback_in_progress=true
  if has_current_release; then
    compose_for "$current_link/runtime.env" "$current_link/compose.yaml" \
      up -d --no-build --wait --wait-timeout 240 server || return 1
    verify_for "$current_link/runtime.env" "$current_link/compose.yaml" || return 1
    echo "PASS rollback-previous-reason-release" >&2
  else
    compose_for "$runtime_env" "$compose_file" stop --timeout 30 server || return 1
    compose_for "$runtime_env" "$compose_file" rm -f server || return 1
    echo "PASS rollback-first-reason-candidate-removed" >&2
  fi
}

on_error() {
  local code="$1"
  local rollback_code
  trap - ERR
  if [ "$rollback_in_progress" = false ]; then
    set +e
    rollback
    rollback_code="$?"
    set -e
    [ "$rollback_code" -eq 0 ] \
      || echo "FAIL rollback: manual Reason recovery required" >&2
  fi
  exit "$code"
}
trap 'on_error $?' ERR

exec 8>/opt/tidewise/uat/deploy.lock
flock -n 8 || {
  echo "FAIL shared-uat-lock: another UAT deployment is running" >&2
  exit 1
}
exec 9>"$deployment_root/deploy.lock"
flock -n 9 || {
  echo "FAIL reason-deployment-lock: another Reason deployment is running" >&2
  exit 1
}

install -d -m 0750 "$releases_dir"
candidate_dir="$(mktemp -d "$releases_dir/.candidate.$release_id.XXXXXX")"
install -d -m 0750 "$candidate_dir/schemas"
install -m 0600 "$runtime_env" "$candidate_dir/runtime.env"
install -m 0640 "$compose_file" "$candidate_dir/compose.yaml"
printf '%s\n' "$release_sha" >"$candidate_dir/commit.sha"
chmod 0640 "$candidate_dir/commit.sha"
cp -a "$content_source/." "$candidate_dir/schemas/"

CONTENT_DIR="$candidate_dir/schemas" MANIFEST="$candidate_dir/schemas.sha256" python3 - <<'PY'
import hashlib
import os
from pathlib import Path

content_dir = Path(os.environ["CONTENT_DIR"])
manifest = Path(os.environ["MANIFEST"])
lines = []
for path in sorted(item for item in content_dir.rglob("*") if item.is_file()):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f"{digest}  {path.relative_to(content_dir).as_posix()}")
manifest.write_text("\n".join(lines) + "\n")
manifest.chmod(0o640)
PY

release_dir="$releases_dir/$release_id"
[ ! -e "$release_dir" ]
sync "$candidate_dir/runtime.env" "$candidate_dir/compose.yaml" \
  "$candidate_dir/commit.sha" "$candidate_dir/schemas.sha256"
mv "$candidate_dir" "$release_dir"
candidate_dir=""

compose_for "$runtime_env" "$compose_file" config --quiet
compose_for "$runtime_env" "$compose_file" pull server
compose_for "$runtime_env" "$compose_file" up -d --no-build --wait --wait-timeout 240 server
verify_for "$runtime_env" "$compose_file"

if has_current_release; then
  current_target="$(readlink -f "$current_link")"
  ln -sfn "$current_target" "$state_dir/previous.next"
  mv -Tf "$state_dir/previous.next" "$previous_link"
fi
ln -sfn "$release_dir" "$state_dir/current.next"
mv -Tf "$state_dir/current.next" "$current_link"
trap - ERR

echo "PASS deployed-reason-uat $release_sha content=$current_link/schemas"

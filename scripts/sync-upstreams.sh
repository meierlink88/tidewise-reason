#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$repo_root/upstreams.lock"
upstream_root="$repo_root/.runtime/upstream"

sync_checkout() {
  local name="$1"
  local repository="$2"
  local version="$3"
  local commit="$4"
  local checkout="$upstream_root/$name"

  if [[ ! -d "$checkout/.git" ]]; then
    git clone --filter=blob:none "$repository" "$checkout"
  fi

  if [[ -n "$(git -C "$checkout" status --porcelain)" ]]; then
    printf 'Refusing to replace modified upstream checkout: %s\n' "$checkout" >&2
    return 1
  fi

  git -C "$checkout" fetch --force --tags origin "$version"
  if [[ "$(git -C "$checkout" rev-list -n 1 "$version")" != "$commit" ]]; then
    printf '%s no longer resolves to locked commit %s\n' "$version" "$commit" >&2
    return 1
  fi

  git -C "$checkout" checkout --detach "$commit"
  test "$(git -C "$checkout" rev-parse HEAD)" = "$commit"
  printf '%s %s -> %s\n' "$name" "$version" "$commit"
}

mkdir -p "$upstream_root"
sync_checkout openspg "$OPENSPG_REPOSITORY" "$OPENSPG_VERSION" "$OPENSPG_COMMIT"
sync_checkout kag "$KAG_REPOSITORY" "$KAG_VERSION" "$KAG_COMMIT"

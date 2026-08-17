#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
kag_source="$repo_root/.runtime/upstream/kag"
kag_venv="$repo_root/.venv"

"$repo_root/scripts/sync-upstreams.sh"

uv python install 3.10.18
uv venv --clear --python 3.10.18 "$kag_venv"
uv pip install --python "$kag_venv/bin/python" --editable "$kag_source"

KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 "$kag_venv/bin/kag" --help >/dev/null
KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 "$kag_venv/bin/knext" --help >/dev/null

printf 'KAG %s (%s) installed in %s\n' \
  "$(<"$kag_source/KAG_VERSION")" \
  "$(git -C "$kag_source" rev-parse HEAD)" \
  "$kag_venv"

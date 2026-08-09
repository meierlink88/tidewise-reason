#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
kag_source="$repo_root/.runtime/KAG"
kag_venv="$repo_root/.venv"

mkdir -p "$repo_root/.runtime"

if [[ ! -d "$kag_source/.git" ]]; then
  git clone --branch v0.8.0 --depth 1 https://github.com/OpenSPG/KAG.git "$kag_source"
fi

uv python install 3.10
uv venv --python 3.10 "$kag_venv"
uv pip install --python "$kag_venv/bin/python" --editable "$kag_source"

"$kag_venv/bin/kag" --help >/dev/null
"$kag_venv/bin/knext" --help >/dev/null

printf 'KAG %s installed in %s\n' "$(<"$kag_source/KAG_VERSION")" "$kag_venv"

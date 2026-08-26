#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_python="${TIDEWISE_GRAPHITI_PYTHON:-$HOME/.local/share/tidewise-reason/graphiti-0.29.3/bin/python}"

if [[ ! -x "$runtime_python" ]]; then
  echo "Graphiti runtime is missing: $runtime_python" >&2
  exit 1
fi

cd "$repo_root"
PYTHONPATH="$repo_root" "$runtime_python" -m initialization.geopolitic.cli "$@"

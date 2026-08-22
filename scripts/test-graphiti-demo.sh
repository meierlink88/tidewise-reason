#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_base="${XDG_DATA_HOME:-$HOME/.local/share}"
runtime_root="${GRAPHITI_RUNTIME_ROOT:-$runtime_base/tidewise-reason/graphiti-0.29.3}"
python_bin="$runtime_root/bin/python"

[ -x "$python_bin" ] || { echo "Graphiti runtime is missing: $python_bin" >&2; exit 1; }

cd "$repo_root/graphiti_demo"
GRAPHITI_TELEMETRY_ENABLED=false exec "$python_bin" -m unittest test_runtime.py

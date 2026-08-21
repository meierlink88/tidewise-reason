#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_base="${XDG_DATA_HOME:-$HOME/.local/share}"
runtime_root="${GRAPHITI_RUNTIME_ROOT:-$runtime_base/tidewise-reason/graphiti-0.29.3}"
uv_bin="${UV_BIN:-$(command -v uv || true)}"

[ -x "$uv_bin" ] || { echo "uv is missing: $uv_bin" >&2; exit 1; }

"$uv_bin" venv --python 3.12.11 "$runtime_root"
"$uv_bin" pip install --python "$runtime_root/bin/python" \
  --require-hashes -r "$repo_root/graphiti_demo/requirements.lock"
"$runtime_root/bin/python" -c \
  "import importlib.metadata, sys; assert sys.version_info[:3] == (3, 12, 11); assert importlib.metadata.version('graphiti-core') == '0.29.3'"

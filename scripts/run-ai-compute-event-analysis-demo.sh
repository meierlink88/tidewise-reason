#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_python="${TIDEWISE_GRAPHITI_PYTHON:-$HOME/.local/share/tidewise-reason/graphiti-0.29.3/bin/python}"

cd "$repo_root"
PYTHONPATH="$repo_root" "$runtime_python" -m evaluation.ai_compute_event_analysis_demo "$@"

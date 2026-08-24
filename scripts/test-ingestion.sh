#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_python="${TIDEWISE_GRAPHITI_PYTHON:-$HOME/.local/share/tidewise-reason/graphiti-0.29.3/bin/python}"
pycache_root="$(mktemp -d)"
trap 'rm -rf "$pycache_root"' EXIT

cd "$repo_root"
PYTHONPATH="$repo_root" PYTHONPYCACHEPREFIX="$pycache_root" \
  "$runtime_python" -m unittest \
    tests.test_evidence_episode_converter \
    tests.test_evidence_episode_api \
    tests.test_evidence_episode_worker \
    tests.test_evidence_episode_worker_loop \
    tests.test_evidence_graphiti_writer \
    tests.test_graphiti_group_contract \
    tests.test_ingestion_runtime \
    tests.test_ingestion_compose_contract \
    tests.test_projection_runtime

#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_python="${TIDEWISE_GRAPHITI_PYTHON:-$HOME/.local/share/tidewise-reason/graphiti-0.29.3/bin/python}"
pycache_root="$(mktemp -d)"
trap 'rm -rf "$pycache_root"' EXIT

cd "$repo_root"
PYTHONPATH="$repo_root" PYTHONPYCACHEPREFIX="$pycache_root" \
  "$runtime_python" -m unittest \
    tests.test_authoritative_projection_writer \
    tests.test_country_region_projection \
    tests.test_industry_projection \
    tests.test_concept_projection \
    tests.test_industry_chain_projection

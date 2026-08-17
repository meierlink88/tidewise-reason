#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" pull server
docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" up -d --no-build server

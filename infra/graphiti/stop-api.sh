#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
env_file="${GRAPHITI_ENV_FILE:-$repo_root/.runtime/graphiti.env}"
compose_file="$repo_root/infra/graphiti/compose.yaml"

# shellcheck source=runtime-env.sh
source "$repo_root/infra/graphiti/runtime-env.sh"
require_private_graphiti_env "$env_file"

docker compose --env-file "$env_file" -f "$compose_file" stop api
docker compose --env-file "$env_file" -f "$compose_file" rm -f api

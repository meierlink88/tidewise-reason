#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_python="${TIDEWISE_GRAPHITI_PYTHON:-$HOME/.local/share/tidewise-reason/graphiti-0.29.3/bin/python}"
data_pg_container="${TIDEWISE_DATA_PG_CONTAINER:-tidewise-infra-postgres-1}"
export_sql="$repo_root/initialization/chainnode/export.sql"
snapshot_file="$(mktemp)"
trap 'rm -f "$snapshot_file"' EXIT

if [[ ! -x "$runtime_python" ]]; then
  echo "Graphiti runtime is missing: $runtime_python" >&2
  exit 1
fi
if [[ "$(docker inspect -f '{{.State.Running}}' "$data_pg_container" 2>/dev/null || true)" != "true" ]]; then
  echo "Tidewise Data PostgreSQL container is not running: $data_pg_container" >&2
  exit 1
fi

cd "$repo_root"
docker exec -i "$data_pg_container" sh -lc \
  'exec psql -X -qAt -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"' \
  < "$export_sql" > "$snapshot_file"
PYTHONPATH="$repo_root" "$runtime_python" -m initialization.chainnode.cli "$@" \
  < "$snapshot_file"

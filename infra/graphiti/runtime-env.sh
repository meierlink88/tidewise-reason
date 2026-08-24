#!/usr/bin/env bash

require_private_graphiti_env() {
  local env_file="$1"
  [ -f "$env_file" ] || {
    echo "missing runtime environment: $env_file" >&2
    return 1
  }

  local mode
  if mode="$(stat -f '%Lp' "$env_file" 2>/dev/null)"; then
    :
  else
    mode="$(stat -c '%a' "$env_file")"
  fi
  [ "$mode" = '600' ] || {
    echo "runtime environment must have mode 0600: $env_file" >&2
    return 1
  }
}

require_reason_api_token() {
  [ -n "${REASON_API_SERVICE_TOKEN:-}" ] || {
    echo 'REASON_API_SERVICE_TOKEN is required for the Reason ingestion API' >&2
    return 1
  }
}

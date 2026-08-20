#!/usr/bin/env bash

set -euo pipefail

prototype_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime_dir="/tmp/reason-smoke-prototype.$$"
mysql_container=tidewise-infra-mysql-1
server_container=reason-server

case "$runtime_dir" in
  /tmp/reason-smoke-prototype.*) ;;
  *) echo "Refusing unexpected runtime directory: $runtime_dir" >&2; exit 1 ;;
esac

cleanup() {
  docker exec "$server_container" sh -c 'case "$1" in /tmp/reason-smoke-prototype.*) rm -rf -- "$1" ;; *) exit 1 ;; esac' sh "$runtime_dir" >/dev/null 2>&1 || true
  unset llm_config vectorizer_config
}
trap cleanup EXIT

docker inspect "$server_container" --format '{{.State.Health.Status}}' | grep -Fx healthy >/dev/null
docker exec "$mysql_container" mysqladmin -uroot -popenspg ping --silent >/dev/null 2>&1

docker exec "$server_container" install -d -m 0700 "$runtime_dir"
docker cp "$prototype_root/demo.py" "$server_container:$runtime_dir/demo.py" >/dev/null
docker cp "$prototype_root/ReasonSmoke.schema" "$server_container:$runtime_dir/ReasonSmoke.schema" >/dev/null

llm_config="$(
  docker exec "$mysql_container" mysql -uroot -popenspg -D openspg -B -N \
    -e "SELECT config FROM kg_user_model WHERE name='DeepSeek V4 Flash' LIMIT 1" 2>/dev/null
)"
vectorizer_config="$(
  docker exec "$mysql_container" mysql -uroot -popenspg -D openspg -B -N \
    -e "SELECT config FROM kg_user_model WHERE name='阿里百炼 Embedding' LIMIT 1" 2>/dev/null
)"
[ -n "$llm_config" ] || { echo "DeepSeek V4 Flash is not configured in local OpenSPG" >&2; exit 1; }
[ -n "$vectorizer_config" ] || { echo "The local OpenSPG vectorizer is not configured" >&2; exit 1; }

printf '%s\n%s\n' "$llm_config" "$vectorizer_config" \
  | docker exec -i \
      -e KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 \
      -w "$runtime_dir" \
      "$server_container" \
      python "$runtime_dir/demo.py" --schema "$runtime_dir/ReasonSmoke.schema"

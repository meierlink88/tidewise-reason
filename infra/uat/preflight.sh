#!/usr/bin/env bash

set -euo pipefail

deployment_root="${DEPLOY_ROOT:?DEPLOY_ROOT is required}"
runtime_env="${RUNTIME_ENV:?RUNTIME_ENV is required}"
compose_file="${COMPOSE_FILE:?COMPOSE_FILE is required}"
expected_runner="${UAT_RUNNER_NAME:?UAT_RUNNER_NAME is required}"
content_source="${REASON_CONTENT_SOURCE:?REASON_CONTENT_SOURCE is required}"

pass() { echo "PASS $1"; }
fail() { echo "FAIL $1: $2" >&2; exit 1; }

if [ "$(uname -s)" != Linux ] || [ "$(uname -m)" != x86_64 ]; then
  fail platform "expected Linux x86_64"
fi
[ "$(id -un)" = tidewise-deploy ] \
  || fail deploy-user "expected tidewise-deploy"
[ "${RUNNER_NAME:-}" = "$expected_runner" ] \
  || fail runner-name "expected $expected_runner"
pass runtime-identity

for command in docker curl find python3 flock ss; do
  command -v "$command" >/dev/null || fail dependency "$command is missing"
done
docker info >/dev/null || fail docker-engine "docker info failed"
docker compose version >/dev/null || fail docker-compose "Docker Compose v2 is unavailable"
docker network inspect tidewise-uat >/dev/null \
  || fail docker-network "tidewise-uat is missing"
pass docker-runtime-and-network

for directory in "$deployment_root" "$deployment_root/state" /opt/tidewise/uat; do
  [ -d "$directory" ] || fail deployment-directory "$directory is missing"
done
[ -w "$deployment_root/state" ] \
  || fail deployment-directory "$deployment_root/state is not writable"
[ -w /opt/tidewise/uat ] || fail shared-lock "/opt/tidewise/uat is not writable"
available_kb="$(df -Pk "$deployment_root" | awk 'NR == 2 {print $4}')"
[ "$available_kb" -ge 5242880 ] \
  || fail disk-space "at least 5 GiB is required"
pass deployment-storage

[ -d "$content_source" ] || fail reason-content "$content_source is missing"
[ -f "$content_source/Tidewise.schema" ] \
  || fail reason-content "Tidewise.schema is missing"
if [ -n "$(find "$content_source" -type l -print -quit)" ]; then
  fail reason-content "symbolic links are not allowed"
fi
pass versioned-reason-content

[ -r "$runtime_env" ] || fail runtime-env "$runtime_env is not readable"
set -a
# shellcheck disable=SC1090
. "$runtime_env"
set +a

official_repository="spg-registry.cn-hangzhou.cr.aliyuncs.com/spg/openspg-server"
case "${OPENSPG_SERVER_IMAGE:-}" in
  "$official_repository":latest|"$official_repository"@sha256:*) ;;
  *) fail server-image "must be the official OpenSPG Server latest tag or its resolved digest" ;;
esac
[[ "${OPENSPG_MYSQL_ROOT_PASSWORD:-}" =~ ^[A-Za-z0-9_-]{24,64}$ ]] \
  || fail mysql-password "must be 24-64 URL-safe characters"
[[ "${OPENSPG_JASYPT_PASSWORD:-}" =~ ^[A-Za-z0-9_-]{24,64}$ ]] \
  || fail jasypt-password "must be 24-64 URL-safe characters"
[[ "${OPENSPG_MINIO_ACCESS_KEY:-}" =~ ^[A-Za-z0-9_-]{3,128}$ ]] \
  || fail minio-access-key "must be 3-128 URL-safe characters"
[[ "${OPENSPG_MINIO_SECRET_KEY:-}" =~ ^[A-Za-z0-9_-]{8,128}$ ]] \
  || fail minio-secret-key "must be 8-128 URL-safe characters"
[[ "${OPENSPG_NEO4J_USER:-}" =~ ^[A-Za-z0-9_-]{1,64}$ ]] \
  || fail neo4j-user "must be 1-64 URL-safe characters"
[[ "${OPENSPG_NEO4J_PASSWORD:-}" =~ ^[A-Za-z0-9_-]{24,64}$ ]] \
  || fail neo4j-password "must be 24-64 URL-safe characters"
[[ "${OPENSPG_WEB_PORT:-8887}" =~ ^[0-9]+$ ]] \
  || fail web-port "must be numeric"
pass protected-runtime-inputs

services="$(docker compose --env-file "$runtime_env" -f "$compose_file" config --services)"
[ "$services" = server ] || fail compose-services "expected only the server service"
configured_image="$(docker compose --env-file "$runtime_env" -f "$compose_file" config --images)"
[ "$configured_image" = "$OPENSPG_SERVER_IMAGE" ] \
  || fail compose-image "resolved image differs from protected runtime"
pass compose-contract

web_port="${OPENSPG_WEB_PORT:-8887}"
published_containers="$(docker ps --filter "publish=$web_port" --format '{{.ID}}')"
while read -r container_id; do
  [ -z "$container_id" ] && continue
  project="$(docker inspect --format '{{ index .Config.Labels "com.docker.compose.project" }}' "$container_id")"
  service="$(docker inspect --format '{{ index .Config.Labels "com.docker.compose.service" }}' "$container_id")"
  if [ "$project" != tidewise-reason-uat ] || [ "$service" != server ]; then
    fail "port-$web_port" "published by a container outside tidewise-reason-uat/server"
  fi
done <<<"$published_containers"
if [ -z "$published_containers" ] && [ -n "$(ss -H -ltn "sport = :$web_port")" ]; then
  fail "port-$web_port" "occupied by a non-Docker listener"
fi
pass office-allowlisted-web-port

docker run --rm -i \
  --network tidewise-uat \
  --add-host release-openspg-neo4j:host-gateway \
  --env-file "$runtime_env" \
  --entrypoint python \
  "$OPENSPG_SERVER_IMAGE" - <<'PY'
import os
import socket
import datetime
import hashlib
import hmac
import http.client

from neo4j import GraphDatabase


def require_tcp(host: str, port: int) -> None:
    with socket.create_connection((host, port), timeout=5):
        pass


require_tcp("mysql", 3306)
require_tcp("minio", 9000)

host = "minio:9000"
access_key = os.environ["OPENSPG_MINIO_ACCESS_KEY"]
secret_key = os.environ["OPENSPG_MINIO_SECRET_KEY"]
now = datetime.datetime.now(datetime.timezone.utc)
amz_date = now.strftime("%Y%m%dT%H%M%SZ")
date_stamp = now.strftime("%Y%m%d")
payload_hash = hashlib.sha256(b"").hexdigest()
canonical_headers = (
    f"host:{host}\n"
    f"x-amz-content-sha256:{payload_hash}\n"
    f"x-amz-date:{amz_date}\n"
)
signed_headers = "host;x-amz-content-sha256;x-amz-date"
canonical_request = (
    "GET\n/\n\n"
    f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
)
credential_scope = f"{date_stamp}/us-east-1/s3/aws4_request"
string_to_sign = (
    "AWS4-HMAC-SHA256\n"
    f"{amz_date}\n{credential_scope}\n"
    f"{hashlib.sha256(canonical_request.encode()).hexdigest()}"
)


def sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode(), hashlib.sha256).digest()


date_key = sign(("AWS4" + secret_key).encode(), date_stamp)
region_key = sign(date_key, "us-east-1")
service_key = sign(region_key, "s3")
signing_key = sign(service_key, "aws4_request")
signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
authorization = (
    f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, "
    f"SignedHeaders={signed_headers}, Signature={signature}"
)
connection = http.client.HTTPConnection("minio", 9000, timeout=5)
connection.request(
    "GET",
    "/",
    headers={
        "Authorization": authorization,
        "Host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    },
)
response = connection.getresponse()
response.read()
if response.status != 200:
    raise RuntimeError(f"authenticated MinIO list-buckets failed: HTTP {response.status}")

uri = "neo4j://release-openspg-neo4j:7687"
auth = (os.environ["OPENSPG_NEO4J_USER"], os.environ["OPENSPG_NEO4J_PASSWORD"])
with GraphDatabase.driver(uri, auth=auth) as driver:
    driver.verify_connectivity()
    with driver.session(database="neo4j") as session:
        version = session.run("RETURN gds.version() AS version").single()["version"]
        if version != "2.13.4":
            raise RuntimeError(f"expected GDS 2.13.4, got {version}")
        session.run("RETURN 1 AS ok").single(strict=True)
print(f"dependencies reachable; GDS {version}")
PY
pass external-mysql-minio-neo4j-gds

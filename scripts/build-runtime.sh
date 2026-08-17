#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$repo_root/upstreams.lock"
openspg_source="$repo_root/.runtime/upstream/openspg"
kag_source="$repo_root/.runtime/upstream/kag"
build_root="$repo_root/.runtime/build"
maven_repository="$repo_root/.runtime/maven-repository"
image_name="${TIDEWISE_REASON_IMAGE:-tidewise-reason:openspg-0.8-kag-0.8.0}"

hash_file() {
  if command -v sha256sum >/dev/null; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

for executable in git mvn uv docker; do
  command -v "$executable" >/dev/null || {
    printf 'Required executable is missing: %s\n' "$executable" >&2
    exit 1
  }
done

"$repo_root/scripts/sync-upstreams.sh"

mkdir -p "$build_root/openspg" "$build_root/kag"
mvn -B \
  --settings "$repo_root/config/maven-settings.xml" \
  -Dmaven.repo.local="$maven_repository" \
  -DskipTests \
  package \
  -f "$openspg_source/pom.xml"
openspg_jar="$openspg_source/dev/release/server/target/arks-sofaboot-0.0.1-SNAPSHOT-executable.jar"
test -f "$openspg_jar"
install -m 0644 "$openspg_jar" "$build_root/openspg/arks-sofaboot-0.8-executable.jar"

find "$build_root/kag" -maxdepth 1 -type f -name '*.whl' -delete
uv build --wheel --out-dir "$build_root/kag" "$kag_source"
test "$(find "$build_root/kag" -maxdepth 1 -type f -name '*.whl' | wc -l | tr -d ' ')" = 1
kag_wheel="$(find "$build_root/kag" -maxdepth 1 -type f -name '*.whl')"
openspg_jar_sha256="$(hash_file "$build_root/openspg/arks-sofaboot-0.8-executable.jar")"
kag_wheel_sha256="$(hash_file "$kag_wheel")"

docker build \
  --build-arg "OPENSPG_COMMIT=$OPENSPG_COMMIT" \
  --build-arg "KAG_COMMIT=$KAG_COMMIT" \
  --build-arg "OPENSPG_VERSION=$OPENSPG_VERSION" \
  --build-arg "KAG_VERSION=$KAG_VERSION" \
  --build-arg "OPENSPG_JAR_SHA256=$openspg_jar_sha256" \
  --build-arg "KAG_WHEEL_SHA256=$kag_wheel_sha256" \
  --tag "$image_name" \
  "$repo_root"

printf 'Built %s from OpenSPG %s and KAG %s\n' "$image_name" "$OPENSPG_COMMIT" "$KAG_COMMIT"
